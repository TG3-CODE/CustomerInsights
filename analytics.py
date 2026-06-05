# analytics.py — Pure functions for computing derived financial metrics.
# No Streamlit or external dependencies — easy to unit-test.

def _safe(a, b, fn):
    """Apply fn(a, b) only if both are not None, else return None."""
    return fn(a, b) if a is not None and b is not None else None

def compute_margins(data: dict) -> dict:
    """Gross, operating, and net margin percentages. None where data is unavailable."""
    rev = data["revenue"]
    return {
        "gross_margin":     [_safe(g, r, lambda g,r: round(g/r*100,1)) for g,r in zip(data["gross_profit"],     rev)],
        "operating_margin": [_safe(o, r, lambda o,r: round(o/r*100,1)) for o,r in zip(data["operating_income"], rev)],
        "net_margin":       [_safe(n, r, lambda n,r: round(n/r*100,1)) for n,r in zip(data["net_income"],       rev)],
    }

def compute_yoy_growth(values: list) -> list:
    """Year-over-year percentage growth. None where prior year is unavailable."""
    result = [None]
    for i in range(1, len(values)):
        prev, curr = values[i - 1], values[i]
        result.append(round((curr - prev) / prev * 100, 1) if prev and curr else None)
    return result

def compute_fcf(data: dict) -> list:
    """Free Cash Flow = Operating Cash Flow − Capital Expenditures."""
    return [_safe(o, c, lambda o,c: round(o-c, 3)) for o,c in zip(data["operating_cf"], data["capex"])]

def compute_cagr(values: list, years: int = 2) -> float:
    """Compound Annual Growth Rate over `years` periods. None if data missing."""
    vals = [v for v in values if v is not None]
    if len(vals) < 2 or vals[0] <= 0:
        return None
    return round(((vals[-1] / vals[0]) ** (1 / years) - 1) * 100, 1)

def compute_debt_to_assets(data: dict) -> list:
    """Total debt as a percentage of total assets. Returns None where data is unavailable."""
    return [
        round(d / a * 100, 1) if d is not None and a is not None else None
        for d, a in zip(data["total_debt"], data["total_assets"])
    ]

def compute_debt_to_equity(data: dict) -> list:
    """
    Debt-to-equity ratio = Total debt ÷ Shareholders equity.
    Formula: leverage = debt / equity (x times, not %).
    Returns None where data is unavailable (e.g. FY2023 balance sheet not in filing).
    """
    return [
        round(d / e, 2) if d is not None and e is not None and e != 0 else None
        for d, e in zip(data["total_debt"], data["equity"])
    ]
