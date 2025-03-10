from pipeline.pipeline import GEDIPipeline
from utils.service_status import get_service_status

import argparse

# --------------------------COMMAND LINE ARGUMENTS AND ERROR HANDLING---------------------------- #
# Set up argument and error handling
parser = argparse.ArgumentParser(description='This pipeline performs all of the tasks (Finding, Downloading, Subsetting) to get GEDI Data.')

parser.add_argument('--dir', required=True, help='Local directory to save GEDI files to be processed / Save the subsetted granules.')

parser.add_argument('--product', required=True, help='GEDI Product to specify for the search query and subsetting module \
                    Select from "GEDI01_B"; "GEDI02_A"; "GEDI02_B"; "GEDI04_A"')

parser.add_argument('--version', required=True, help='GEDI Product version to specify for the search query and subsetting module \
                    Select from "001"; "002"')

parser.add_argument('--start', required=True, help='Start date for time period of interest: valid format is yyyy.mm.dd (e.g. 2020.11.12).')

parser.add_argument('--end', required=True, help='Start date for time period of interest: valid format is yyyy.mm.dd (e.g. 2021.07.01).')

parser.add_argument('--recurring_months', required=False, help='Include this option to GEDIPipeline only search the included months across all years provided.',
                    action='store_true')

parser.add_argument('--roi', required=True, help='Region of interest (ROI) to subset the GEDI orbit to in the output file. \
                    Valid inputs are bounding box coordinates: ul_lat,ul_lon,lr_lat,lr_lon')

parser.add_argument('--beams', required=False, help='Specific beams to be included in the output file (default is all beams) \
                    BEAM0000,BEAM0001,BEAM0010,BEAM0011 are Coverage Beams. BEAM0101,BEAM0110,BEAM1000,BEAM1011 are Full Power Beams.', default=None)

parser.add_argument('--sds', required=False, help='Specific science datasets (SDS) to include in the output subsetted file. \
                    (see README for a list of available SDS and a list of default SDS returned for each product).', default=None)

parser.add_argument('--login_keep', required=False, help='Include this option to keep EarthData login saved to this machine. It defaults saving to \
                    the .netrc file', action='store_true')

args = parser.parse_args()

# ------------------------------------------------------------------------------------#

nots = get_service_status(args.product)

pipeline = GEDIPipeline(
    out_directory = args.dir,
    product = args.product,
    version = args.version,
    date_start = args.start,
    date_end = args.end,
    recurring_months=args.recurring_months,
    roi = args.roi,
    beams = args.beams,
    sds = args.sds,
    persist_login = args.login_keep
)

print("[Pipeline] Pipeline set, starting ...")

try:
    granules = pipeline.run_pipeline()
except Exception as e:
    print("[Pipeline] Failed to complete running the Pipeline. See the error below for more information.")
    print(e)
    exit(0)

print(f"[Pipeline] Pipeline Run Complete! Subsetted {len(granules)} files saved to: {args.dir}")

