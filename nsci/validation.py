import pandas as pd
import networkx as nx
from .graph import build_graph

REQUIRED_COLUMNS = {
    "functions": {"function_id", "function_name", "critical_time_hours", "needed_from_hour", "needed_until_hour", "is_critical_endpoint", "source_id"},
    "dependencies": {"source_function_id", "target_function_id", "source_id"},
    "companies": {"company_id", "ticker", "company_name"}, "company_functions": {"company_id", "function_id"},
    "company_metrics": {"company_id", "function_id", "metric_name", "value", "source_id", "data_date"},
    "metric_definitions": {"function_id", "metric_name", "unit", "higher_is_better", "required", "description"},
    "disasters": {"disaster_id", "disaster_name", "date"},
    "disaster_deployments": {"company_id", "function_id", "disaster_id", "deployment_status", "source_id"},
    "regional_need": {"region_id", "region_name", "function_id", "need_value", "unit", "source_id"},
    "company_regional_capacity": {"company_id", "function_id", "region_id", "capacity_value", "unit", "source_id"},
    "evidence_sources": {"source_id", "source_reference", "source_name", "source_type", "source_url", "notes"},
}
ALLOWED_EVIDENCE = {"government", "local_government", "official_disaster_report", "academic", "expert_interview"}


def validate_data(data):
    errors, warnings = [], []
    for name, columns in REQUIRED_COLUMNS.items():
        missing = columns - set(data[name].columns)
        if missing:
            errors.append(f"{name}: missing columns {sorted(missing)}")
    if errors:
        return errors, warnings
    sources = set(data["evidence_sources"].source_id.astype(str))
    if data["evidence_sources"].source_reference.isna().any() or (data["evidence_sources"].source_reference.astype(str).str.strip() == "").any():
        errors.append("evidence_sources: source_reference is required")
    for name in ("functions", "dependencies", "company_metrics", "disaster_deployments", "regional_need", "company_regional_capacity"):
        if data[name].source_id.isna().any() or (data[name].source_id.astype(str).str.strip() == "").any():
            errors.append(f"{name}: source_id is required")
        unknown = set(data[name].source_id.dropna().astype(str)) - sources
        if unknown: errors.append(f"{name}: unknown source_id {sorted(unknown)}")
    forbidden_metric_columns = {"unit", "higher_is_better"} & set(data["company_metrics"].columns)
    if forbidden_metric_columns:
        errors.append(f"company_metrics: definition-controlled columns are forbidden: {sorted(forbidden_metric_columns)}")
    function_ids = set(data["functions"].function_id.astype(str)); company_ids = set(data["companies"].company_id.astype(str)); disaster_ids = set(data["disasters"].disaster_id.astype(str))
    for name, column, known in (("dependencies", "source_function_id", function_ids), ("dependencies", "target_function_id", function_ids), ("company_functions", "function_id", function_ids), ("company_functions", "company_id", company_ids), ("company_metrics", "function_id", function_ids), ("company_metrics", "company_id", company_ids), ("regional_need", "function_id", function_ids), ("company_regional_capacity", "function_id", function_ids), ("company_regional_capacity", "company_id", company_ids), ("disaster_deployments", "company_id", company_ids), ("disaster_deployments", "function_id", function_ids), ("disaster_deployments", "disaster_id", disaster_ids)):
        unknown = set(data[name][column].astype(str)) - known
        if unknown: errors.append(f"{name}.{column}: unknown IDs {sorted(unknown)}")
    source_types = data["evidence_sources"].set_index("source_id").source_type.astype(str)
    for row in data["dependencies"].itertuples(index=False):
        if source_types.get(row.source_id) not in ALLOWED_EVIDENCE: errors.append(f"dependencies: source {row.source_id} has an unapproved source_type")
    if data["dependencies"].duplicated(["source_function_id", "target_function_id"]).any(): errors.append("dependencies: duplicate edge")
    if data["company_metrics"].duplicated(["company_id", "function_id", "metric_name"]).any(): errors.append("company_metrics: duplicate company/function/metric")
    if (pd.to_numeric(data["company_regional_capacity"].capacity_value, errors="coerce") < 0).any(): errors.append("company_regional_capacity: negative capacity")
    needs_by_region = data["regional_need"][["function_id", "region_id", "unit"]].drop_duplicates()
    capacity_units = data["company_regional_capacity"].merge(needs_by_region, on=["function_id", "region_id"], how="left", suffixes=("_capacity", "_need"))
    mismatched_units = capacity_units[capacity_units.unit_need.notna() & (capacity_units.unit_capacity.astype(str) != capacity_units.unit_need.astype(str))]
    if not mismatched_units.empty: errors.append("regional_need/company_regional_capacity: unit mismatch")
    times = data["functions"]
    if (pd.to_numeric(times.critical_time_hours, errors="coerce") < 0).any() or (pd.to_numeric(times.critical_time_hours, errors="coerce") > 720).any() or (pd.to_numeric(times.needed_until_hour, errors="coerce") < pd.to_numeric(times.needed_from_hour, errors="coerce")).any(): errors.append("functions: invalid time range")
    definitions = set(zip(data["metric_definitions"].function_id.astype(str), data["metric_definitions"].metric_name.astype(str)))
    for row in data["company_metrics"].itertuples(index=False):
        if (str(row.function_id), str(row.metric_name)) not in definitions: errors.append(f"company_metrics: undefined metric {row.function_id}/{row.metric_name}")
    if not set(data["disaster_deployments"].deployment_status.astype(str)) <= {"deployed", "not_deployed", "unknown"}: errors.append("disaster_deployments: invalid deployment_status")
    graph = build_graph(data)
    if not nx.is_directed_acyclic_graph(graph): warnings.append("dependencies: circular dependency detected; centralities are still calculated")
    return errors, warnings
