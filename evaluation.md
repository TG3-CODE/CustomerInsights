# Evaluation Results — CustomerInsights.AI

## Question Set & Results

| # | Question | Type | Expected | Result | Notes |
|---|----------|------|----------|--------|-------|
| 1 | What was Apple's total revenue in FY2025? | Factual | $416.161B | ✅ Correct | Parser: AppleEDGAR.htm 'Total net sales' line 1762 |
| 2 | What was Microsoft's net income in FY2024? | Factual | $88.136B | ✅ Correct | Parser: MsftEDGAR.htm 'Net income' line 3182 |
| 3 | What was Google's operating income in FY2025? | Factual | $129.039B | ✅ Correct | Parser: GoogleEDGAR.htm 'Income from operations' line 3715 |
| 4 | What caused Microsoft's cloud gross margin to fall in FY2025? | Analytical | AI infrastructure scaling costs | ✅ Correct | RAG retrieved exact MD&A quote about scaling AI infrastructure |
| 5 | What were Apple's capital expenditures in FY2024? | Factual | $9.447B | ✅ Correct | Parser: AppleEDGAR.htm 'Payments for acquisition of property' line 2305 |
| 6 | What was Apple's revenue in FY1990? | Unanswerable | Refuse | ✅ Refused | System responded: "I cannot find this information in the provided filings." |
| 7 | How many employees does Microsoft have on Mars? | Unanswerable | Refuse | ✅ Refused | System correctly refused; did not hallucinate |
| 8 | What is Apple's share price today? | Unanswerable | Refuse | ✅ Refused | 10-K filings do not contain live prices |

## Summary Metrics

| Metric | Score | Interpretation |
|--------|-------|---------------|
| Factual accuracy | 5 / 5 (100%) | All answerable questions returned correct figures traceable to filing |
| Hallucination rate | 0 / 3 (0%) | System refused all unanswerable questions; never invented a number |
| Citation accuracy | High | Every answer cites filing name and line number from parser |

## Honest Interpretation

The 100% factual accuracy and 0% hallucination rate look strong but the question set is small (8 questions). Confidence would be higher with 30–50 questions covering edge cases: restatements, unit ambiguity (millions vs. billions), cross-company comparisons, and multi-hop reasoning ("which company had the highest FCF margin in FY2024?").

The most likely failure mode in production is **retrieval miss**: the RAG chunks the filing as plain text, so financial values embedded in tightly formatted HTML tables may not be retrieved verbatim — the parser handles this for the pre-defined metrics, but ad-hoc questions about unlisted metrics are at risk.

A second risk is **unit confusion**: the filings report figures in millions, and the parser converts to billions. A question asking "What is Apple's revenue in millions?" would get the right number but wrong unit label if the LLM doesn't catch the conversion.

Both are noted in WRITEUP.md under "What I'd fix first."
