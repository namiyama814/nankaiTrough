import math
import networkx as nx
import pandas as pd


def calculate_function_scores(data, graph, config) -> pd.DataFrame:
    functions = data["functions"].copy()
    total = len(functions)
    endpoints = set(functions.loc[functions["is_critical_endpoint"].astype(bool), "function_id"].astype(str))
    betweenness = nx.betweenness_centrality(graph, normalized=True)
    records = []
    for row in functions.itertuples(index=False):
        function_id = str(row.function_id)
        descendants = nx.descendants(graph, function_id)
        reach = len(descendants) / (total - 1) if total > 1 else 0.0
        endpoint_reach = len(({function_id} | descendants) & endpoints) / len(endpoints) if endpoints else 0.0
        urgency = 1 - math.log1p(float(row.critical_time_hours)) / math.log1p(config.max_evaluation_hours)
        urgency = max(0.0, min(1.0, urgency))
        values = [reach, betweenness.get(function_id, 0.0), urgency, endpoint_reach]
        fci = sum(values) / len(values) if config.fci_method == "arithmetic" else math.prod(values) ** (1 / len(values))
        records.append({"function_id": function_id, "function_name": row.function_name, "reach": reach,
                        "betweenness": betweenness.get(function_id, 0.0), "urgency": urgency,
                        "critical_endpoint_reach": endpoint_reach, "FCI": fci})
    return pd.DataFrame(records)
