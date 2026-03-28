# ARES Framework Simulation and Evaluation

This repository contains the experimental framework used to evaluate the **ARES adaptive reconfiguration strategy** against a baseline approach under different runtime conditions.

The framework is designed to simulate, execute, and evaluate dynamic data source selection based on QoS (Quality of Service) KPIs.

---

## 📁 Repository Structure

```
.
├── data_generation.py         # KPI generation (ground truth + estimated)
├── data_visualization.ipynb   # Notebook for reproducing plots from the paper
├── evaluation.py              # Metrics computation (RQ1, RQ2, RQ3)
├── model.py                   # Data structures and simulation model
├── simulation.py              # Simulation of baseline and ARES strategies
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

An additional Jupyter notebook is provided to reproduce the plots presented in the paper.

---

## 🚀 Setup

Create and activate a virtual environment, then install dependencies:

### Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## ▶️ Usage

### 1. Generate KPI Data

```bash
python data_generation.py
```

This step generates:

* Ground truth KPI profiles
* Estimated KPI profiles (with noise)

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
* **RQ1 – Violation Burst Length**
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

### 4. Reproduce Paper Plots

```bash
jupyter notebook data_visualization.ipynb
```

The notebook reproduces the plots presented in the paper using the generated evaluation data.

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

### RQ2 – Reconfiguration Effectiveness

Measures whether reconfigurations improve system performance.

### RQ3 – Cost-Quality Trade-off

Evaluates the cost per compliant execution.

---

## 🔁 Reproducibility

To fully reproduce the experimental results:

```bash
python data_generation.py
python simulation.py
python evaluation.py
```

Then run:

```bash
jupyter notebook data_visualization.ipynb
```

All outputs are stored in the `data/` directory.

---

## 🧪 Configuration

Key simulation parameters are defined in `model.py`:

* `TOTAL_TIME_SIMULATION`
* `ARES_RECONFIG_FREQUENCY`

---

## 📌 Notes

* The framework is deterministic unless randomness is introduced in KPI generation.
* All results are exported in CSV format for easy post-processing.
