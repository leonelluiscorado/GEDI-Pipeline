# GEDI-Pipeline

This repository provides a unified workflow of acquiring data from the Global Ecosystem Dynamics Investigation (GEDI) mission at a footprint level.

<img src="https://github.com/leonelluiscorado/GEDI-Pipeline/blob/main/pipeline/docs/img/gedi-pipeline.png" alt="GEDI Pipeline" width="600"/>


- **Finder** searches for all the orbits passing over a ROI and specified timestamp and outputs its download link from LPDAAC
- **Downloader** downloads the entire granule from the link provided by the Finder
- **Subsetter** clips to the study area and selects all the available Science Dataset (SDS) data product variables to burn for each footprint

Usually the user finds and downloads GEDI data products via a graphical user interface (GUI) using NASA [EarthData Search](https://search.earthdata.nasa.gov) or programmatically using NASA's Common Metadata Repository ([CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)), and then subsets to a desired study area, using separate programs/scripts. This pipeline automates such task by finding, downloading and subsetting all the granules provided by the Finder using NASA's CMR.

Subsetting the granule _before_ downloading is [currently unavailable](https://forum.earthdata.nasa.gov/viewtopic.php?t=2775) through the APIs provided. After the granule is subsetted, the original downloaded file ".h5" is always deleted.

## Installation

### Requirements
-  The user must have a registered [EarthData](https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/earthdata-login) account before accessing any of these datasets.
-  Python (>=3.12)

You can set up the virtual environment to run this project in two ways:
1. Python's venv and pip
2. Anaconda / Mamba Environment

### Virtual Environment

1. Create a new [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) with a name and path of your choice by running `python3 -m venv <PATH-TO-ENV>/<NAME>`
2. Activate the newly created environment by `source <PATH-TO-ENV>/bin/activate` (Check that python points to the new environment with `which python3` or `which pip` after activating, it should print something like: `..<PATH-TO-ENV>/<NAME>/bin/python`)
3. Install all the required packages for the pipeline to work with `python3 -m pip install -r requirements.txt`

### Usage with Anaconda / Mamba

You may create a Conda/Mamba environment specifically for this project, requiring a few extra steps than creating a venv.
1. Install [Anaconda](https://docs.anaconda.com/free/anaconda/install/) or [Mambaforge](https://github.com/conda-forge/miniforge#mambaforge) (If installing on Windows, check the `Add to PATH environment variable` to work on a command-line interface).
2. Create a new conda environment with pip installed by `conda create --name <NAME> python=3.12 pip` (or switch `conda` with `mamba` if Mambaforge is installed).
3. Activate the newly created environment with `conda activate <NAME>` or `mamba activate <NAME>` and check if python points to the activated environment path with `which python3`
4. Update the existing environment with `environment.yml` provided in the repository with `conda env update --file environment.yml`. Be patient, it should take a while.

## Executing the Pipeline script

You can execute the pipeline script by running `python3 gedi_pipeline.py`. Additional commands must be provided for the pipeline to work, such as GEDI product, version, start date and end date query and the output directory. You can run `python3 gedi_pipeline.py --help` for more information.

## Available GEDI Products

- GEDI L1B Geolocated Waveform Data Global Footprint Level - GEDI01_B
- GEDI L2A Elevation and Height Metrics Data Global Footprint Level - GEDI02_A
- GEDI L2B Canopy Cover and Vertical Profile Metrics Data Global Footprint Level - GEDI02_B
- GEDI L4A Footprint Level Aboveground Biomass Density - GEDI04_A

For each GEDI data product, you can specify which version you want to download: version '001' or version '002'.

## Contributing to this project

This project is in its early stages so any contributions are welcome with a well documented/explained issue and implementation!

## References

The GEDI Pipeline is inspired by other two repositories:
- NASA's GEDI Data Resources: https://github.com/nasa/GEDI-Data-Resources
- pyGEDI: https://github.com/EduinHSERNA/pyGEDI
- Also from this specific answer to a forum post: https://forum.earthdata.nasa.gov/viewtopic.php?t=591