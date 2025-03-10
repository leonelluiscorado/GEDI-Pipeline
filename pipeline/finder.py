import os
import requests as r
from datetime import datetime

# Set up dictionary where key is GEDI shortname + version
concept_ids = {
    'GEDI01_B.002': 'C2142749196-LPCLOUD', 
    'GEDI02_A.002': 'C2142771958-LPCLOUD', 
    'GEDI02_B.002': 'C2142776747-LPCLOUD',
    'GEDI04_A.002': 'C2237824918-ORNL_CLOUD'
}

class GEDIFinder:
    """
    The Finder :class: exports all the available URLs to download GEDI Data that passes over a given ROI and timestamp.

    Args:
        product: GEDI Product (without version). Products available are {'GEDI01_B'; 'GEDI02_A'; 'GEDI02_B'; 'GEDI04_A'}
        version: Version of the desired GEDI Product. There are only two available versions 001 and 002
        date_start: Starting datetime to search for GEDI Data. Must be in format YEAR.month.day (e.g 2020.04.01)
        date_end: End datetime to search for GEDI Data. Must be in format YEAR.month.day (e.g 2020.12.31)
        roi: Region of Interest to search for granules. Coordinates must be in WG84 EPSG:4326 and organized as follows: [UL_Lat, UL_Lon, LR_Lat, LR_Lon]

    Example usage:
        finder = GEDIFinder(product='GEDI04_A', version='002', date_start='2021.01.01', date_end='2021.12.31', roi=[])
        granules = finder.find(save_file=False)
        granules
        >>> ["URL1", "URL2", "URL3", ...]
    """

    def __init__(self, product='GEDI02_A', version='002', date_start='', date_end='', recurring_months=False, roi=None):

        self.product = product
        self.version = version

        # Date format must be in "Year.month.day"
        try:
            self.date_start = datetime.strptime(date_start, "%Y.%m.%d")
            self.date_end = datetime.strptime(date_end, "%Y.%m.%d")
        except:
            print("Dates provided not valid. Valid format is \"Y.m.d\" (e.g. 2019.01.01).")

        if roi is not None:
            # GEDI Finder expects bbox to be (LL_lon, LL_lat, UR_lon, UR_lat)
            [ul_lat, ul_lon, lr_lat, lr_lon] = roi
            self.roi = " ".join(map(str, [ul_lon, lr_lat, lr_lon, ul_lat]))

        self.recurring_months = recurring_months

        if self.recurring_months:
            print("Recurring Months is TRUE. Searching between provided months across all provided years.")


    def __find_all_granules(self):
        """
        Functions that requests all the links and download sizes for each granule found over the ROI provided.
        """

        # CMR uses pagination for queries with more features returned than the page size
        page = 1
        bbox = self.roi.replace(' ', ',')  # Remove any white spaces
        product = self.product+"."+self.version

        # Provider is always after the "-" at its concept_id
        provider = concept_ids[product].split("-")[-1]

        # Define the base CMR granule search url, including LPDAAC provider name and max page size (2000 is the max allowed)
        cmr = f"https://cmr.earthdata.nasa.gov/search/granules.json?pretty=true&provider={provider}&page_size=2000&concept_id="

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


    def __date_filter(self, granules):
        """
        The finder outputs all the granules that pass over ROI, by default.
        This function (date_filter) filters the desired granules by the dates provided.
        """
        filter_g = []

        # Dynamically create the set of allowed months from date_start to date_end
        rec_months = set(range(self.date_start.month, self.date_end.month + 1))

        for g in granules:
            # Date of granule is in the filename described as a Julian Date YYYYDDD (e.g. 2020348)
            granule_name = g[0].split("/")[-1]
            date_sec = granule_name.split("_")[2][0:7]
            date_sec = datetime.strptime(date_sec, "%Y%j")

            # Stop search query if passes end_date
            if date_sec > self.date_end:
                return filter_g

            # Apply recurring months filter if enabled
            if self.recurring_months and not date_sec.month in rec_months:
                continue  # Skip this granule

            if date_sec >= self.date_start and date_sec <= self.date_end:
                filter_g.append(g)

        return filter_g


    def __check_download_size(self, link_list):
        """
        Converts MB to GB and returns download size of all the links provided by the *link_list*
        """
        return sum(float(l[1]) for l in link_list) / 1000


    def find(self, save_file=True, output_filepath=None) -> list:
        """
        Executes the finding algorithm.
        Args:
            save_file: If true, saves all the download URLs to a file.
            output_filepath: Filepath to URLs file.

        Returns:
            a list with all the date filtered granule links for download
        """

        all_granules = self.__find_all_granules()

        print(f"[Finder] Found {len(all_granules)} granules over bbox [{self.roi}]")
        
        granules_date_filtered = self.__date_filter(all_granules)

        print(f"[Finder] Between dates ({self.date_start}) and ({self.date_end}) exist {len(granules_date_filtered)} granules over bbox [{self.roi}]")
        print(f"[Finder] Estimated download size for select granules : {self.__check_download_size(granules_date_filtered):.2f} GB")
        
        if save_file:
            # Save txt file with all the links found
            filename = f"{self.product.replace('.', '_')}_GranuleList_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
            output_filepath = output_filepath if not output_filepath is None else ""
            # Open file and write each granule link on a new line
            with open(os.path.join(output_filepath, filename), "w") as gf:
                for g in granules_date_filtered:
                    gf.write(f"{g[0]}\n")

            print(f"[Finder] Saved links to file {os.path.join(output_filepath, filename)}")

        return granules_date_filtered