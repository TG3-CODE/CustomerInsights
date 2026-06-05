# rag.py — RAG pipeline: filing ingestion, vectorstore, and QA chain.

import os
import streamlit as st
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate

PROMPT_TEMPLATE = """You are a financial analyst reviewing SEC 10-K filings.
Answer the question using ONLY the context provided.
Always cite the specific company, filing section, and page number.
If the answer is not in the context, say exactly:
"I cannot find this information in the provided filings."
Do NOT make up numbers or figures. Do NOT use external knowledge.

Context:
{context}

Question: {question}

Answer (with citations):"""


@st.cache_data(show_spinner=False)
def load_filing_text(filepath: str) -> str:
    """Parse an HTM filing into plain text, stripping scripts and styles."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        lines = [l.strip() for l in soup.get_text(separator="\n").splitlines() if l.strip()]
        return "\n".join(lines)
    except Exception as e:
        return f"Error loading file: {e}"


@st.cache_resource(show_spinner=False)
def build_vectorstore(api_key: str, companies: dict):
    """Chunk all filings and build a ChromaDB vector store."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)

    all_docs = []
    for company, info in companies.items():
        if os.path.exists(info["file"]):
            text = load_filing_text(info["file"])
            chunks = splitter.create_documents(
                [text],
                metadatas=[{"company": company, "ticker": info["ticker"], "source": info["file"]}],
            )
            all_docs.extend(chunks)

    return Chroma.from_documents(all_docs, embeddings, persist_directory="./chroma_db") if all_docs else None


def get_qa_chain(vectorstore, api_key: str, company_filter: str = None):
    """Return a callable QA chain that retrieves from the vectorstore and answers with citations."""
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

    search_kwargs = {"k": 5}
    if company_filter and company_filter != "All Companies":
        search_kwargs["filter"] = {"company": company_filter}
    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)

    prompt = PromptTemplate(input_variables=["context", "question"], template=PROMPT_TEMPLATE)

    class _Chain:
        def __call__(self, inputs: dict) -> dict:
            question = inputs["query"]
            docs = retriever.invoke(question)
            context = "\n\n".join(doc.page_content for doc in docs)
            response = llm.invoke(prompt.format(context=context, question=question))
            return {"result": response.content, "source_documents": docs}

    return _Chain()
