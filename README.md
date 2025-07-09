# GEDI-Pipeline

<img src="https://github.com/leonelluiscorado/GEDI-Pipeline/blob/main/pipeline/docs/img/GEDIPipeline-logo.png" alt="GEDI Pipeline-logo"/>

**This repository provides a unified workflow of acquiring data from the Global Ecosystem Dynamics Investigation (GEDI) mission at a footprint level.**

<img src="https://github.com/leonelluiscorado/GEDI-Pipeline/blob/main/pipeline/docs/img/gedi-pipeline2.png" alt="GEDI Pipeline"/>

- **Finder** searches for all the orbits passing over a Region Of Interest (ROI) at the specified timestamp and outputs its download link from LPDAAC / ORNLDAAC
- **Downloader** downloads the entire granule from the link provided by the Finder, provided with authentication for EarthData
- **Subsetter** clips to the study area and selects all the available Science Dataset (SDS) data product variables to burn for each footprint, and outputs the subsetted orbit

**Pipeline** automates the previous modules into a single class / script.

## Overview

<img src="https://github.com/leonelluiscorado/GEDI-Pipeline/blob/main/pipeline/docs/img/footprintoverview.png" alt="Subset-Orbit"/>

1. The Finder searches NASA's data repository for all the available orbits that pass over the ROI (Rectangle) and a list of URLs is returned, containing the download links for the granules (**A.**).
2. The Downloader downloads each (entire) granule to a specified directory, as subsetting the granule _before_ downloading is [currently unavailable](https://forum.earthdata.nasa.gov/viewtopic.php?t=2775) through the APIs provided.
3. After downloading, the subsetter first clips the footprints and the specified BEAMS that the ROI contains and then selects the specified SDS variables for each footprint, saving to a .gpkg file. This process is repeated every time a granule is downloaded. After subsetting, the original granule is deleted, as to save space.
4. After pipeline completion, the user is left with all the clipped orbits displayed by the Finder to the specified ROI (**B.**), saved as .gpkg files.
5. The user can manipulate, analyze and use each footprint as desired. The table displays the variables burnt into a single footprint (in this example, the data product is GEDI L2A Version 2) (**C.**).

Depending on the number of granules and the number of variables to subset, processing time may **vary**, so be patient.

### Why we built this framework

Usually the user finds and downloads GEDI data products via a graphical user interface (GUI) using NASA [EarthData Search](https://search.earthdata.nasa.gov) or programmatically using NASA's Common Metadata Repository ([CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)), and then subsets to a desired study area, using **separate** programs/scripts.

This pipeline automates such task by finding, downloading and subsetting all the granules provided by the Finder using NASA's CMR. There are repositories that automate the Finder and Subsetter modules, but need to be executed separately and with different program arguments. We believe that merging all of these separate frameworks eases some burden into launching different scripts, managing the data and processing, streamlining the workflow for Remote Sensing, Data Analysis and Data Science 
researchers, which enables a much more efficient analysis of GEDI data.

## Installation

### Requirements
-  The user must have a registered [EarthData](https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/earthdata-login) account before accessing any of these datasets.
-  Python (>=3.12)

You can set up the virtual environment to run this project in two ways:
1. Python's venv and pip
2. Anaconda / Mamba Environment

### Virtual Environment

1. Create a new [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/) with name `gedi-pipeline` by running `python3 -m venv ~/venvs/gedi-pipeline`
2. Activate the newly created environment by `source ~/venvs/gedi-pipeline/bin/activate` (Check that python points to the new environment with `which python3` or `which pip` after activating, it should print something like: `../venvs/gedi-pipeline/bin/python`)
3. Install all the required packages for the pipeline to work with `python3 -m pip install -r requirements.txt`

### Usage with Anaconda / Mamba

You may create a Conda/Mamba environment specifically for this project, requiring a few extra steps than creating a venv.
1. Install [Anaconda](https://docs.anaconda.com/free/anaconda/install/) or [Mambaforge](https://github.com/conda-forge/miniforge#mambaforge) (If installing on Windows, check the `Add to PATH environment variable` to work on a command-line interface).
2. Create a new conda environment called `gedi-pipeline` with pip installed by running `conda create --name gedi-pipeline python=3.12 pip` (or switch `conda` with `mamba` if Mambaforge is installed).
3. Activate the newly created environment with `conda activate gedi-pipeline` or `mamba activate gedi-pipeline` and check if python points to the activated environment path with `which python3`
4. Update the existing environment with `environment.yml` provided in the repository with `conda env update -f environment.yml`. Be patient, it should take a while.

## Executing the Pipeline script

You can execute the pipeline script by running `python3 gedi_pipeline.py`. Additional commands must be provided for the pipeline to work, such as GEDI product, version, start date and end date query and the output directory. You can run `python3 gedi_pipeline.py --help` for more information.

## Available GEDI Products

- GEDI L1B Geolocated Waveform Data Global Footprint Level - [GEDI01_B](https://lpdaac.usgs.gov/products/gedi01_bv001/)
- GEDI L2A Elevation and Height Metrics Data Global Footprint Level - [GEDI02_A](https://lpdaac.usgs.gov/products/gedi02_av002/)
- GEDI L2B Canopy Cover and Vertical Profile Metrics Data Global Footprint Level - [GEDI02_B](https://lpdaac.usgs.gov/products/gedi02_bv002/)
- GEDI L4A Footprint Level Aboveground Biomass Density - [GEDI04_A](https://daac.ornl.gov/GEDI/guides/GEDI_L4A_AGB_Density_V2_1.html)

For each GEDI data product, you can specify which version you want to download: version '001' or version '002'.

## Contributing to this project

This project is in its early stages so any contributions are welcome with a well documented/explained issue and implementation!

## Acknowledgements

We would like to thank the University of Maryland and NASA's Goddard Space Flight Center for their relentless work on the GEDI mission.

The GEDI Pipeline is (very) inspired by other repositories, which we would like to thank for their contributions for the GEDI Project:
- NASA's GEDI Data Resources: https://github.com/nasa/GEDI-Data-Resources
- pyGEDI: https://github.com/EduinHSERNA/pyGEDI
- Also from this specific answer to a forum post: https://forum.earthdata.nasa.gov/viewtopic.php?t=591
- rGEDI: https://github.com/carlos-alberto-silva/rGEDI

### Funding

This work was conducted within the framework of the GEDI4SMOS project (Combining LiDAR, radar, and multispectral data to characterize the three-dimensional structure of vegetation and produce land cover maps), financially supported by the Directorate-General for Territory (DGT) with funds from the Recovery and Resilience Plan (Investimento RE-C08-i02: Cadastro da Propriedade Rústica e Sistema de Monitorização da Ocupação do Solo).

## References

Dubayah, R., Blair, J.B., Goetz, S., Fatoyinbo, L., Hansen, M., Healey, S., Hofton, M., Hurtt, G., Kellner, J., Luthcke, S., & Armston, J. (2020) The Global Ecosystem Dynamics Investigation: High-resolution laser ranging of the Earth’s forests and topography. Science of Remote Sensing, p.100002. https://doi.org/10.1016/j.srs.2020.100002

Hancock, S., Armston, J., Hofton, M., Sun, X., Tang, H., Duncanson, L.I., Kellner, J.R. and Dubayah, R., 2019. The GEDI simulator: A large-footprint waveform lidar simulator for calibration and validation of spaceborne missions. Earth and Space Science. https://doi.org/10.1029/2018EA000506

Silva,C.A; Hamamura,C.; Valbuena, R.; Hancock,S.; Cardil,A.; Broadbent, E. N.; Almeida,D.R.A.; Silva Junior, C.H.L; Klauberg, C. rGEDI: NASA's Global Ecosystem Dynamics Investigation (GEDI) Data Visualization and Processing. version 0.1.10, accessed on February. 23, 2024, available at: https://CRAN.R-project.org/package=rGEDI

## Citing this Project

Corado, L., Godinho, S., 2024. GEDI-Pipeline. Version 0.1.0, accessed on 12-11-2024, available at: https://github.com/leonelluiscorado/GEDI-Pipeline
