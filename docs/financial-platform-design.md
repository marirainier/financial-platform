# Microsoft Fabric E2E Medallion & Lambda Architecture Project Plan

## 1. Executive Summary & Intent
This project establishes a **Code-First, Git-Integrated Microsoft Fabric Modern Data Platform** designed to process financial transactions and generate real-time and batch **Revenue Projections**. It implements a dual-path architecture (**Hot Path** for real-time telemetry streaming and alerts, and **Cold Path** for batch medallion transformations and executive reporting).

---

## 2. Goals, Non-Goals & Anti-Goals

### Goals
- **Dual-Path Lambda Architecture**: Hot path using Eventstream + Kusto DB (Eventhouse) + Real-Time Dashboards + Activator; Cold path using Lakehouse Files -> Silver Lakehouse -> Gold Warehouse -> Direct Lake Semantic Model -> Power BI.
- **Code-First & Git Integration**: All Fabric items (Notebooks, Data Pipelines, Semantic Models, Reports) maintained as code (PySpark, TMDL, PBIR) and synced with a Git repository (GitHub/Azure DevOps).
- **Automated CI/CD**: GitHub Actions pipeline for linting, PySpark unit tests, schema validation, and deployment automation using Fabric Deployment Pipelines and Variable Libraries.
- **Financial Revenue Projections**: Sample financial dataset simulating streaming invoices, payments, and batch ledger updates to calculate dynamic revenue forecasts.

### Non-Goals
- Multi-cloud data ingestion (AWS/GCP) in Phase 1.
- Custom machine learning model training pipelines (focus is on analytics, Spark transforms, SQL, and Direct Lake).

### Anti-Goals
- Manual workspace modifications in the Fabric portal without Git tracking.
- Monolithic unversioned SQL scripts.

---

## 3. Architecture Overview (Hot Path + Cold Path)

### Hot Path (Real-time Streaming)
1. **Fabric Events / Eventstream**: Ingests real-time financial transaction events.
2. **Bronze Kusto DB**: Raw event ingestion table.
3. **Silver Kusto DB**: Parsed and filtered clean event streams via Kusto update policies.
4. **Gold Kusto DB**: Materialized views aggregating live revenue metrics per minute/region.
5. **Real-Time Dashboard**: KQL Dashboard visualizing real-time revenue velocity.
6. **Activator**: Reflex rules triggering automated alerts (Teams/Email) on revenue anomalies or threshold breaches.

### Cold Path (Batch Medallion Architecture)
1. **Bronze Lakehouse (Files / Delta)**: Landing zone for raw batch financial CSV/Parquet files.
2. **Silver Lakehouse (Delta tables)**: Cleaned, conformed, and schema-enforced PySpark transformations.
3. **Gold Data Warehouse (Star Schema)**: Dimension and Fact tables (`Dim_Customer`, `Dim_Date`, `Fact_Revenue`) via T-SQL / Stored Procedures.
4. **Semantic Model (Direct Lake / TMDL)**: Direct Lake connection over Gold DW tables with DAX revenue measures.
5. **Power BI Report (PBIR)**: Executive dashboard for financial projections and trend analysis.

---

## 4. Repository Structure (Code-First Git Layout)

```
fabric-financial-revenue-platform/
├── .github/
│   └── workflows/
│       ├── ci.yml                 # Linting, pytest, and static validation
│       └── deploy.yml             # Automated deployment & git sync
├── config/
│   ├── contracts/                 # Table layout and data quality contracts
│   └── variable_library.json      # Environment-specific variables (Dev/Test/Prod)
├── data/
│   └── sample/                    # Sample financial datasets (CSV/Parquet)
├── docs/                          # Architecture diagrams, specifications, runbooks
├── fabric/                        # Fabric Workspace Items (Workspace-as-Code)
│   ├── notebooks/                 # PySpark Notebooks (.ipynb / .py)
│   │   ├── 01_landing_to_bronze.py
│   │   ├── 02_bronze_to_silver.py
│   │   └── 03_silver_to_gold.py
│   ├── pipelines/                 # Data Pipelines (.DataPipeline)
│   │   └── pl_end_to_end_orchestrate.json
│   ├── semantic_models/           # TMDL definitions for Direct Lake
│   └── reports/                   # PBIR report layouts
├── sql/                           # T-SQL scripts & stored procedures for Gold Warehouse
│   ├── ddl/
│   └── stored_procs/
├── src/                           # Python transformation functions
│   └── financial_transforms/
├── tests/                         # Unit tests (pytest) & contract tests
│   ├── test_transforms.py
│   └── validate_contracts.py
├── .gitignore
├── README.md
├── pyproject.toml
└── requirements.txt
```

---

## 5. CI/CD & Deployment Pipeline Strategy

- **Version Control**: GitHub repository serving as the single source of truth.
- **Branch Strategy**: Feature branches -> PR into `main` -> Automated CI validation -> Deployment pipeline promotion.
- **CI Checks (`ci.yml`)**:
  - Python linting (`flake8` / `black`)
  - PySpark unit testing (`pytest` on local Spark runtime)
  - Schema contract validation (`validate_fabric_items.py`)
- **Deployment**: Fabric Git integration synchronizes the `fabric/` folder to the Development workspace. Deployment pipelines promote Dev -> Test -> Prod using Variable Libraries (`vl_financial_settings`) for connection strings and workspace parameters.
