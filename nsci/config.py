from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass(frozen=True)
class Config:
    fci_method: str = "arithmetic"
    normalization_method: str = "percentile_rank"
    minimum_normalization_peers: int = 3
    minimum_data_coverage: float = 1.0
    minimum_deployment_data_coverage: float = 1.0
    company_aggregation: str = "top_k_mean"
    top_k: int = 3
    minimum_company_function_coverage: float = 1.0
    minimum_valid_functions: int = 1
    max_evaluation_hours: int = 720


def load_config(path: str | Path | None = None) -> Config:
    if path is None:
        return Config()
    with Path(path).open(encoding="utf-8") as handle:
        values = yaml.safe_load(handle) or {}
    config = Config(**values)
    if config.fci_method not in {"arithmetic", "geometric"}:
        raise ValueError("fci_method must be arithmetic or geometric")
    if config.normalization_method not in {"percentile_rank", "minmax"}:
        raise ValueError("normalization_method must be percentile_rank or minmax")
    if config.company_aggregation not in {"top_k_mean", "max"}:
        raise ValueError("company_aggregation must be top_k_mean or max")
    for name in ("minimum_data_coverage", "minimum_deployment_data_coverage", "minimum_company_function_coverage"):
        if not 0 <= getattr(config, name) <= 1:
            raise ValueError(f"{name} must be between 0 and 1")
    return config
