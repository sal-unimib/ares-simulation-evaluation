"""
simulation.py

Simulation framework for evaluating data source selection and reconfiguration
across different scenarios (Stable, Degradation, Dynamic).

This script:
- Imports KPI profiles (ground truth and observed) from CSV files.
- Evaluates feasibility of each data source.
- Computes scores to select the best data source.
- Simulates system reconfiguration over time according to ARES policy.
- Records iterations of simulation including ground truth, baseline, and ARES decisions.

Key parameters:
- TOTAL_TIME_SIMULATION: total number of time steps per scenario
- ARES_RECONFIG_FREQUENCY: how often ARES performs reconfiguration
"""

from model import GetWeightKpiProfile, DataSource, Scenario, Simulation, SimulationIteration, ARES_RECONFIG_FREQUENCY, TOTAL_TIME_SIMULATION
from typing import Dict, List, Tuple
import pandas as pd

# ---------------------------
# Feasibility function
# ---------------------------
def feasible(kpi_profile: GetWeightKpiProfile) -> bool:
    """
    Method to evaluate if a Data Source configuration is feasible.

    :param kpi_profile: The current KPI profile to analyze
    :type kpi_profile: GetWeightKpiProfile
    :return: True if the Data Source is feasible, False otherwise
    :rtype: bool
    """
    return kpi_profile.reliability >= 0.9 and kpi_profile.latency <= 2.0

# ---------------------------
# Score function
# ---------------------------
def score(kpi_profile: GetWeightKpiProfile) -> float:
    """
    Method that computes a weighted score for a KPI profile.

    :param kpi_profile: The KPI profile to score
    :type kpi_profile: GetWeightKpiProfile
    :return: Weighted score combining reliability and latency
    :rtype: float
    """
    wr = 0.7  # weight for reliability
    wl = 0.3  # weight for latency
    l_max = 5.0  # maximum latency normalization
    norm_lat = min(1.0, kpi_profile.latency / l_max)
    return wr * kpi_profile.reliability - wl * norm_lat

# ---------------------------
# Data Source selection
# ---------------------------
def data_sources_selection(ds_profiles: Dict[DataSource, GetWeightKpiProfile]) -> DataSource:
    """
    Method to select the best Data Source based on maximizing the score function.

    :param ds_profiles: Current KPI profiles of all Data Sources
    :type ds_profiles: Dict[DataSource, GetWeightKpiProfile]
    :return: The Data Source that maximizes the score
    :rtype: DataSource
    """
    ds_scores = {ds: score(kpi) for ds, kpi in ds_profiles.items()}
    return max(ds_scores, key=ds_scores.get)

# ---------------------------
# Reconfiguration logic
# ---------------------------
def reconfiguration(ds_profiles: Dict[DataSource, GetWeightKpiProfile]) -> Tuple[DataSource, bool]:
    """
    Method that performs the reconfiguration of the active data source.

    Considers only feasible data sources, selects the one with the best score,
    and returns the selected configuration along with feasibility.

    :param ds_profiles: Current KPI profiles of all Data Sources
    :type ds_profiles: Dict[DataSource, GetWeightKpiProfile]
    :return: Tuple of (selected Data Source, feasibility flag)
    :rtype: Tuple[DataSource, bool]
    """
    ds_feasibles = {ds: kpi for ds, kpi in ds_profiles.items() if feasible(kpi)}
    new_conf_feasibility = len(ds_feasibles) > 0
    new_conf = data_sources_selection(ds_feasibles if new_conf_feasibility else ds_profiles)
    return new_conf, new_conf_feasibility

# ---------------------------
# KPI profiles import
# ---------------------------
def import_kpi_profiles(scenario: Scenario) -> Tuple[Dict[DataSource, List[GetWeightKpiProfile]], Dict[DataSource, List[GetWeightKpiProfile]]]:
    """
    Method to import KPI profiles from CSV files for a given scenario.

    :param scenario: The scenario to import data from
    :type scenario: Scenario
    :return: Tuple of dictionaries containing ground truth and observed KPIs
    :rtype: Tuple[Dict[DataSource, List[GetWeightKpiProfile]] , Dict[DataSource, List[GetWeightKpiProfile]]]
    """
    ground_truth_kpis = {}
    observed_kpis = {}

    for ds in DataSource:
        # Ground truth
        ds_gt_df = pd.read_csv(f"data/{scenario.name}/{ds.name}_ground_truth.csv")
        ds_gt_kpis = [GetWeightKpiProfile(row.reliability, row.latency, row.availability) for _, row in ds_gt_df.iterrows()]
        ground_truth_kpis[ds] = ds_gt_kpis

        # Observed
        ds_est_df = pd.read_csv(f"data/{scenario.name}/{ds.name}_observed.csv")
        ds_est_kpis = [GetWeightKpiProfile(row.reliability, row.latency, row.availability) for _, row in ds_est_df.iterrows()]
        observed_kpis[ds] = ds_est_kpis

    return ground_truth_kpis, observed_kpis

# ---------------------------
# Simulation
# ---------------------------
def simulate(scenario: Scenario) -> Simulation:
    """
    Method to run the full simulation for a given scenario.

    Steps:
    1. Import ground truth and observed KPI profiles.
    2. For each time step:
        - Evaluate current KPIs.
        - Compute ground truth configuration.
        - Compute baseline configuration.
        - Compute ARES reconfiguration every ARES_RECONFIG_FREQUENCY steps.
    3. Store each iteration in a Simulation object.

    :param scenario: The scenario to simulate
    :type scenario: Scenario
    :return: Simulation object containing KPI profiles and iterations
    :rtype: Simulation
    """
    ground_truth_kpis, observed_kpis = import_kpi_profiles(scenario)
    iterations: List[SimulationIteration] = []

    ares_configuration = None
    ares_feasibility = False

    for t in range(TOTAL_TIME_SIMULATION):
        # Current KPI profiles
        actual_gt_kpis = {ds: ground_truth_kpis[ds][t] for ds in DataSource}
        actual_observed_kpis = {ds: observed_kpis[ds][t] for ds in DataSource}

        # Reconfiguration decisions
        gt_configuration, gt_feasibility = reconfiguration(actual_gt_kpis)
        baseline_configuration, baseline_feasibility = reconfiguration(actual_observed_kpis)
        if t % ARES_RECONFIG_FREQUENCY == 0:
            ares_configuration, ares_feasibility = reconfiguration(actual_observed_kpis)

        # Store iteration
        iterations.append(SimulationIteration(
            ground_truth_configuration=gt_configuration,
            ground_truth_configuration_feasibility=gt_feasibility,
            baseline_configuration=baseline_configuration,
            baseline_configuration_feasibility=baseline_feasibility,
            ares_configuration=ares_configuration,
            ares_configuration_feasibility=ares_feasibility,
            ares_reconfiguration=t % ARES_RECONFIG_FREQUENCY == 0
        ))

    return Simulation(
        scenario=scenario,
        ground_truth_kpi_profiles=ground_truth_kpis,
        observed_kpi_profiles=observed_kpis,
        iterations=iterations
    )

# ---------------------------
# Main execution
# ---------------------------
if __name__ == '__main__':
    for scenario in Scenario:
        scenario_sim = simulate(scenario)
        # TODO: calculate metrics (RQ1, RQ2, RQ3)
        scenario_sim.to_csv()