# Import necessary libraries
import os
import h5py
import pandas as pd
from shapely.geometry import Polygon
import geopandas as gp
import argparse
import sys
import numpy as np
import warnings
warnings.filterwarnings("ignore")

from utils.utils import get_date_from_gedi_fn

# Default layers to be subset and exported, see README for information on how to add additional layers
l1b_subset = ['/geolocation/latitude_bin0', '/geolocation/longitude_bin0', '/channel', '/shot_number', '/rx_sample_start_index',
             '/rxwaveform','/rx_sample_count', '/stale_return_flag', '/tx_sample_count', '/txwaveform',
             '/geolocation/degrade', '/geolocation/delta_time', '/geolocation/digital_elevation_model',
              '/geolocation/solar_elevation',  '/geolocation/local_beam_elevation',  '/noise_mean_corrected',
             '/geolocation/elevation_bin0', '/geolocation/elevation_lastbin', '/geolocation/surface_type', '/geolocation/digital_elevation_model_srtm' '/geolocation/degrade']

l2a_subset = ['/lat_lowestmode', '/lon_lowestmode', '/channel', '/shot_number', '/degrade_flag', '/delta_time', 
             '/digital_elevation_model', '/elev_lowestmode', '/quality_flag', '/rh', '/sensitivity', '/rx_cumulative', '/digital_elevation_model_srtm', 
             '/elevation_bias_flag', '/surface_flag',  '/num_detectedmodes',  '/selected_algorithm',  '/solar_elevation']


l2b_subset = ['/geolocation/lat_lowestmode', '/geolocation/lon_lowestmode', '/channel', '/geolocation/shot_number',
             '/cover', '/cover_z', '/fhd_normal', '/pai', '/pai_z',  '/rhov',  '/rhog',
             '/pavd_z', '/l2a_quality_flag', '/l2b_quality_flag', '/rh100', '/sensitivity',  
             '/stale_return_flag', '/surface_flag', '/geolocation/degrade_flag',  '/geolocation/solar_elevation',
             '/geolocation/delta_time', '/geolocation/digital_elevation_model', '/geolocation/elev_lowestmode', '/pgap_theta']

l4a_subset = ['/lat_lowestmode', '/lon_lowestmode', '/channel', '/shot_number', '/degrade_flag', '/delta_time', 
             '/digital_elevation_model', '/elev_lowestmode', '/l4_quality_flag', '/agbd', '/agbd_se', '/agbd_t', '/agbd_t_se', '/sensitivity',
             '/rx_cumulative', '/digital_elevation_model_srtm', '/elevation_bias_flag', '/surface_flag',  '/num_detectedmodes',  '/selected_algorithm',
             '/solar_elevation'] # TODO: select relevant L4A product variables

# Default BEAM Subset
beam_subset = ['BEAM0000', 'BEAM0001', 'BEAM0010', 'BEAM0011', 'BEAM0101', 'BEAM0110', 'BEAM1000', 'BEAM1011']
 

