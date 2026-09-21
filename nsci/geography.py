import pandas as pd


def calculate_gci(data) -> pd.DataFrame:
    needs = data["regional_need"]
    capacities = data["company_regional_capacity"]
    company_functions = data["company_functions"]
    records = []
    for pair in company_functions.itertuples(index=False):
        company_id, function_id = str(pair.company_id), str(pair.function_id)
        function_needs = needs[needs.function_id.astype(str) == function_id]
        matching = capacities[(capacities.company_id.astype(str) == company_id) & (capacities.function_id.astype(str) == function_id)]
        if function_needs.empty:
            records.append({"company_id": company_id, "function_id": function_id, "GCI": float("nan"), "gci_status": "insufficient_data"})
            continue
        merged = function_needs.merge(matching, on=["function_id", "region_id"], how="left", suffixes=("_need", "_capacity"))
        if merged.capacity_value.isna().any():
            records.append({"company_id": company_id, "function_id": function_id, "GCI": float("nan"), "gci_status": "insufficient_data"})
            continue
        if (merged.unit_need.astype(str) != merged.unit_capacity.astype(str)).any():
            records.append({"company_id": company_id, "function_id": function_id, "GCI": float("nan"), "gci_status": "unit_mismatch"})
            continue
        denominator = merged.need_value.sum()
        gci = (merged.need_value * (merged.capacity_value / merged.need_value).clip(upper=1)).sum() / denominator if denominator > 0 else float("nan")
        records.append({"company_id": company_id, "function_id": function_id, "GCI": gci, "gci_status": "ok"})
    return pd.DataFrame(records)
