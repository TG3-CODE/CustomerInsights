# data.py — Company metadata, MD&A narrative quotes, and evaluation questions.
# Financial figures are NOT stored here — they are extracted live by parser.py.

COMPANIES = {
    "Apple":     {"file": "fillings/AppleEDGAR.htm",  "ticker": "AAPL",  "color": "#58a6ff"},
    "Microsoft": {"file": "fillings/MsftEDGAR.htm",   "ticker": "MSFT",  "color": "#3fb950"},
    "Google":    {"file": "fillings/GoogleEDGAR.htm",  "ticker": "GOOGL", "color": "#f78166"},
}

# Labeled evaluation question set
EVAL_QUESTIONS = [
    {
        "question": "What was Apple's total revenue in FY2025?",
        "expected": "$416.161B",
        "type":     "Factual",
        "result":   "✅ Correct",
        "notes":    "AppleEDGAR.htm — Total net sales $416,161M (p.29)",
    },
    {
        "question": "What was Microsoft's net income in FY2024?",
        "expected": "$88.136B",
        "type":     "Factual",
        "result":   "✅ Correct",
        "notes":    "MsftEDGAR.htm — Net income $88,136M (p.50)",
    },
    {
        "question": "What was Google's operating income in FY2025?",
        "expected": "$129.039B",
        "type":     "Factual",
        "result":   "✅ Correct",
        "notes":    "GoogleEDGAR.htm — Income from operations $129,039M (p.49)",
    },
    {
        "question": "What caused Microsoft's cloud gross margin to decrease in FY2025?",
        "expected": "AI infrastructure scaling costs",
        "type":     "Analytical",
        "result":   "✅ Correct",
        "notes":    "RAG retrieved exact MD&A quote about scaling AI infrastructure",
    },
    {
        "question": "What were Apple's capital expenditures in FY2024?",
        "expected": "$9.447B",
        "type":     "Factual",
        "result":   "✅ Correct",
        "notes":    "AppleEDGAR.htm — Payments for PP&E $9,447M (p.33)",
    },
    {
        "question": "What was Apple's revenue in FY1990?",
        "expected": "UNANSWERABLE — not in filings",
        "type":     "Unanswerable",
        "result":   "✅ Refused",
        "notes":    "System said: 'I cannot find this information in the provided filings.'",
    },
    {
        "question": "How many employees does Microsoft have on Mars?",
        "expected": "UNANSWERABLE — nonsensical",
        "type":     "Unanswerable",
        "result":   "✅ Refused",
        "notes":    "System correctly refused; did not hallucinate",
    },
    {
        "question": "What is Apple's exact share price today?",
        "expected": "UNANSWERABLE — not in 10-K",
        "type":     "Unanswerable",
        "result":   "✅ Refused",
        "notes":    "10-K filings do not contain current share prices",
    },
]
