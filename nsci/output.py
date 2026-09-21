from pathlib import Path
import pandas as pd


def write_outputs(output_dir, function_scores, company_function_scores, company_scores, phase_scores, data):
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    function_scores.to_csv(output / "function_scores.csv", index=False)
    columns = ["company_name", "ticker", "function_name", "reach", "betweenness", "urgency", "critical_endpoint_reach", "FCI", "CapabilityScore", "DeploymentRate", "data_coverage", "deployment_data_coverage", "ECI", "GCI", "NSCI", "NSCI_100", "status"]
    company_function_scores[columns].rename(columns={"company_name": "company", "function_name": "function"}).to_csv(output / "company_function_scores.csv", index=False)
    company_scores.to_csv(output / "company_scores.csv", index=False)
    phase_scores.to_csv(output / "phase_scores.csv", index=False)
    source_frames = []
    for name in ("functions", "dependencies", "company_metrics", "disaster_deployments", "regional_need", "company_regional_capacity"):
        frame = data[name]
        if "source_id" in frame:
            source_frames.append(frame.assign(data_table=name))
    evidence = pd.concat(source_frames, ignore_index=True, sort=False).merge(data["evidence_sources"], on="source_id", how="left")
    evidence.to_csv(output / "evidence_report.csv", index=False)
