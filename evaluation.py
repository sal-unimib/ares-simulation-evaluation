"""
evaluation.py

Evaluation module for computing metrics over simulation results.

This module provides:
- Constraint Satisfaction Rate (CSR)
- Violation Burst Length (VBL)
- Reconfiguration Effectiveness
- Cost-Quality Trade-off

Each metric is computed for both Baseline and ARES strategies
using ground truth KPI profiles.
"""

import logging
from model import Scenario, Simulation
import os
import pandas as pd
from simulation import feasible, score
from typing import Any, Dict, List, Tuple


# ---------------------------
# Logging configuration
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

logger = logging.getLogger(__name__)


# ---------------------------
# Compliance
# ---------------------------
def compliance(simulation: Simulation) -> Tuple[List[int], List[int], List[int]]:
    """
    Method to compute compliance vectors for ground truth, baseline, and ARES.

    :param simulation: Simulation object
    :type simulation: Simulation
    :return: Tuple of compliance lists (ground truth, baseline, ARES)
    :rtype: Tuple[List[int], List[int], List[int]]
    """
    gt_comp, baseline_comp, ares_comp = [], [], []

    for t, iteration in enumerate(simulation.iterations):
        gt_comp.append(1 if iteration.ground_truth_configuration_feasibility else 0)

        baseline_kpi = simulation.ground_truth_kpi_profiles[iteration.baseline_configuration][t]
        baseline_comp.append(1 if feasible(baseline_kpi) else 0)

        ares_kpi = simulation.ground_truth_kpi_profiles[iteration.ares_configuration][t]
        ares_comp.append(1 if feasible(ares_kpi) else 0)

    return gt_comp, baseline_comp, ares_comp


# ---------------------------
# Constraint Satisfaction Rate
# ---------------------------
def constraint_satisfaction_rate(simulation: Simulation) -> Tuple[float, float, float]:
    """
    Method to compute the Constraint Satisfaction Rate (CSR).

    :param simulation: Simulation object
    :type simulation: Simulation
    :return: CSR values (ground truth, baseline, ARES)
    :rtype: Tuple[float, float, float]
    """
    gt_comp, baseline_comp, ares_comp = compliance(simulation)

    gt_csr = sum(gt_comp) / len(gt_comp)
    baseline_csr = sum(baseline_comp) / len(baseline_comp)
    ares_csr = sum(ares_comp) / len(ares_comp)

    return gt_csr, baseline_csr, ares_csr


# ---------------------------
# Violation Bursts
# ---------------------------
def violation_bursts(comp: List[int]) -> List[Tuple[int, int]]:
    """
    Method to extract violation bursts from a compliance sequence.

    :param comp: Compliance vector (1 = compliant, 0 = violation)
    :type comp: List[int]
    :return: List of (start, end) indices for each burst
    :rtype: List[Tuple[int, int]]
    """
    sequences = []
    start = None

    for i, v in enumerate(comp):
        if v == 0:
            if start is None:
                start = i
        else:
            if start is not None:
                sequences.append((start, i - 1))
                start = None

    if start is not None:
        sequences.append((start, len(comp) - 1))

    return sequences


def violation_burst_length(simulation: Simulation) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Method to compute statistics on violation burst lengths.

    :param simulation: Simulation object
    :type simulation: Simulation
    :return: Tuple of dictionaries (baseline stats, ARES stats)
    :rtype: Tuple[Dict[str, Any], Dict[str, Any]]
    """
    import statistics
    from collections import Counter

    _, baseline_comp, ares_comp = compliance(simulation)

    def compute_stats(bursts: List[Tuple[int, int]]) -> Dict[str, Any]:
        lengths = [end - start + 1 for start, end in bursts]
        if not lengths:
            return {
                "vb": bursts,
                "vb_num": 0,
                "min": 0,
                "max": 0,
                "average": 0.0,
                "median": 0,
                "mode": [],
                "mode_count": 0,
            }

        counter = Counter(lengths)
        modes = statistics.multimode(lengths)

        return {
            "vb": bursts,
            "vb_num": len(lengths),
            "min": min(lengths),
            "max": max(lengths),
            "average": sum(lengths) / len(lengths),
            "median": statistics.median(lengths),
            "mode": modes,
            "mode_count": counter[modes[0]],
        }

    baseline = compute_stats(violation_bursts(baseline_comp))
    ares = compute_stats(violation_bursts(ares_comp))

    return baseline, ares


# ---------------------------
# Effectiveness
# ---------------------------
def effective_reconfiguration_rate(simulation: Simulation) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Method to compute reconfiguration effectiveness.

    Effectiveness measures how often a reconfiguration improves the score.

    :param simulation: Simulation object
    :type simulation: Simulation
    :return: Tuple (baseline stats, ARES stats)
    :rtype: Tuple[Dict[str, float], Dict[str, float]]
    """
    baseline_eff, ares_eff = [], []

    ares_last_config = simulation.iterations[0].ares_configuration

    for t in range(1, len(simulation.iterations)):
        current = simulation.iterations[t]
        previous = simulation.iterations[t - 1]

        # Baseline
        if current.baseline_configuration != previous.baseline_configuration:
            actual_score = score(simulation.ground_truth_kpi_profiles[current.baseline_configuration][t])
            last_score = score(simulation.ground_truth_kpi_profiles[previous.baseline_configuration][t])
            baseline_eff.append(1 if actual_score > last_score else 0)
        else:
            baseline_eff.append(0)

        # ARES
        if current.ares_reconfiguration:
            if current.ares_configuration != ares_last_config:
                actual_score = score(simulation.ground_truth_kpi_profiles[current.ares_configuration][t])
                last_score = score(simulation.ground_truth_kpi_profiles[ares_last_config][t])
                ares_eff.append(1 if actual_score > last_score else 0)
            else:
                ares_eff.append(0)
            ares_last_config = current.ares_configuration

    def build_stats(eff: List[int]) -> Dict[str, float]:
        return {
            "reconfig_num": len(eff),
            "effectiveness_sum": sum(eff),
            "effectiveness": sum(eff) / len(eff) if eff else 0.0
        }

    return build_stats(baseline_eff), build_stats(ares_eff)


