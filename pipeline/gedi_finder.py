import os
import requests as r
from datetime import datetime

class GEDIFinder:

    def __init__(self, product='GEDI02_A', version='002', date_start='', date_end='', roi=None):

        self.product = product
        self.version = version

        # Date format must be in "Year.month.day"
        try:
            self.date_start = datetime.strptime(date_start, "%Y.%m.%d")
            self.date_end = datetime.strptime(date_end, "%Y.%m.%d")
        except:
            print("Dates provided not valid. Valid format is \"Y.m.d\" (e.g. 2019.01.01).")

        if roi is not None:
            # GEDIFinder expects bbox to be (LL_lon, LL_lat, UR_lon, UR_lat)
            [ul_lat, ul_lon, lr_lat, lr_lon] = roi
            self.roi = " ".join(map(str, [ul_lon, lr_lat, lr_lon, ul_lat]))


    def _find_all_granules(self):
        """
        Requests all the links and download sizes for each granule found over the ROI provided.
        Based on the GEDI Data Resources github repository by : 
        """

        # Define the base CMR granule search url, including LPDAAC provider name and max page size (2000 is the max allowed)
        cmr = "https://cmr.earthdata.nasa.gov/search/granules.json?pretty=true&provider=LPDAAC_ECS&page_size=2000&concept_id="
        
        # Set up dictionary where key is GEDI shortname + version
        concept_ids = {'GEDI01_B.002': 'C1908344278-LPDAAC_ECS', 
                    'GEDI02_A.002': 'C1908348134-LPDAAC_ECS', 
                    'GEDI02_B.002': 'C1908350066-LPDAAC_ECS'}
        
        # CMR uses pagination for queries with more features returned than the page size
        page = 1
        bbox = self.roi.replace(' ', ',')  # remove any white spaces
        product = self.product+"."+self.version

        try:
            # Send GET request to CMR granule search endpoint w/ product concept ID, bbox & page number, format return as json
            cmr_response = r.get(f"{cmr}{concept_ids[product]}&bounding_box={bbox}&pageNum={page}").json()['feed']['entry']

            # If 2000 features are returned, move to the next page and submit another request, and append to the response
            while len(cmr_response) % 2000 == 0:
                page += 1
                cmr_response += r.get(f"{cmr}{concept_ids[product]}&bounding_box={bbox}&pageNum={page}").json()['feed']['entry']
            # CMR returns more info than just the Data Pool links, below use list comprehension to return a list of DP links
            return [(c['links'][0]['href'], c['granule_size']) for c in cmr_response if not ".png" in c['links'][0]['href']]
        except:
            # If the request did not complete successfully, print out the response from CMR
            print("[Finder] Request not successful.")
            print(r.get(f"{cmr}{concept_ids[product]}&bounding_box={bbox.replace(' ', '')}&pageNum={page}").json())
            exit(0)


    def _date_filter(self, granules):
        """
        GEDI Finder, by default, finds all the granules that pass over ROI.
        This function (date_filter) filters the desired granules by the dates provided.
        """
        filter_g = []

        for g in granules:
            # Date of granule is at the 7th section on CMR website
            date_sec = datetime.strptime(g[0].split("/")[7], "%Y.%m.%d")

            # Stop search query if passes end_date
            if date_sec > self.date_end:
                return filter_g

            if date_sec >= self.date_start and date_sec <= self.date_end:
                filter_g.append(g)

        return filter_g


    def _check_download_size(self, link_list):
        """
        Converts MB to GB and returns download size of all the links provided by the *link_list*
        """
        return sum(float(l[1]) for l in link_list) / 1000


    def find(self, output_filepath, save_file=True):

        all_granules = self._find_all_granules()

        print(f"[Finder] Found {len(all_granules)} granules over bbox [{self.roi}]")
        
        granules_date_filtered = self._date_filter(all_granules)

        print(f"[Finder] Between dates ({self.date_start}) and ({self.date_end}) exist {len(granules_date_filtered)} granules over bbox [{self.roi}]")
        print(f"[Finder] Estimated download size for select granules : {self._check_download_size(granules_date_filtered):.2f} GB")
        
        if save_file:
            filename = f"{self.product.replace('.', '_')}_GranuleList_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            # Open file and write each granule link on a new line
            with open(os.path.join(output_filepath, filename), "w") as gf:
                for g in granules_date_filtered:
                    gf.write(f"{g[0]}\n")

            print(f"[Finder] Saved links to file {os.path.join(output_filepath, filename)}")

        return granules_date_filtered