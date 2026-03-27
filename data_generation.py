"""
data_generation.py

Generates simulation data for three data sources (Smart Scale, Cloud Service, Manual Input)
across different scenarios (Stable, Degradation, Dynamic). For each scenario, the script produces:
- Ground Truth KPIs: ideal KPI values for each provider.
- estimated KPIs: simulated estimated values with delay and noise, representing measurement imperfections.

Considered KPIs:
- reliability
- latency
- availability

Data is saved as CSV files for each provider and scenario.
"""

import logging
import os
import pandas as pd
import random
from typing import Dict, List

from model import DataSource, GetWeightKpiProfile, Scenario, TOTAL_TIME_SIMULATION


# ---------------------------
# Logging configuration
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


# ---------------------------
# Set random seed for reproducibility
# ---------------------------
random.seed(1234)


# ---------------------------
# Base KPI profiles for each data source
# These represent the baseline from which simulations start
# ---------------------------
base_kpi_profiles = {
    DataSource.smart_scale: GetWeightKpiProfile(
        reliability=0.95,
        latency=1.2
    ),
    DataSource.cloud_service: GetWeightKpiProfile(
        reliability=0.9,
        latency=1.8
    ),
    DataSource.manual_input: GetWeightKpiProfile(
        reliability=0.85,
        latency=1.0
    )
}


# ---------------------------
# Ground Truth Generation
# ---------------------------
def generate_ground_truth(scenario: Scenario) -> Dict[DataSource, List[GetWeightKpiProfile]]:
    """
    Method that generates the ground truth KPI profiles for a given scenario.

    :param scenario: The scenario to simulate (stable, degradation, dynamic)
    :type scenario: Scenario
    :return: Dictionary mapping each DataSource to a list of KPI profiles over time
    :rtype: Dict[DataSource, List[GetWeightKpiProfile]]
    """
    scenario_kpis = {}

    for ds in DataSource:
        ds_ground_truth = []

        for t in range(TOTAL_TIME_SIMULATION):
            base_reliability = base_kpi_profiles[ds].reliability
            base_latency = base_kpi_profiles[ds].latency

            # ---------------------------
            # Stable scenario: KPIs remain constant
            # ---------------------------
            if scenario == Scenario.stable:
                ds_ground_truth.append(GetWeightKpiProfile(
                    reliability=base_reliability,
                    latency=base_latency
                ))

            # ---------------------------
            # Degradation scenario: slow deterioration of some KPIs
            # ---------------------------
            elif scenario == Scenario.degradation:
                if ds == DataSource.smart_scale:
                    ds_ground_truth.append(GetWeightKpiProfile(
                        reliability=max(0.60, base_reliability - 0.0003 * t),
                        latency=min(3.50, base_latency + 0.0015 * t)
                    ))
                else:
                    ds_ground_truth.append(GetWeightKpiProfile(
                        reliability=base_reliability,
                        latency=base_latency
                    ))

            # ---------------------------
            # Dynamic scenario: temporary and sudden KPI changes
            # ---------------------------
            elif scenario == Scenario.dynamic:
                if ds == DataSource.smart_scale:
                    if t in range(200, 350):
                        ds_ground_truth.append(GetWeightKpiProfile(0.75, 2.8))
                    elif t in range(500, 650):
                        ds_ground_truth.append(GetWeightKpiProfile(0.92, 1.4))
                    elif t in range(850, 1000):
                        ds_ground_truth.append(GetWeightKpiProfile(0.65, 3.2))
                    else:
                        ds_ground_truth.append(GetWeightKpiProfile(
                            reliability=base_reliability,
                            latency=base_latency
                        ))

                elif ds == DataSource.cloud_service:
                    if t in range(350, 500):
                        ds_ground_truth.append(GetWeightKpiProfile(0.93, 1.4))
                    elif t in range(700, 850):
                        ds_ground_truth.append(GetWeightKpiProfile(0.78, 2.6))
                    else:
                        ds_ground_truth.append(GetWeightKpiProfile(
                            reliability=base_reliability,
                            latency=base_latency
                        ))

                elif ds == DataSource.manual_input:
                    if t in range(500, 650):
                        ds_ground_truth.append(GetWeightKpiProfile(0.88, 0.9))
                    else:
                        ds_ground_truth.append(GetWeightKpiProfile(
                            reliability=base_reliability,
                            latency=base_latency
                        ))

        scenario_kpis[ds] = ds_ground_truth

    return scenario_kpis


# ---------------------------
# estimated KPI Generation
# ---------------------------
def generate_estimated_kpi(
        ground_truth: Dict[DataSource, List[GetWeightKpiProfile]]
) -> Dict[DataSource, List[GetWeightKpiProfile]]:
    """
    Method that generates estimated KPI profiles by introducing random noise
    and measurement delay.

    :param ground_truth: The ground truth KPI profiles for each DataSource
    :type ground_truth: Dict[DataSource, List[GetWeightKpiProfile]]
    :return: Dictionary mapping each DataSource to a list of estimated KPI profiles
    :rtype: Dict[DataSource, List[GetWeightKpiProfile]]
    """
    scenario_kpis = {}

    for ds in DataSource:
        ds_estimated_kpis = []

        for t in range(TOTAL_TIME_SIMULATION):
            # Apply delay to simulate non-instantaneous measurements
            delayed_reliability = ground_truth[ds][t-5].reliability if t-5 >= 0 else base_kpi_profiles[ds].reliability
            delayed_latency = ground_truth[ds][t-3].latency if t-3 >= 0 else base_kpi_profiles[ds].latency

            # Add random noise
            ds_estimated_kpis.append(GetWeightKpiProfile(
                reliability=delayed_reliability + random.uniform(-0.03, 0.03),
                latency=delayed_latency + random.uniform(-0.20, 0.20)
            ))

        scenario_kpis[ds] = ds_estimated_kpis

    return scenario_kpis


# ---------------------------
# Main execution
# ---------------------------
if __name__ == '__main__':
    logger.info("Starting KPI generation pipeline")

    # Create the 'data' folder if it does not exist
    os.makedirs('data', exist_ok=True)

    # Iterate over all scenarios
    for scenario in Scenario:
        logger.info(f"Processing scenario: {scenario.name}")

        os.makedirs(f'data/{scenario.name}', exist_ok=True)

        # Generate ground truth and estimated KPIs
        logger.info("Generating ground truth KPIs")
        ground_truth = generate_ground_truth(scenario)

        logger.info("Generating estimated KPIs")
        estimated = generate_estimated_kpi(ground_truth)

        # Save CSV files for each provider
        for ds in DataSource:
            logger.info(f"Saving data for DataSource: {ds.name}")

            ground_truth_df = pd.DataFrame([vars(kpi) for kpi in ground_truth[ds]])
            ground_truth_df.to_csv(
                f'data/{scenario.name}/{ds.name}_ground_truth.csv',
                index_label="t"
            )

            estimated_df = pd.DataFrame([vars(kpi) for kpi in estimated[ds]])
            estimated_df.to_csv(
                f'data/{scenario.name}/{ds.name}_estimated.csv',
                index_label="t"
            )

    logger.info("KPI generation completed successfully")
