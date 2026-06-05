# WRITEUP — CustomerInsights.AI Financial Dashboard

## Architecture & Files

Five files, each with one job:

- **`parser.py`** — Extracts financial figures directly from the HTM filings. Dynamically detects section boundaries (income statement, balance sheet, cash flows) by searching for statement headers validated by nearby financial content — no hardcoded line numbers. Every extracted value is tagged with its source label and line index for full traceability.
- **`analytics.py`** — Pure functions: gross/operating/net margins, YoY growth, 2-year CAGR, FCF, debt-to-assets. No Streamlit, no file I/O — independently testable.
- **`rag.py`** — RAG pipeline: BeautifulSoup HTML parser, `RecursiveCharacterTextSplitter` (1500 tokens / 200 overlap), ChromaDB vectorstore, `gpt-4o-mini` QA chain. API key passed directly to clients — never written to `os.environ`.
- **`data.py`** — Static config only: company metadata (file paths, tickers, colors) and the labeled evaluation question set. No financial figures, no narrative quotes.
- **`app.py`** — Streamlit UI. Loads financial data from `parser.py` on startup (cached), wires analytics and RAG into four tabs: Overview, Deep Dive, RAG Q&A, Evaluation.

**Derived metrics computed in-app** (inputs and formulas traceable to source):
- Gross / operating / net margins = income ÷ revenue × 100
- YoY growth = (current − prior) / prior × 100
- 2-year CAGR = (FY2025 / FY2023)^(1/2) − 1
- FCF = Operating Cash Flow − Capital Expenditures
- Debt-to-Assets = Total term debt ÷ Total assets × 100

**Quant-to-narrative linkage is fully RAG-generated.** The app detects the top 3 metric movers (by absolute YoY % change) for the selected company, constructs targeted questions ("Why did Microsoft's Capital Expenditures increase in FY2025?"), and retrieves management commentary from the actual filing chunks. No pre-written quotes.

---

## Hallucination Rate & Executive Readiness

**Hallucination rate: 0/3** on the labeled unanswerable set — all refused correctly.

**Would I trust it in front of an executive? Not yet.** Two specific concerns:

1. FY2023 balance sheet figures (total assets, total debt) are unavailable from the FY2025 10-K filings — these only cover two balance sheet years. The app marks them as None and notes this explicitly.
2. Google's FY2025 net income ($132.2B) is inflated by $29.8B of non-operating investment gains. A side-by-side comparison with Apple/Microsoft on net income misleads without that context — the RAG narrative surfaces this when queried.

**Fix first:** XBRL parsing for guaranteed schema-validated figures, replacing the HTML text parser.

---

## Most Interesting Insight

Google's FCF ($69.5B → $73.3B) barely moved over 3 years while capex nearly tripled ($32.3B → $91.4B), because operating cash flow grew from $101.7B to $164.7B. Both Microsoft and Google are self-funding massive AI infrastructure bets from operations — but Google is spending proportionally more aggressively relative to its size.

Confidence: **High.** All three figures (OCF, capex) read directly from Cash Flow Statements in the filings, formula explicit in the dashboard.

---

## One Failure Found & Diagnosed

The original `FINANCIAL_DATA` (before the parser was written) had Apple FY2025 revenue at **$394.33B**. The actual 10-K figure is **$416.161B** — a $21.8B overstatement (5.5%).

Root cause: estimated data used instead of reading the filing directly. Diagnosed by searching the HTM file for "Total net sales" and reading adjacent numeric rows. The parser now extracts this directly from line 1762 of AppleEDGAR.htm, cited as `AppleEDGAR.htm — 'Total net sales' (line 1762)`.

Secondary error: Apple FY2024 and FY2025 net income were listed as identical ($93.74B). Actual: FY2024 = $93.736B, FY2025 = $112.010B. Same root cause, same fix.

---

## How AI Tools Were Used

Claude was used throughout: the Streamlit scaffolding, LangChain RAG pipeline, HTML parser, analytics functions, and chart layout. All code was reviewed line-by-line and corrected where needed.

**One specific override:** Claude's initial `get_qa_chain` used `RetrievalQA.from_chain_type` from `langchain.chains` — removed in LangChain 1.x. Replaced with a direct `retriever.invoke()` + `llm.invoke()` pattern that preserves the same interface without the removed wrapper.

**Second override:** Claude initially hardcoded both FINANCIAL_DATA (numbers) and NARRATIVE (MD&A quotes). Both were identified as defeating the purpose of the assessment and replaced — numbers with a live HTML parser, narrative with dynamic RAG queries against the actual filings.

---

## Where the Framework Helped vs. Where I Fought It

**Helped:** LangChain's `RecursiveCharacterTextSplitter` and `Chroma.from_documents` made chunking and indexing three large HTM files with per-company metadata straightforward. The retriever's `filter` kwarg (`{"company": "Apple"}`) scopes Q&A to a single filing without re-indexing.

**Fought it:** LangChain 1.x removed `langchain.chains`, `langchain.prompts`, and `langchain.text_splitter` — all three imports in the original scaffold broke on install. Dropped to direct `langchain_core` and `langchain_text_splitters` imports and replaced the high-level chain with two direct invoke calls. Cleaner and more debuggable than the removed wrapper.
