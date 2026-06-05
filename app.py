# app.py — Streamlit UI. All data, analytics, and RAG logic live in separate modules.

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from data import COMPANIES, EVAL_QUESTIONS
from analytics import compute_margins, compute_yoy_growth, compute_fcf, compute_cagr, compute_debt_to_equity
from rag import build_vectorstore, get_qa_chain
from parser import extract

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="CustomerInsights.AI", page_icon="📊", layout="wide")

# ── Load financial data live from filings (cached after first run) ─────────────
@st.cache_data(show_spinner="Parsing filings…")
def load_financial_data():
    return {company: extract(company) for company in COMPANIES}

FINANCIAL_DATA = load_financial_data()

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
    .stApp { background: #0d1117; color: #e6edf3; }
    .metric-card  { background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; margin:4px 0; }
    .company-tag  { display:inline-block; padding:2px 10px; border-radius:12px; font-size:12px; font-weight:600; font-family:'IBM Plex Mono',monospace; }
    .source-cite  { background:#161b22; border-left:3px solid #388bfd; padding:8px 12px; border-radius:0 4px 4px 0; font-size:13px; margin-top:8px; font-family:'IBM Plex Mono',monospace; }
    .narrative-card  { background:#161b22; border:1px solid #388bfd; border-radius:8px; padding:16px; margin:8px 0; }
    .narrative-quote { border-left:3px solid #f78166; padding:6px 12px; font-style:italic; color:#cdd9e5; font-size:13px; margin:8px 0; }
    h1, h2, h3 { font-family:'IBM Plex Mono',monospace; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    api_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("---")
    st.markdown("### 📁 Data Sources")
    import os
    for company, info in COMPANIES.items():
        exists = os.path.exists(info["file"])
        st.markdown(f"{'✅' if exists else '❌'} **{company}** ({info['ticker']})")
        if exists:
            st.caption(f"10-K · {FINANCIAL_DATA[company]['fiscal_year_end']}")
    st.markdown("---")
    st.caption("Source: SEC EDGAR · Public filings only")
    st.caption("All figures in USD billions unless stated.")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 📊 Financial Analysis Dashboard")
st.markdown("**Apple · Microsoft · Google** — Comparative 10-K Analysis (FY2023–FY2025)")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "💰 Deep Dive", "🤖 RAG Q&A", "🔬 Evaluation"])

# ── Shared chart defaults ──────────────────────────────────────────────────────
DARK = dict(plot_bgcolor="#0d1117", paper_bgcolor="#0d1117", font_color="#e6edf3")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Overview
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    # Revenue bar chart
    st.markdown("### Revenue (USD Billions)")
    fig = go.Figure()
    for company, info in COMPANIES.items():
        d = FINANCIAL_DATA[company]
        fig.add_trace(go.Bar(
            name=company, x=d["years"], y=d["revenue"],
            marker_color=info["color"],
            text=[f"${v:.1f}B" for v in d["revenue"]], textposition="outside",
        ))
    fig.update_layout(**DARK, barmode="group", height=380, legend=dict(bgcolor="#161b22"))
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Source: Consolidated Statements of Operations/Income — each company's 10-K filing")

    # Net margin line chart
    st.markdown("### Net Income Margin (%)")
    fig2 = go.Figure()
    for company, info in COMPANIES.items():
        d = FINANCIAL_DATA[company]
        m = compute_margins(d)
        fig2.add_trace(go.Scatter(
            name=company, x=d["years"], y=m["net_margin"],
            mode="lines+markers+text", line=dict(color=info["color"], width=2),
            text=[f"{v}%" for v in m["net_margin"]], textposition="top center",
        ))
    fig2.update_layout(**DARK, height=320, yaxis_title="Net Margin (%)")
    st.plotly_chart(fig2, use_container_width=True)

    # FCF bar chart
    st.markdown("### Free Cash Flow (USD Billions)  —  Operating CF − Capex")
    fig3 = go.Figure()
    for company, info in COMPANIES.items():
        d = FINANCIAL_DATA[company]
        fcf = compute_fcf(d)
        fig3.add_trace(go.Bar(
            name=company, x=d["years"], y=fcf,
            marker_color=info["color"],
            text=[f"${v:.1f}B" for v in fcf], textposition="outside",
        ))
    fig3.update_layout(**DARK, barmode="group", height=360)
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("FCF = Operating Cash Flow − Capital Expenditures. Source: Cash Flow Statements.")

    # Snapshot cards
    st.markdown("### FY2025 Snapshot")
    cols = st.columns(3)
    for i, (company, info) in enumerate(COMPANIES.items()):
        d = FINANCIAL_DATA[company]
        m = compute_margins(d)
        fcf = compute_fcf(d)
        yoy = compute_yoy_growth(d["revenue"])
        cagr = compute_cagr(d["revenue"])
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <span class="company-tag" style="background:{info['color']}22;color:{info['color']}">{info['ticker']}</span>
                <h3 style="margin:8px 0">{company}</h3>
                <p><b>Revenue:</b> ${d['revenue'][-1]:.2f}B</p>
                <p><b>Net Income:</b> ${d['net_income'][-1]:.2f}B</p>
                <p><b>Net Margin:</b> {m['net_margin'][-1]}%</p>
                <p><b>FCF:</b> ${fcf[-1]:.1f}B</p>
                <p><b>Rev YoY:</b> {yoy[-1]}% &nbsp;|&nbsp; <b>2yr CAGR:</b> {cagr}%</p>
                <p style="font-size:11px;color:#8b949e">FY end: {d['fiscal_year_end']}</p>
            </div>
            """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Deep Dive
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    selected = st.selectbox("Select Company", list(COMPANIES.keys()))
    d     = FINANCIAL_DATA[selected]
    color = COMPANIES[selected]["color"]
    m     = compute_margins(d)
    fcf   = compute_fcf(d)
    yoy   = compute_yoy_growth(d["revenue"])
    dte   = compute_debt_to_equity(d)

    # CAGR summary
    st.markdown("#### 2-Year CAGR  (FY2023 → FY2025)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue",    f"{compute_cagr(d['revenue'])}%")
    c2.metric("Net Income", f"{compute_cagr(d['net_income'])}%")
    c3.metric("FCF",        f"{compute_cagr(fcf)}%")
    c4.metric("Op. CF",     f"{compute_cagr(d['operating_cf'])}%")
    st.caption(f"Formula: (FY2025 / FY2023)^(1/2) − 1  |  {d['source_income']} · {d['source_cashflow']}")
    st.markdown("---")

    # Margin trends
    st.markdown(f"### {selected} — Margin Trends (%)")
    fig_m = go.Figure()
    for label, vals in [("Gross", m["gross_margin"]), ("Operating", m["operating_margin"]), ("Net", m["net_margin"])]:
        fig_m.add_trace(go.Scatter(
            name=f"{label} Margin", x=d["years"], y=vals,
            mode="lines+markers+text", line=dict(width=2),
            text=[f"{v}%" for v in vals], textposition="top center",
        ))
    fig_m.update_layout(**DARK, height=320, yaxis_title="Margin (%)")
    st.plotly_chart(fig_m, use_container_width=True)
    st.caption(f"Source: {d['source_income']}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Revenue YoY Growth (%)")
        yoy_vals  = [v for v in yoy if v is not None]
        yoy_years = d["years"][1:]
        fig_y = go.Figure(go.Bar(
            x=yoy_years, y=yoy_vals, marker_color=color,
            text=[f"{v}%" for v in yoy_vals], textposition="outside",
        ))
        fig_y.update_layout(**DARK, height=280)
        st.plotly_chart(fig_y, use_container_width=True)

    with col2:
        st.markdown("#### Debt-to-Equity (×)  —  Total Debt ÷ Equity")
        dte_years = [y for y, v in zip(d["years"], dte) if v is not None]
        dte_vals  = [v for v in dte if v is not None]
        fig_d = go.Figure(go.Bar(
            x=dte_years, y=dte_vals, marker_color=color,
            text=[f"{v}×" for v in dte_vals], textposition="outside",
        ))
        fig_d.update_layout(**DARK, height=280)
        st.plotly_chart(fig_d, use_container_width=True)
        if len(dte_vals) < 3:
            st.caption("⚠ FY2023 balance sheet not in FY2025 10-K — only FY2024 & FY2025 shown.")

    st.caption(f"Debt-to-Assets = Total term debt ÷ Total assets  |  {d['source_balance']}")

    # FCF waterfall
    st.markdown("#### FCF Breakdown: Operating CF vs Capex (USD Billions)")
    fig_f = go.Figure()
    fig_f.add_trace(go.Bar(name="Operating CF", x=d["years"], y=d["operating_cf"],  marker_color=color, opacity=0.75))
    fig_f.add_trace(go.Bar(name="Capex (−)",    x=d["years"], y=[-c for c in d["capex"]], marker_color="#f78166", opacity=0.85))
    fig_f.add_trace(go.Scatter(name="FCF", x=d["years"], y=fcf,
                               mode="lines+markers+text", line=dict(color="#f0e040", width=2),
                               text=[f"${v:.1f}B" for v in fcf], textposition="top center"))
    fig_f.update_layout(**DARK, barmode="relative", height=340, yaxis_title="USD Billions")
    st.plotly_chart(fig_f, use_container_width=True)
    st.caption(f"Source: {d['source_cashflow']}")

    # ── Conflicts & comparability warnings ────────────────────────────────────
    st.markdown("---")
    st.markdown("### ⚠️ Data Conflicts & Comparability Warnings")
    for c in d.get("conflicts", []):
        icon = "🔴" if c["severity"] == "conflict" else "🟡"
        with st.expander(f"{icon} {c['title']}"):
            st.markdown(c["detail"])

    # ── Quant → Narrative (RAG-generated) ────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📝 Quant → Narrative Linkage")

    if not api_key:
        st.info("Enter your OpenAI API key in the sidebar to generate RAG-powered narrative.")
    else:
        # Detect top 3 metric movers (largest absolute YoY % change, FY2024→FY2025)
        metric_map = {
            "Revenue":           d["revenue"],
            "Net Income":        d["net_income"],
            "Operating Income":  d["operating_income"],
            "Capital Expenditures": d["capex"],
            "Free Cash Flow":    fcf,
        }
        movers = []
        for name, values in metric_map.items():
            yoy = compute_yoy_growth(values)
            if yoy[-1] is not None:
                movers.append((abs(yoy[-1]), name, yoy[-1]))
        movers.sort(reverse=True)

        with st.spinner("Retrieving management commentary from filings…"):
            try:
                vs = build_vectorstore(api_key, COMPANIES)
                if vs:
                    qa = get_qa_chain(vs, api_key, company_filter=selected)
                    for _, metric_name, change in movers[:3]:
                        direction = "increase" if change > 0 else "decrease"
                        question  = (
                            f"Why did {selected}'s {metric_name} {direction} in fiscal year 2025? "
                            f"What does management say in the MD&A or risk factors?"
                        )
                        result = qa({"query": question})
                        sources = {doc.metadata.get("source","") for doc in result["source_documents"]}
                        st.markdown(f"""
                        <div class="narrative-card">
                            <b>📊 {selected} — {metric_name}: {'+' if change>0 else ''}{change}% YoY</b>
                            <p style="margin:8px 0;font-size:14px">{result['result']}</p>
                            {''.join(f'<div class="source-cite">📄 {s}</div>' for s in sources)}
                        </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Narrative generation failed: {e}")

    # Optional RAG follow-up
    if api_key:
        st.markdown("#### Ask a follow-up about this company's filings")
        follow_up = st.text_input("Question", placeholder=f"Why did {selected}'s capex grow so much?", key="followup")
        if st.button("Ask RAG", key="followup_btn") and follow_up:
            with st.spinner("Searching filings..."):
                try:
                    vs = build_vectorstore(api_key, COMPANIES)
                    if vs:
                        qa = get_qa_chain(vs, api_key, company_filter=selected)
                        result = qa({"query": follow_up})
                        st.write(result["result"])
                        seen = set()
                        for doc in result["source_documents"]:
                            key = f"{doc.metadata.get('company')}:{doc.metadata.get('source')}"
                            if key not in seen:
                                seen.add(key)
                                st.markdown(f"<div class='source-cite'>📄 {doc.metadata.get('company')} — {doc.metadata.get('source')}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — RAG Q&A
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Ask the Filings")
    st.info("Answers are grounded in the actual 10-K filings. Unanswerable questions are refused.")

    if not api_key:
        st.warning("Enter your OpenAI API key in the sidebar to enable Q&A.")
    else:
        company_filter = st.selectbox("Filter by company", ["All Companies"] + list(COMPANIES.keys()))
        question = st.text_input("Ask a question", placeholder="What are Apple's main risk factors?")

        if st.button("Ask") and question:
            with st.spinner("Searching filings..."):
                try:
                    vs = build_vectorstore(api_key, COMPANIES)
                    if vs is None:
                        st.error("Could not load filings. Check that HTM files are in fillings/.")
                    else:
                        qa = get_qa_chain(vs, api_key, company_filter)
                        result = qa({"query": question})
                        st.markdown("#### Answer")
                        st.write(result["result"])
                        st.markdown("#### Sources")
                        seen = set()
                        for doc in result["source_documents"]:
                            company = doc.metadata.get("company", "Unknown")
                            source  = doc.metadata.get("source",  "Unknown")
                            key = f"{company}:{source}"
                            if key not in seen:
                                seen.add(key)
                                st.markdown(f"<div class='source-cite'>📄 {company} — {source}</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("#### Sample Questions")
        for q in [
            "What are Apple's main risk factors related to tariffs?",
            "How does Microsoft describe its AI infrastructure investment strategy?",
            "What drove the increase in Google's general and administrative expenses in 2025?",
            "What is Apple's approach to share buybacks?",
            "What caused changes in Microsoft's cloud gross margin?",
        ]:
            st.markdown(f"- {q}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — Evaluation
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("### Evaluation Framework")
    st.markdown(
        "Labeled question set assessing RAG answer quality, citation accuracy, and hallucination rate. "
        "Results obtained by running the Q&A chain with `gpt-4o-mini` against the actual filings."
    )

    df = pd.DataFrame(EVAL_QUESTIONS)
    st.dataframe(df[["question", "expected", "type", "result", "notes"]]
                 .rename(columns={"question": "Question", "expected": "Expected",
                                  "type": "Type", "result": "Result", "notes": "Notes"}),
                 use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Factual Accuracy",   "5/5",  "100% on answerable questions")
    c2.metric("Hallucination Rate", "0/3",  "Refused all unanswerable questions")
    c3.metric("Citation Accuracy",  "High", "All answers cite filing + page")

    st.markdown("---")
    st.markdown("### Honest Assessment")
    st.markdown("""
**Would I trust this in front of an executive? Not yet.**

- FY2023 balance sheet figures rely on prior 10-Ks not in this dataset — accurate but not verifiable from these specific HTM files.
- RAG retrieval handles narrative text well but can miss values in tightly packed HTML tables.
- Google's FY2025 net income ($132.2B) is significantly inflated by $29.8B of non-operating investment gains — a naive comparison with Apple/Microsoft would mislead. The dashboard surfaces this in the Quant→Narrative section.

**Fix first:** XBRL parsing for all numerical figures, eliminating manual extraction and unit mix-up risk.

**Most interesting insight:**
Google's FCF ($69.5B → $73.3B) barely moved over 3 years while capex tripled ($32.3B → $91.4B), because operating cash flow grew even faster ($101.7B → $164.7B). Both Microsoft and Google are self-funding massive AI infrastructure bets from operations — but Google is spending proportionally more aggressively.

**One failure found and diagnosed:**
Original data had Apple FY2025 revenue at $394.33B. Actual 10-K figure: $416.161B — a $21.8B overstatement (5.5%). Root cause: estimated data used instead of reading the filing directly. Fixed by reading `Total net sales` from AppleEDGAR.htm line-by-line.
    """)
