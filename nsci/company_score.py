import numpy as np
import pandas as pd


def _normalise_metrics(data, config) -> pd.DataFrame:
    metrics = data["company_metrics"].merge(
        data["metric_definitions"][["function_id", "metric_name", "higher_is_better", "required"]],
        on=["function_id", "metric_name"], how="inner"
    ).copy()
    records = []
    for (_, _), group in metrics.groupby(["function_id", "metric_name"], sort=True):
        peers = group["company_id"].nunique()
        ranks = group["value"].astype(float).rank(method="average")
        for index, row in group.iterrows():
            score = np.nan
            comparison_ok = peers >= config.minimum_normalization_peers
            if comparison_ok:
                values = group["value"].astype(float)
                if config.normalization_method == "percentile_rank":
                    score = (ranks.loc[index] - 1) / (len(values) - 1) if len(values) > 1 else np.nan
                else:
                    low, high = values.min(), values.max()
                    score = 1.0 if high == low else (float(row.value) - low) / (high - low)
                if not bool(row["higher_is_better"]):
                    score = 1 - score
            records.append({"company_id": str(row["company_id"]), "function_id": str(row["function_id"]),
                            "metric_name": row["metric_name"], "metric_score": score,
                            "comparison_ok": comparison_ok})
    return pd.DataFrame(records)


def calculate_eci(data, config) -> pd.DataFrame:
    definitions = data["metric_definitions"].copy()
    definitions["function_id"] = definitions.function_id.astype(str)
    required = definitions[definitions.required.astype(bool)]
    normalized = _normalise_metrics(data, config)
    deployments = data["disaster_deployments"].copy()
    disasters_count = len(data["disasters"])
    records = []
    for pair in data["company_functions"].itertuples(index=False):
        company_id, function_id = str(pair.company_id), str(pair.function_id)
        required_defs = required[required.function_id == function_id]
        required_names = set(required_defs.metric_name)
        metric_rows = normalized[(normalized.company_id == company_id) & (normalized.function_id == function_id) & (normalized.metric_name.isin(required_names))]
        observed_names = set(metric_rows.metric_name)
        coverage = len(observed_names) / len(required_names) if required_names else np.nan
        comparison_failure = bool(len(required_names) and not metric_rows.empty and not metric_rows.comparison_ok.all())
        capability = metric_rows.metric_score.mean() if not metric_rows.empty else np.nan

        dep = deployments[(deployments.company_id.astype(str) == company_id) & (deployments.function_id.astype(str) == function_id)]
        confirmed = dep[dep.deployment_status.isin(["deployed", "not_deployed"])]
        deployment_coverage = len(confirmed) / disasters_count if disasters_count else np.nan
        deployment_rate = (confirmed.deployment_status == "deployed").mean() if len(confirmed) else np.nan

        status = "ok"
        if comparison_failure:
            status = "insufficient_comparison_data"
        elif pd.isna(coverage) or coverage < config.minimum_data_coverage or pd.isna(deployment_coverage) or deployment_coverage < config.minimum_deployment_data_coverage:
            status = "insufficient_data"
        elif pd.isna(capability) or pd.isna(deployment_rate):
            status = "insufficient_data"
        eci = (capability + deployment_rate) / 2 if status == "ok" else np.nan
        records.append({"company_id": company_id, "function_id": function_id, "CapabilityScore": capability,
                        "DeploymentRate": deployment_rate, "data_coverage": coverage,
                        "deployment_data_coverage": deployment_coverage, "ECI": eci, "eci_status": status})
    return pd.DataFrame(records)


def calculate_company_function_scores(data, function_scores, eci_scores, gci_scores) -> pd.DataFrame:
    pairs = data["company_functions"].copy()
    pairs["company_id"] = pairs.company_id.astype(str)
    pairs["function_id"] = pairs.function_id.astype(str)
    companies = data["companies"].copy()
    companies["company_id"] = companies.company_id.astype(str)
    functions = data["functions"][["function_id", "function_name"]].copy()
    functions["function_id"] = functions.function_id.astype(str)
    result = (pairs.merge(companies, on="company_id", how="left")
              .merge(functions, on="function_id", how="left")
              .merge(function_scores, on=["function_id", "function_name"], how="left")
              .merge(eci_scores, on=["company_id", "function_id"], how="left")
              .merge(gci_scores, on=["company_id", "function_id"], how="left"))
    result["status"] = "ok"
    result.loc[result.eci_status != "ok", "status"] = result.loc[result.eci_status != "ok", "eci_status"]
    result.loc[(result.status == "ok") & (result.gci_status != "ok"), "status"] = result.loc[(result.status == "ok") & (result.gci_status != "ok"), "gci_status"]
    result["NSCI"] = result.FCI * result.ECI * result.GCI
    result.loc[result.status != "ok", "NSCI"] = np.nan
    result["NSCI_100"] = result.NSCI * 100
    return result


def calculate_company_scores(company_function_scores, config) -> pd.DataFrame:
    records = []
    for company_id, group in company_function_scores.groupby("company_id", sort=True):
        valid = group[(group.status == "ok") & group.NSCI.notna()]
        coverage = len(valid) / len(group) if len(group) else np.nan
        status = "ok" if len(valid) >= config.minimum_valid_functions and coverage >= config.minimum_company_function_coverage else "insufficient_data"
        overall = np.nan
        if status == "ok":
            values = valid.NSCI.sort_values(ascending=False)
            overall = values.max() if config.company_aggregation == "max" else values.head(config.top_k).mean()
        first = group.iloc[0]
        records.append({"company_id": company_id, "company": first.company_name, "ticker": first.ticker,
                        "overall_NSCI": overall, "company_function_coverage": coverage, "status": status})
    result = pd.DataFrame(records)
    result["rank"] = result.overall_NSCI.rank(method="min", ascending=False).astype("Int64")
    return result.sort_values(["rank", "company"], na_position="last")
