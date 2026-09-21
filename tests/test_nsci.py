from pathlib import Path
import shutil
import pandas as pd
import pytest
from nsci.config import load_config
from nsci.data_loader import load_data
from nsci.graph import build_graph
from nsci.function_score import calculate_function_scores
from nsci.company_score import calculate_eci, calculate_company_function_scores, calculate_company_scores
from nsci.geography import calculate_gci
from nsci.validation import validate_data

DATA = Path(__file__).parents[1] / "data"


def scores(data=None):
    data = data or load_data(DATA)
    config = load_config(Path(__file__).parents[1] / "config.yaml")
    functions = calculate_function_scores(data, build_graph(data), config)
    eci = calculate_eci(data, config)
    gci = calculate_gci(data)
    return functions, eci, gci, calculate_company_function_scores(data, functions, eci, gci), config


def test_function_network_scores():
    function_scores, *_ = scores()
    indexed = function_scores.set_index("function_id")
    assert indexed.loc["power", "reach"] > indexed.loc["telecom", "reach"]
    assert indexed.loc["telecom", "betweenness"] > 0
    assert indexed.loc["power", "urgency"] > indexed.loc["telecom", "urgency"]
    assert indexed.loc["rescue", "critical_endpoint_reach"] == 1
    assert indexed.loc["rescue", "FCI"] > 0


def test_nscis_and_company_ranking_are_deterministic():
    _, _, _, first, config = scores()
    _, _, _, second, _ = scores()
    pd.testing.assert_frame_equal(first, second)
    company_scores = calculate_company_scores(first, config)
    assert company_scores.iloc[0].company_id == "alpha"
    assert (first.NSCI >= 0).all()


def test_unknown_deployment_is_not_zero(tmp_path):
    target = tmp_path / "data"; shutil.copytree(DATA, target)
    file = target / "disaster_deployments.csv"
    dep = pd.read_csv(file)
    dep.loc[(dep.company_id == "alpha") & (dep.function_id == "power") & (dep.disaster_id == "d3"), "deployment_status"] = "unknown"
    dep.to_csv(file, index=False)
    _, eci, *_ = scores(load_data(target))
    row = eci[(eci.company_id == "alpha") & (eci.function_id == "power")].iloc[0]
    assert row.DeploymentRate == 1
    assert row.deployment_data_coverage < 1
    assert row.eci_status == "insufficient_data"


def test_insufficient_comparison_data(tmp_path):
    target = tmp_path / "data"; shutil.copytree(DATA, target)
    file = target / "company_metrics.csv"
    metrics = pd.read_csv(file)
    metrics = metrics[~((metrics.company_id == "gamma") & (metrics.function_id == "power"))]
    metrics.to_csv(file, index=False)
    _, eci, *_ = scores(load_data(target))
    assert eci[(eci.company_id == "alpha") & (eci.function_id == "power")].iloc[0].eci_status == "insufficient_comparison_data"


def test_missing_regional_capacity_is_na(tmp_path):
    target = tmp_path / "data"; shutil.copytree(DATA, target)
    file = target / "company_regional_capacity.csv"
    capacity = pd.read_csv(file)
    capacity = capacity[~((capacity.company_id == "alpha") & (capacity.function_id == "power") & (capacity.region_id == "kochi"))]
    capacity.to_csv(file, index=False)
    _, _, gci, company_function, _ = scores(load_data(target))
    row = gci[(gci.company_id == "alpha") & (gci.function_id == "power")].iloc[0]
    assert pd.isna(row.GCI)
    assert company_function[(company_function.company_id == "alpha") & (company_function.function_id == "power")].iloc[0].status == "insufficient_data"


def test_validation_detects_unknown_source_and_unit_mismatch():
    data = load_data(DATA)
    data["dependencies"].loc[0, "source_id"] = "unknown"
    errors, _ = validate_data(data)
    assert any("unknown source_id" in error for error in errors)
    data = load_data(DATA)
    data["company_regional_capacity"].loc[0, "unit"] = "異なる単位"
    errors, _ = validate_data(data)
    assert any("unit mismatch" in error for error in errors)
