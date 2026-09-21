from pathlib import Path
import matplotlib.pyplot as plt
import networkx as nx


def build_graph(data):
    graph = nx.DiGraph()
    for row in data["functions"].itertuples(index=False):
        graph.add_node(str(row.function_id), function_name=str(row.function_name),
                       is_critical_endpoint=bool(row.is_critical_endpoint))
    for row in data["dependencies"].itertuples(index=False):
        graph.add_edge(str(row.source_function_id), str(row.target_function_id), source_id=str(row.source_id))
    return graph


def write_graph(graph, output_dir: str | Path) -> None:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(graph, output / "dependency_graph.graphml")
    plt.figure(figsize=(11, 7))
    positions = nx.spring_layout(graph, seed=42)
    labels = {node: graph.nodes[node].get("function_name", node) for node in graph.nodes}
    nx.draw_networkx(graph, positions, labels=labels, node_color="#cfe8f3", arrows=True,
                     font_family="sans-serif", font_size=9, node_size=2500)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output / "dependency_graph.png", dpi=180)
    plt.close()
