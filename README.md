# BEPVis Tool Documentation

[![DOI](https://zenodo.org/badge/867164554.svg)](https://doi.org/10.5281/zenodo.17883831)

Welcome to the **BEPVis** — Building Energy Performance Visualization Toolkit

**BEPVis** is a modular post-processing and visualization framework designed to extract, organize, and visually explore results from **EnergyPlus** simulations. It automates all data preparation steps and generates high-quality interactive visualizations for energy analysis, comfort assessment, and thermal balance interpretation.

The system is structured around a central Manager (BEPVis_Manager.py) that reads EnergyPlus outputs (SQLite + epJSON), generates standardized datasets, and orchestrates multiple visualization modules (Bokeh and Plotly).

🔥 Quick Start Guide

Follow these steps to run BEPVis in a few minutes.

1. Install Dependencies

BEPVis uses Python 3.9+.

Install all required packages:

pip install -r requirements.txt


Or install manually:

pip install pandas bokeh plotly colorcet numpy scipy openpyxl

2. Prepare EnergyPlus Output Folder

Place your simulation outputs in a folder with at least:

ExampleProject/
    eplusout.sql
    in.epJSON


Optional files (if available) will also be parsed automatically.

3. Run the BEPVis Manager

Run the main processing engine:

python BEPVis_Manager.py --input ExampleProject/


Alternatively, if the path is hard-coded in your workflow:

python BEPVis_Manager.py

4. Inspect the Outputs

The Manager will automatically create:

ExampleProject/VisualizationOutput/
    GainsAndLosses.html
    PMV_Linechart.html
    PPD_Linechart.html
    Heatmap.html
    ScatterHeatingCooling.html
    Radar.html

    (and corresponding Excel datasets)


All HTML files are fully interactive and can be opened in any web browser.

⚙️ BEPVis Manager — Post-Processing and Visualization Orchestrator

BEPVis_Manager.py is the core of the entire pipeline.
It performs:

- loading of EnergyPlus outputs (SQLite + epJSON)

- optimized queries to the EnergyPlus SQL database

- extraction and organization of key variables

- monthly/hourly aggregation

- generation of standardized intermediate datasets

- execution of all visualization modules

- logging (console + optional file logs)

- support for batch processing of multiple simulations

⭐ Main Features

EnergyPlus Data Extraction

✔ Heating/cooling rates
✔ Indoor temperature + RH
✔ PMV/PPD comfort indices
✔ Internal gains
✔ HVAC performance
✔ Zone energy balances
✔ Environmental monitoring variables (optional)

Data Processing

✔ Timestamp normalization
✔ Hourly & monthly aggregation
✔ Computation of derived indicators
✔ Consistent metric conversion
✔ Automatic normalization per floor area (kWh/m²)

Intermediate Dataset Generation

✔ Clean, structured Excel files
✔ One dataset per visualization
✔ 100% automatic—no user editing required

Visualization Orchestration

✔ Automatic execution of all charts
✔ Output as interactive HTML
✔ Bokeh + Plotly integration
✔ Clear, informative layout

📊 How BEPVis Handles Data
BEPVis implements a fully automated workflow that transforms raw simulation data into interactive visualizations without user intervention.

Workflow Diagram

flowchart LR

A[EnergyPlus Output Files<br>(SQLite, CSV, epJSON)] --> B[BEPVis Manager<br>(Data Processing Engine)]
B --> C[Auto-generated Excel Files<br>(Structured Inputs)]
C --> D[Visualization Modules<br>(Bokeh / Plotly)]
D --> E[Interactive HTML Reports]

🧠 1. Manager: Automated Data Processing Engine

The Manager (BEPVis_Manager.py)performs all data preparation steps:

✔ Parsing raw EnergyPlus outputs

- Temperature, RH

- Heating/cooling demand

- Occupancy

- PMV/PPD

- Envelope loads and internal gains

✔ Cleaning and transforming results

- reorganizing multivariate zone data

- filtering, grouping, aggregating

- hourly and monthly summaries

✔ Creating visualization-ready Excel files

These files are not user-provided.
They are generated automatically for internal use.

📁 2. Auto-Generated Excel Files (by Visualization Type)

Below is the list of files created by the Manager:

🔹 Heatmap Module (Heatmap.py)

File: Heatmap_Data.xlsx
Columns:
| Month | Zone | Value |

🔹 Gains & Losses (GainsAndLosses.py)

File: GainsAndLosses.xlsx
Columns:
| Space | Solar Gains | Internal Gains | Envelope Losses | ... |

🔹 Comfort Line Charts (Linechart.py)

Files:
- PMV Data.xlsx
- PPD Data.xlsx
Columns:
| Month | Zone1 | Zone1min | Zone1max | Zone2 | ... |

🔹 Radar Charts (Radar.py)

File: Radar_Energy.xlsx
Columns
| Zone | Category1 | Category2 | Category3 | ... |

🔹 Scatter Plot Module (Scatter.py)

File: Scatter_ILAS.xlsx
Required columns:

- Outdoor_Temperature
- Zone_ILAS_HeatingRate
- Zone_ILAS_CoolingRate
- Date/Time

🎨 3. Visualization Modules

Each module reads its corresponding dataset and produces an interactive HTML file.
Modules do not:

- clean data
- compute indicators
- modify data structures

Their responsibility is purely visual:

- Bokeh (Gains & Losses, Heatmap, Linecharts, Scatter)
- Plotly (Radar)

📤 4. Interactive HTML Output

All outputs are:

- fully interactive
- browser-friendly
- publication-ready
- suitable for dashboards
- reproducible and traceable

📜 License

MIT License

🙌 Contributions

Contributions, issues, and feature requests are welcome via GitHub Issues and Pull Requests.
