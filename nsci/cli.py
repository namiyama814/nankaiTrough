import argparse
from pathlib import Path
from .config import load_config
from .data_loader import load_data
from .validation import validate_data
from .graph import build_graph, write_graph
from .function_score import calculate_function_scores
from .company_score import calculate_eci, calculate_company_function_scores, calculate_company_scores
from .geography import calculate_gci
from .phases import calculate_phase_scores
from .output import write_outputs


def _validate_or_exit(data):
    errors, warnings = validate_data(data)
    for warning in warnings:
        print(f"WARNING: {warning}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return False
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m nsci")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "calculate", "graph"):
        item = subparsers.add_parser(command)
        item.add_argument("--data", required=True)
        if command != "validate": item.add_argument("--output", required=True)
        item.add_argument("--config", default=None)
    args = parser.parse_args(argv)
    data = load_data(args.data)
    if not _validate_or_exit(data):
        raise SystemExit(1)
    if args.command == "validate":
        print("Validation passed.")
        return
    graph = build_graph(data)
    if args.command == "graph":
        write_graph(graph, args.output)
        print(f"Graph written to {Path(args.output)}")
        return
    config = load_config(args.config)
    function_scores = calculate_function_scores(data, graph, config)
    eci_scores = calculate_eci(data, config)
    gci_scores = calculate_gci(data)
    company_function_scores = calculate_company_function_scores(data, function_scores, eci_scores, gci_scores)
    company_scores = calculate_company_scores(company_function_scores, config)
    phase_scores = calculate_phase_scores(data, company_function_scores)
    write_outputs(args.output, function_scores, company_function_scores, company_scores, phase_scores, data)
    write_graph(graph, args.output)
    print(f"NSCI outputs written to {Path(args.output)}")


if __name__ == "__main__":
    main()