class GEDISubsetter:
    """
    The GEDISubsetter :class: clips the granule to the specified ROI and selects all the desired variables for each footprint
    Args:
        roi: Region of Interest to search for granules. Coordinates must be in WG84 EPSG:4326 and organized as follows: [UL_Lat, UL_Lon, LR_Lat, LR_Lon]
             Rectangle polygons ONLY. TODO: Take SHP files as argument and MultiPolygon
        sds: Science Dataset variables used to extract from the granule. Check the product Data Dictionary for more info.
             If the variable is inside a group except BEAMXXXX/, it must be specified ( e.g '/geolocation/lat_lowestmode' )
             If None, extracts the default variables; else it appends to default variables.
        beams: Keeps footprints of select BEAMS to extract from the granule. If none, selects all the available GEDI Beams.
               Available BEAMS: ['BEAM0000', 'BEAM0001', 'BEAM0010', 'BEAM0011', 'BEAM0101', 'BEAM0110', 'BEAM1000', 'BEAM1011']
        product: GEDI Product (without version). Products available are {'GEDI01_B'; 'GEDI02_A'; 'GEDI02_B'; 'GEDI04_A'}
        out_dir: Filepath to save the subsetted granule in the 'out_format' file.
        out_format: File format for the subsetted granule. 
                    The subset function outputs the final clipped and subsetted granule to a GeoPKG file, by default.
                    TODO: The user can also select the following options: {GEOJSON, SHP}

    Example:
        subsetter = GEDISubsetter(roi=[.., .., .., ..], product='GEDI02_A', out_dir='some_path')
        subset_df = subsetter.subset('[filename].h5')  # Outputs a GeoPandas dataframe
        >>> ...
        >>>  [Subsetter] [filename].gpkg saved at: [out_dir]+filename ...
        subset_df.info()
        >>> ...
    """
    
    def __init__(self, roi, product, out_dir, out_format=None, sds=None, beams=None):
        self.roi = roi
        self.sds = sds
        self.beams = beams
        self.product = product
        self.out_dir = out_dir
        self.out_format = "GPKG" if out_format is None else out_format # Defaults to GeoPKG

        self._preprocess()

    def _preprocess(self):

        # Define Polygon for subsetting
        try:
            self.ROI = Polygon([(self.roi[1], self.roi[0]), (self.roi[3], self.roi[0]), (self.roi[3], self.roi[2]), (self.roi[1], self.roi[2])]) 
        except:
            print('[Subsetter] Error: unable to read input bounding box coordinates, the required format is: ul_lat,ul_lon,lr_lat,lr_lon')
            sys.exit(2)

        # Keep the exact input geometry for the final clip to ROI
        self.final_clip = gp.GeoDataFrame(index=[0], geometry=[self.ROI], crs='EPSG:4326')

        # Define BEAMS
        if self.beams is not None:
            self.beam_subset = self.beams.split(',')
        else:
            self.beam_subset = beam_subset

        # Define product and build SDS subset for extraction
        if 'GEDI01_B' in self.product:
            self.sds_subset = l1b_subset
        elif 'GEDI02_A' in self.product:
            self.sds_subset = l2a_subset
        elif 'GEDI02_B' in self.product:
            self.sds_subset = l2b_subset
        else:
            self.sds_subset = l4a_subset

        # Append defined additional sds to main sds_subset
        if self.sds is not None:
            layer_subset = self.sds.split(',')
            [self.sds_subset.append(y) for y in layer_subset]


    def _select_beams_within_roi(self, gedi_file, gedi_df, beams, gedi_sds):
        """
        This function selects all the footprints inside the ROI with the select beams
        Reference:  https://github.com/nasa/GEDI-Data-Resources/blob/main/python/scripts/GEDI_Subsetter/GEDI_Subsetter.py
        """

        # Loop through each beam and create a geodataframe with lat/lon for each shot, then clip to ROI
        for b in beams:
            beams_sds = [s for s in gedi_sds if b in s]
            
            # Search for latitude, longitude, and shot number SDS
            lat = [l for l in beams_sds if self.sds_subset[0] in l][0]  
            lon = [l for l in beams_sds if self.sds_subset[1] in l][0]
            shot = f'{b}/shot_number'          
            
            # Open latitude, longitude, and shot number SDS
            shots = gedi_file[shot][()]
            lats = gedi_file[lat][()]
            lons = gedi_file[lon][()]
            
            # Append BEAM, shot number, latitude, longitude and an index to the GEDI dataframe
            geoDF = pd.DataFrame({'BEAM': len(shots) * [b], shot.split('/', 1)[-1].replace('/', '_'): shots,
                                'Latitude':lats, 'Longitude':lons, 'index': np.arange(0, len(shots), 1)})

            # Convert lat/lon coordinates to shapely points and append to geodataframe
            geoDF = gp.GeoDataFrame(geoDF, geometry=gp.points_from_xy(geoDF.Longitude, geoDF.Latitude))

            # Clip to only include points within the user-defined bounding box
            geoDF = geoDF[geoDF['geometry'].within(self.ROI.envelope)]
            gedi_df = pd.concat([gedi_df, geoDF])
            del geoDF
    
        # Convert to geodataframe and add crs
        gedi_df = gp.GeoDataFrame(gedi_df)
        gedi_df.crs = 'EPSG:4326'
        del lats, lons, shots

        return gedi_df


    def _select_sds_variables(self, gedi_file, gedi_df, beams, gedi_sds):
        """
        For each clipped footprint (to ROI), subsets to desired variable set available in the product
        Reference:  https://github.com/nasa/GEDI-Data-Resources/blob/main/python/scripts/GEDI_Subsetter/GEDI_Subsetter.py
        """

        beams_df = pd.DataFrame()  # Create dataframe to store SDS
        j = 0
        
        # Loop through each beam and extract subset of defined SDS
        for b in beams:
            beam_df = pd.DataFrame()
            beam_sds = [s for s in gedi_sds if b in s and not any(s.endswith(d) for d in self.sds_subset[0:3])]
            shot = f'{b}/shot_number'
            
            try:
                # set up indexes in order to retrieve SDS data only within the clipped subset from above
                mindex = min(gedi_df[gedi_df['BEAM'] == b]['index'])
                maxdex = max(gedi_df[gedi_df['BEAM'] == b]['index']) + 1
                shots = gedi_file[shot][mindex:maxdex]
            except ValueError:
                print(f"[Subsetter] No intersecting shots found for {b} for {gedi_file}.")
                continue

            # Loop through and extract each SDS subset and add to DF
            for s in beam_sds:
                j += 1
                s_name = s.split('/', 1)[-1].replace('/', '_')

                # Datasets with consistent structure as shots
                if gedi_file[s].shape == gedi_file[shot].shape:
                    beam_df[s_name] = gedi_file[s][mindex:maxdex]  # Subset by index
                
                # Datasets with a length of one 
                elif len(gedi_file[s][()]) == 1:
                    beam_df[s_name] = [gedi_file[s][()][0]] * len(shots) # create array of same single value
                
                # Multidimensional datasets
                elif len(gedi_file[s].shape) == 2 and 'surface_type' not in s: 
                    all_data = gedi_file[s][()][mindex:maxdex]
                    
                    # For each additional dimension, create a new output column to store those data
                    for i in range(gedi_file[s].shape[1]):
                        step = []
                        for a in all_data:
                            step.append(a[i])

                        beam_df[f"{s_name}_{i}"] = step
                
                # Waveforms
                elif s.endswith('waveform') or s.endswith('pgap_theta_z'):
                    waveform = []
                    
                    if s.endswith('waveform'):
                        # Use sample_count and sample_start_index to identify the location of each waveform
                        start = gedi_file[f'{b}/{s.split("/")[-1][:2]}_sample_start_index'][mindex:maxdex]
                        count = gedi_file[f'{b}/{s.split("/")[-1][:2]}_sample_count'][mindex:maxdex]
                    
                    # for pgap_theta_z, use rx sample start index and count to subset
                    else:
                        # Use sample_count and sample_start_index to identify the location of each waveform
                        start = gedi_file[f'{b}/rx_sample_start_index'][mindex:maxdex]
                        count = gedi_file[f'{b}/rx_sample_count'][mindex:maxdex]

                    wave = gedi_file[s][()]
                    
                    # In the dataframe, each waveform will be stored as a list of values
                    for k in range(len(start)):
                        single_WF = wave[int(start[k] - 1): int(start[k] - 1 + count[k])]
                        waveform.append(','.join([str(q) for q in single_WF]))

                    beam_df[s_name] = waveform
                
                # Surface type 
                elif s.endswith('surface_type'):
                    surfaces = ['land', 'ocean', 'sea_ice', 'land_ice', 'inland_water']
                    all_data = gedi_file[s][()]

                    for i in range(gedi_file[s].shape[0]):
                        beam_df[f'{surfaces[i]}'] = all_data[i][mindex:maxdex]

                    del all_data

                else:
                    print(f"[Subsetter] SDS: {s} not found")
            
            beams_df = pd.concat([beams_df, beam_df])

        del beam_df, beam_sds, beams, gedi_file, gedi_sds, shots
        
        return beams_df


    def subset(self, granule):
        """
        Subsets an entire downloaded granule file and exports to GPKG (or other format) with the same filename

        Args:
            granule: filepath to granule file, already downloaded.

        Returns:
            Geopandas dataframe with all the intersecting footprints at ROI and select SDS variables
            Also exports this dataframe to a GPKG file with the same name as the granule.
            Returns None / Does not save if all the footprints in the granule do not intersect with ROI
            or ScienceDataset is empty / does not align with product.
        """

        # Open granule file
        print(f"[Subsetter] Processing file: {granule}")
        h5_granule = h5py.File(granule, 'r')      # Open file
        granule_name = granule.split('.h5')[0]  # Keep original filename

        # Check if already subsetted file exists
        ## TODO: not sure if good idea to keep this or not.
        if os.path.exists(os.path.join(self.out_dir, granule.split("/")[-1].replace(".h5", ".gpkg"))):
            print(f"[Subsetter] File: {granule} already subsetted. Skipping...")
            return

        gedi_objs = []
        h5_granule.visit(gedi_objs.append)  # Retrieve list of datasets

        gedi_sds = [str(o) for o in gedi_objs if isinstance(h5_granule[o], h5py.Dataset)]

        # Subset to the selected datasets
        gedi_sds = [c for c in gedi_sds if any(c.endswith(d) for d in self.sds_subset)]

        # Get unique list of beams and subset to user-defined subset or default (all beams)
        beams = []
        for v in gedi_sds:
            beam = v.split('/', 1)[0]
            if beam not in beams and beam in self.beam_subset:
                beams.append(beam)

        gedi_df = pd.DataFrame()  # Create empty dataframe to store GEDI datasets    
        del beam, gedi_objs, v

        # Select beams and clip to roi
        print(f"[Subsetter] Selecting BEAMS and clipping to ROI ...")
        gedi_df = self._select_beams_within_roi(h5_granule, gedi_df, beams, gedi_sds)
        
        if gedi_df.shape[0] == 0:
            print(f"[Subsetter] No intersecting shots were found between {granule_name} and the region of interest submitted.")
            return None

        else:
            print(f"[Subsetter] Intersecting shots found. Selecting variables from subset ...")
            beams_df = self._select_sds_variables(h5_granule, gedi_df, beams, gedi_sds)

            # Combine geolocation dataframe with SDS layer dataframe
            out_df = pd.merge(gedi_df, beams_df, left_on='shot_number', right_on=[sn for sn in beams_df.columns if sn.endswith('shot_number')][0])
            
            out_df.index = out_df['index']

            del gedi_df, beams_df  
            
            # Subset the output DF to the actual boundary of the input ROI
            out_df = gp.overlay(out_df, self.final_clip)

            # Drop all empty or not valid (NaN) geometry, as it corrupts the final output file
            out_df = out_df.dropna(subset=['geometry'])
            out_df = out_df[out_df['geometry'].is_valid]
            out_df = out_df[~out_df['geometry'].is_empty]

            # Write date column to subsetted file
            out_df['date'] = get_date_from_gedi_fn(granule_name)
        
        ## TODO: Implement the saving to file module as optional
        try:    
            # Export final geodataframe as Geojson
            print(f"[Subsetter] {granule_name}.gpkg")
            out_df.to_file(f"{granule_name}.gpkg", driver='GPKG')
            print(f"[Subsetter] {granule.replace('.h5', '.gpkg')} saved at: {self.out_dir}")

        except ValueError:
            print(f"[Subsetter] {granule_name} intersects the bounding box of the input ROI, but no shots intersect final clipped ROI.")

        return out_df