# ---------------------------
# Cost-Quality Trade-off
# ---------------------------
def cost_quality_tradeoff(simulation: Simulation) -> Tuple[float, float]:
    """
    Method to compute the cost per compliant execution.

    :param simulation: Simulation object
    :type simulation: Simulation
    :return: Tuple (baseline cost, ARES cost)
    :rtype: Tuple[float, float]
    """
    _, baseline_comp, ares_comp = compliance(simulation)

    baseline_total = sum(baseline_comp)
    ares_total = sum(ares_comp)

    baseline_ops = len(baseline_comp)
    ares_ops = sum(1 for it in simulation.iterations if it.ares_reconfiguration)

    baseline_cost = baseline_ops / baseline_total if baseline_total > 0 else float('inf')
    ares_cost = ares_ops / ares_total if ares_total > 0 else float('inf')

    return baseline_cost, ares_cost


# ---------------------------
# Main execution
# ---------------------------
if __name__ == '__main__':
    logger.info("Starting evaluation pipeline")

    # Load simulations
    simulations = {}
    for scenario in Scenario:
        logger.info(f"Loading simulation for scenario: {scenario.name}")
        simulations[scenario] = Simulation.from_csv(scenario)

    # ---------------------------
    # RQ1 - CSR
    # ---------------------------
    logger.info("Evaluating RQ1 - Constraint Satisfaction Rate")
    os.makedirs('data/evaluation/rq1', exist_ok=True)

    csr_rows = []
    for scenario in Scenario:
        gt, base, ares = constraint_satisfaction_rate(simulations[scenario])
        csr_rows.append({
            "scenario": scenario.name,
            "gt": gt,
            "baseline": base,
            "ares": ares
        })

    pd.DataFrame(csr_rows).to_csv('data/evaluation/rq1/csr.csv', index=False)
    logger.info("CSR results saved")

    # ---------------------------
    # RQ1 - VBL
    # ---------------------------
    logger.info("Evaluating RQ1 - Violation Burst Length")

    for scenario in [Scenario.degradation, Scenario.dynamic]:
        base, ares = violation_burst_length(simulations[scenario])
        pd.DataFrame([base, ares]).to_csv(
            f'data/evaluation/rq1/vbl_{scenario.name}.csv', index=False
        )

    logger.info("VBL results saved")

    # ---------------------------
    # RQ2 - Effectiveness
    # ---------------------------
    logger.info("Evaluating RQ2 - Effectiveness")
    os.makedirs('data/evaluation/rq2', exist_ok=True)

    for scenario in [Scenario.degradation, Scenario.dynamic]:
        base, ares = effective_reconfiguration_rate(simulations[scenario])
        pd.DataFrame([base, ares]).to_csv(
            f'data/evaluation/rq2/effectiveness_{scenario.name}.csv', index=False
        )

    logger.info("Effectiveness results saved")

    # ---------------------------
    # RQ3 - Cost
    # ---------------------------
    logger.info("Evaluating RQ3 - Cost-Quality Trade-off")
    os.makedirs('data/evaluation/rq3', exist_ok=True)

    cost_rows = []
    for scenario in [Scenario.degradation, Scenario.dynamic]:
        base_cost, ares_cost = cost_quality_tradeoff(simulations[scenario])
        cost_rows.append({
            "scenario": scenario.name,
            "baseline": base_cost,
            "ares": ares_cost
        })

    pd.DataFrame(cost_rows).to_csv('data/evaluation/rq3/cost.csv', index=False)
    logger.info("Cost results saved")

    logger.info("Evaluation completed successfully")