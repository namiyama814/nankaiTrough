import pandas as pd

PHASES = [("0_24h", 0, 24), ("24_48h", 24, 48), ("48_72h", 48, 72), ("72_168h", 72, 168), ("168_720h", 168, 720)]


def calculate_phase_scores(data, company_function_scores: pd.DataFrame) -> pd.DataFrame:
    functions = data["functions"][["function_id", "needed_from_hour", "needed_until_hour"]]
    base = company_function_scores.merge(functions, on="function_id", how="left")
    records = []
    for row in base.itertuples(index=False):
        for phase, start, end in PHASES:
            active = float(row.needed_from_hour) < end and float(row.needed_until_hour) > start
            records.append({"company": row.company_name, "ticker": row.ticker, "function": row.function_name,
                            "phase": phase, "active": active, "NSCI": row.NSCI})
    return pd.DataFrame(records)
