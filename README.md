# GEDI-Pipeline

This repository provides a unified workflow of acquiring data from the Global Ecosystem Dynamics Investigation (GEDI) mission at a footprint level.

<img src="https://github.com/leonelluiscorado/GEDI-Pipeline/blob/main/pipeline/docs/img/gedi-pipeline.png" alt="GEDI Pipeline" width="600"/>


- **Finder** searches for all the orbits passing over a ROI and specified timestamp and outputs its download link from LPDAAC
- **Downloader** downloads the entire granule from the link provided by the Finder
- **Subsetter** clips to the study area and selects all the available Science Dataset (SDS) data product variables to burn for each footprint


Usually the user finds and downloads GEDI data products via a graphical user interface (GUI) using NASA [EarthData Search](https://search.earthdata.nasa.gov) or programmatically using NASA's Common Metadata Repository ([CMR](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html)), and then subsets to a desired study area, using separate programs/scripts. This pipeline automates such task by finding, downloading and subsetting all the granules provided by the Finder using NASA's CMR.

Subsetting the granule _before_ downloading is [currently unavailable](https://forum.earthdata.nasa.gov/viewtopic.php?t=2775) through the APIs provided.

## Installation

**Requirements**:
-  The user must have a registered [EarthData](https://www.earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/earthdata-login) account before accessing any of these datasets.
-  Python (version >)

## Executing the Pipeline

## Available GEDI Products

## Contributing to this project

## References