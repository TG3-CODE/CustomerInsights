# CustomerInsights.AI — Financial Dashboard

Streamlit RAG dashboard for comparative 10-K analysis of Apple, Microsoft, and Google (FY2023–FY2025).

## Setup

```bash
pip install streamlit langchain-openai langchain-community langchain-text-splitters \
            langchain-core chromadb beautifulsoup4 plotly pandas
```

## Run

```bash
streamlit run app.py
```

Enter your OpenAI API key in the sidebar to enable RAG Q&A and narrative generation.

## Document Sources

All filings are public SEC EDGAR documents, stored in `/fillings/`:

| File | Company | Filing | Period |
|------|---------|--------|--------|
| AppleEDGAR.htm | Apple Inc. | 10-K | FY2025 (Sep 27, 2025) |
| MsftEDGAR.htm | Microsoft Corp. | 10-K | FY2025 (Jun 30, 2025) |
| GoogleEDGAR.htm | Alphabet Inc. | 10-K | FY2025 (Dec 31, 2025) |

Source: https://www.sec.gov/cgi-bin/browse-edgar

## File Structure

| File | Responsibility |
|------|---------------|
| `app.py` | Streamlit UI — tabs, charts, layout only |
| `parser.py` | Extracts financial figures from HTM filings with line-level citations |
| `analytics.py` | Pure math — margins, CAGR, FCF, YoY growth |
| `rag.py` | RAG pipeline — filing ingestion, ChromaDB vectorstore, QA chain |
| `data.py` | Static config — company metadata and evaluation questions |

## Design Choices

**Why parse from HTM instead of hardcoding?**
The assessment explicitly required pulling figures from the filings. `parser.py` dynamically detects financial statement section boundaries by searching for statement headers (e.g. "CONSOLIDATED BALANCE SHEETS" validated by nearby "total assets"), then extracts values using regex with parenthesis-negation handling. Every figure is tagged with its source label and line number.

**Why RAG for narrative, not hardcoded quotes?**
The quant-to-narrative linkage is fully dynamic. The app computes the top 3 metric movers (by absolute YoY % change) for the selected company, then queries the RAG with targeted questions like "Why did Apple's Net Income increase in FY2025?" The LLM answers using only retrieved filing chunks — no pre-written quotes.

**Why ChromaDB?**
Lightweight, no infrastructure, persists locally. Adequate for three documents (~800 chunks).

**Why gpt-4o-mini?**
Cost-effective for retrieval-augmented Q&A. Temperature 0 for deterministic answers.

**Refusal behavior:**
The system prompt instructs the model to say "I cannot find this information in the provided filings." for unanswerable questions — tested in the Evaluation tab.

## Evaluation Results

| Metric | Score |
|--------|-------|
| Factual accuracy (answerable Qs) | 5/5 (100%) |
| Hallucination rate (unanswerable Qs) | 0/3 (0%) |
| Citation accuracy | High — all answers cite filing + line |

See the Evaluation tab for the full question set and per-question notes.
