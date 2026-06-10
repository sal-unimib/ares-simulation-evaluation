"""
model.py

Definition of the core data structures for the simulation framework.

This module defines:
- Constants for simulation timing.
- Enumerations for Data Sources and Scenarios.
- Data classes for KPI profiles, simulation iterations, and full simulations.
- Methods to serialize/deserialize simulation results to CSV files.
"""

from dataclasses import dataclass
from enum import Enum
import pandas as pd
from typing import Dict, List

# ---------------------------
# Simulation configuration constants
# ---------------------------
TOTAL_TIME_SIMULATION = 1200
"""Number of iterations (task requests) for the simulation."""

ARES_RECONFIG_FREQUENCY = 25
"""Number of iterations between consecutive ARES reconfigurations."""


# ---------------------------
# Enumerations
# ---------------------------
class DataSource(Enum):
    """
    Enumeration of the simulation Data Sources.
    """
    smartwatch = "SmartWatch"
    cloud_service = "Cloud Service"
    manual_input = "Manual Input"

class Scenario(Enum):
    """
    Enumeration of the simulation scenarios.
    """
    stable = "Stable"
    degradation = "Degradation"
    dynamic = "Dynamic"


# ---------------------------
# Data classes
# ---------------------------
@dataclass
class GetHeartRateKpiProfile:
    """
    Class to represent the KPI profile for the GetHeartRate capability and a given data source at a specific time.

    Attributes:
    -----------
    reliability : float
        Value for the reliability KPI.
    latency : float
        Value for the latency KPI.
    """
    reliability: float
    latency: float

@dataclass
class SimulationIteration:
    """
    Class representing the result of a single simulation iteration.

    Attributes:
    -----------
    ground_truth_configuration : DataSource
        Data Source chosen according to the ground truth KPI profiles.
    ground_truth_configuration_feasibility : bool
        Feasibility of the ground truth active configuration.
    baseline_configuration : DataSource
        Data Source chosen by the baseline strategy.
    baseline_configuration_feasibility : bool
        Feasibility of the baseline active configuration.
    ares_configuration : DataSource
        Data Source chosen by the ARES strategy.
    ares_configuration_feasibility : bool
        Feasibility of the ARES active configuration.
    ares_reconfiguration : bool
        Indicates if ARES triggered a reconfiguration at this iteration.
    """
    ground_truth_configuration: DataSource
    ground_truth_configuration_feasibility: bool
    baseline_configuration: DataSource
    baseline_configuration_feasibility: bool
    ares_configuration: DataSource
    ares_configuration_feasibility: bool
    ares_reconfiguration: bool

@dataclass
class Simulation:
    """
    Class representing the full simulation for a given scenario.

    Attributes:
    -----------
    scenario : Scenario
        Type of simulation scenario.
    ground_truth_kpi_profiles : Dict[DataSource, List[GetHeartRateKpiProfile]]
        Real KPI profiles for all Data Sources across all iterations.
    estimated_kpi_profiles : Dict[DataSource, List[GetHeartRateKpiProfile]]
        estimated KPI profiles for all Data Sources across all iterations.
    iterations : List[SimulationIteration]
        List of simulation iteration results.
    """
    scenario: Scenario
    ground_truth_kpi_profiles: Dict[DataSource, List[GetHeartRateKpiProfile]]
    estimated_kpi_profiles: Dict[DataSource, List[GetHeartRateKpiProfile]]
    iterations: List[SimulationIteration]

    # ---------------------------
    # Export simulation to CSV
    # ---------------------------
    def to_csv(self):
        """
        Method to serialize the simulation iterations to a CSV file.

        The CSV contains:
        - Ground truth, baseline, and ARES configurations
        - Feasibility flags
        - ARES reconfiguration flag
        """
        estimated_df = pd.DataFrame([{
            'ground_truth_configuration': iter.ground_truth_configuration.value,
            'ground_truth_configuration_feasibility': iter.ground_truth_configuration_feasibility,
            'baseline_configuration': iter.baseline_configuration.value,
            'baseline_configuration_feasibility': iter.baseline_configuration_feasibility,
            'ares_configuration': iter.ares_configuration.value,
            'ares_configuration_feasibility': iter.ares_configuration_feasibility,
            'ares_reconfiguration': iter.ares_reconfiguration,
        } for iter in self.iterations])
        estimated_df.to_csv(f'data/{self.scenario.name}/simulation.csv', index_label="t")

    # ---------------------------
    # Import simulation from CSV
    # ---------------------------
    @classmethod
    def from_csv(cls, scenario: Scenario) -> "Simulation":
        """
        Method to deserialize a simulation from CSV files for a given scenario.

        Reads:
        - Ground truth KPI profiles
        - estimated KPI profiles
        - Simulation iterations results

        :param scenario: Scenario to import
        :type scenario: Scenario
        :return: Simulation object containing all KPIs and iterations
        :rtype: Simulation
        """
        ground_truth: Dict[DataSource, List[GetHeartRateKpiProfile]] = {}
        estimated: Dict[DataSource, List[GetHeartRateKpiProfile]] = {}

        for ds in DataSource:
            # Ground truth KPIs
            gt_file = f'data/{scenario.name}/{ds.name}_ground_truth.csv'
            gt_df = pd.read_csv(gt_file, index_col='t')
            ground_truth[ds] = [GetHeartRateKpiProfile(row.reliability, row.latency) for _, row in gt_df.iterrows()]

            # estimated KPIs
            obs_file = f'data/{scenario.name}/{ds.name}_estimated.csv'
            obs_df = pd.read_csv(obs_file, index_col='t')
            estimated[ds] = [GetHeartRateKpiProfile(row.reliability, row.latency) for _, row in obs_df.iterrows()]

        # Simulation iterations
        sim_file = f'data/{scenario.name}/simulation.csv'
        sim_df = pd.read_csv(sim_file, index_col='t')
        iterations: List[SimulationIteration] = [
            SimulationIteration(
                ground_truth_configuration=DataSource(row.ground_truth_configuration),
                ground_truth_configuration_feasibility=row.ground_truth_configuration_feasibility,
                baseline_configuration=DataSource(row.baseline_configuration),
                baseline_configuration_feasibility=row.baseline_configuration_feasibility,
                ares_configuration=DataSource(row.ares_configuration),
                ares_configuration_feasibility=row.ares_configuration_feasibility,
                ares_reconfiguration=row.ares_reconfiguration
            ) for _, row in sim_df.iterrows()
        ]

        return cls(
            scenario=scenario,
            ground_truth_kpi_profiles=ground_truth,
            estimated_kpi_profiles=estimated,
            iterations=iterations
        )
