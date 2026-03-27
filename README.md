# ARES Framework Simulation and Evaluation

This repository contains the experimental framework used to evaluate the **ARES adaptive reconfiguration strategy** against a baseline approach under different runtime conditions.

The framework is designed to simulate, execute, and evaluate dynamic data source selection based on QoS (Quality of Service) KPIs.

---

## 📁 Repository Structure

```
.
├── data_generation.py   # KPI generation (ground truth + estimated)
├── simulation.py        # Simulation of baseline and ARES strategies
├── evaluation.py        # Metrics computation (RQ1, RQ2, RQ3)
├── model.py             # Data structures and simulation model
└── data/
    ├── stable/
    ├── degradation/
    ├── dynamic/
    └── evaluation/
```

---

## ⚙️ Overview

The framework is organized into three main phases:

1. **Data Generation**
2. **Simulation Execution**
3. **Evaluation**

Each phase corresponds to a Python script.

---

## 🚀 Usage

### 1. Generate KPI Data

```bash
python data_generation.py
```

This step generates:

* Ground truth KPI profiles
* estimated KPI profiles (with noise)

Output:

```
data/<scenario>/<datasource>_ground_truth.csv
data/<scenario>/<datasource>_estimated.csv
```

---

### 2. Run Simulation

```bash
python simulation.py
```

This step:

* Simulates data source selection
* Compares **Baseline** vs **ARES**
* Stores per-iteration results

Output:

```
data/<scenario>/simulation.csv
```

---

### 3. Evaluate Results

```bash
python evaluation.py
```

This step computes the experimental metrics:

* **RQ1 – Constraint Satisfaction**
* **RQ2 – Reconfiguration Effectiveness**
* **RQ3 – Cost-Quality Trade-off**

Output:

```
data/evaluation/
├── rq1/
├── rq2/
└── rq3/
```

---

## 📊 Scenarios

The experiments are conducted under three scenarios:

* **Stable**: No significant changes in KPIs
* **Degradation**: Gradual performance degradation
* **Dynamic**: Frequent and unpredictable changes

---

## 🧩 Data Sources

The system evaluates multiple data sources:

* Smart Scale
* Cloud Service
* Manual Input

Each source is characterized by:

* Reliability
* Latency
* Availability

---

## 📈 Metrics

The following metrics are computed:

### RQ1 – Constraint Satisfaction Rate (CSR)

Percentage of time the selected configuration satisfies constraints.

### RQ1 – Violation Burst Length (VBL)

Analysis of consecutive constraint violations.

### RQ2 – Adaptation Latency

Measures how quickly the system reacts to inadequacy events.

### RQ2 – Reconfiguration Effectiveness

Measures whether reconfigurations improve system performance.

### RQ3 – Cost-Quality Trade-off

Evaluates the cost per compliant execution.

---

## 🔁 Reproducibility

To reproduce the results:

```bash
python data_generation.py
python simulation.py
python evaluation.py
```

All outputs will be stored in the `data/` directory.

---

## 🧪 Configuration

Key simulation parameters are defined in `model.py`:

* `TOTAL_TIME_SIMULATION`
* `ARES_RECONFIG_FREQUENCY`

---

## 📌 Notes

* The framework is deterministic unless randomness is introduced in KPI generation.
* All results are exported in CSV format for easy analysis.

