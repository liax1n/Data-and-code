# Hydrological Responses of Groundwater-Dependent Ecosystems to Human Activities in the Mu Us Sandy Land(Data-and-code)

## Overview

This repository contains the model inputs, analysis scripts, and selected outputs associated with the study **“Hydrological Responses of Groundwater-Dependent Ecosystems to Human Activities in the Mu Us Sandy Land”**. The study investigates groundwater and related ecohydrological responses to vegetation restoration, agricultural irrigation, and coal mining in the Mu Us Sandy Land, northern China.

The analysis combines a 1 km ParFlow-CLM model with eight factorial scenarios to quantify individual effects and nonlinear interactions among the three human activities. The repository is organized into model inputs, scenario-specific processing scripts, and selected simulation outputs.

## Study area

The model domain covers the Mu Us Sandy Land between 37.4–39.4° N and 107.3–110.6° E, with a horizontal resolution of 0.01° (approximately 1 km). The ParFlow-CLM domain contains 330 × 200 horizontal grid cells and 10 vertical layers.

## Repository structure

```text
Data-and-code/
├── 1\\\_inputs\\\_data/
│   ├── clm\\\_input/       # CLM vegetation and parameter input files
│   └── pfb\\\_files/       # ParFlow spatial parameter fields
├── 2\\\_codes/
│   ├── S1/              # Scenario-specific processing scripts
│   ├── S2/
│   ├── S3/
│   ├── S4/
│   ├── S5/
│   ├── S6/
│   ├── S7/
│   └── S8/
├── 3\\\_outputs/
│   ├── 1\\\_WTD\\\_daily/                     # Daily water table depth
│   ├── 2\\\_streamflow/                     # Streamflow results at six stations
│   ├── 3\\\_ET/                             # Daily evapotranspiration
│   ├── 4\\\_1\\\_gradient\\\_darcy/               # Upward hydraulic gradient proxy
│   ├── 4\\\_2\\\_rootzone\\\_water\\\_availability/  # Root-zone water availability
│   ├── 4\\\_3\\\_veg\\\_trans\\\_mmday/              # Vegetation transpiration
│   ├── 4\\\_4\\\_sh/                           # Sensible heat flux
│   └── 4\\\_5\\\_lh/                           # Latent heat flux
├── .gitattributes
└── README.md
```

## Main file formats

|Format|Description|
|-|-|
|`.py`|Python processing and analysis scripts|
|`.tcl`|Tcl scripts used for ParFlow/PFTools processing|
|`.sh`|Shell scripts intended for Linux/HPC execution|
|`.pfb`|ParFlow binary files|
|`.sa`|ParFlow simple ASCII files|
|`.dat`|CLM input and parameter files|
|`.npy`|NumPy arrays containing gridded daily or annual results|
|`.csv`|Spatial summaries, station results, and regional statistics|
|`.png`|Diagnostic and result figures|

## Software requirements

The main software used in the workflow includes:

* ParFlow **v3.13.0** with the integrated CLM land-surface module
* Python **3.12.4**
* NumPy **1.26.4**
* pandas **2.2.2**
* Matplotlib **3.8.4**
* Tcl/Tk and ParFlow PFTools

## Data notes

* Gridded outputs generally follow the 200-row × 330-column model layout.
* Daily output arrays include a time dimension in addition to the two spatial dimensions.
* Water table depth is expressed in metres unless stated otherwise.
* Daily evapotranspiration and transpiration outputs are expressed in millimetres per day unless stated otherwise.

## Reproducibility notes

The scripts may contain paths that are specific to the original Windows workstation or Linux/HPC environment. Users should update these paths before running the workflow. Shell (`.sh`) and Tcl (`.tcl`) files should retain LF line endings for execution under Linux.

## Authors and contact

Jiaxin Lei, Beijing Normal University

Email: jiaxinlei@mail.bnu.edu.cn

## License

Code: MIT License

Author-generated outputs: CC BY 4.0

