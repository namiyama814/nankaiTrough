from pathlib import Path
import pandas as pd

FILES = {
    "functions": "functions.csv", "dependencies": "dependencies.csv", "companies": "companies.csv",
    "company_functions": "company_functions.csv", "company_metrics": "company_metrics.csv",
    "metric_definitions": "metric_definitions.csv", "disasters": "disasters.csv",
    "disaster_deployments": "disaster_deployments.csv", "regional_need": "regional_need.csv",
    "company_regional_capacity": "company_regional_capacity.csv", "evidence_sources": "evidence_sources.csv",
}


def load_data(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    root = Path(data_dir)
    missing = [filename for filename in FILES.values() if not (root / filename).is_file()]
    if missing:
        raise FileNotFoundError("Missing input CSV files: " + ", ".join(missing))
    return {name: pd.read_csv(root / filename, keep_default_na=True) for name, filename in FILES.items()}
