#Author: Lydia 
#GHS-MOD Data downloaded from https://ghsl.jrc.ec.europa.eu/download.php?ds=pop
#2022 Shape file download from https://data.humdata.org/dataset/cod-ab-pak
#Remember to clip the Shapefile to remove the disputed areas (AJK and GB) For Pakistan
###################################################################################


# first install all the softwares on git and then import
import geopandas as gpd
import pandas as pd
import os
import rasterio
import GOSTrocks.rasterMisc as rMisc
from rasterio import features
import numpy as  np
#pip install xarray-spatial
from xrspatial import zonal_stats
import rioxarray
from rasterio.transform import from_origin
import warnings




#this is describing all the inputs
#smod vals the 8 degrees of urbanization
smod_vals = [10, 11, 12, 13, 21, 22, 23, 30]
# years that are have GHSL data for
years = ["2020"]  # Add more years as needed
#years = ["1975", "1980", "1985", "1990", "1995", "2000", "2005", "2010", "2015", "2020", "2025", "2030",]  # Add or subtract years as needed
# read input files
iso3 = 'PAK'
shortnm = 'adm0'
adm0 = ''
homedir = os.getcwd()


# creating the loop
for year in years:
    outdir = os.path.join(homedir, "Input") #this is the directory code
    outdir2 = os.path.join(homedir, "Output") #this is the second directory code

    input_dir = os.path.join(outdir, year)
    output_dir = os.path.join(outdir2, year)
    admin_input_dir = os.path.join(outdir, 'admin units')

    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    #creating the PAK POP and SMOD raster using the pakistan boundary shapefile
    ghssmod_file = os.path.join(output_dir, year + "_" + "GHS" + "_" + iso3 + "_" + "SMOD" + '.tif')
    shape_file = os.path.join(input_dir, "pak_admbnda_adm0_wfp_20220909") #change the shapefile name based on the what the boundary shapefile is labelled- 
    aoi_pop = os.path.join(output_dir, year + "_" + "GHS" + "_" + iso3 + "_" + "POP" + '.tif')


    #good to have error and print commands to check if everything is working    
    print("Processing year:", year)
    print("Input directory:", input_dir)
    print("Output directory:", output_dir)    
    
    #creating urban cal function
    def urban_cal(year, adm, inA, smod_file, pop_file, inRaster):
        final = pd.Series(dtype=float)
        stats = {}
        shape_areas =[]
        inRaster = os.path.join(input_dir, inRaster)
        xpop = rioxarray.open_rasterio(inRaster).squeeze()
        inA_mw = gpd.read_file(inA)

        adm_en = adm.upper() + "_EN"
        adm_code = adm.upper() + "_PCODE"
        inA_out = inA_mw.to_crs(xpop.rio.crs)
        print("Columns in DataFrame:", inA_out.columns)
        print("Number of rows in DataFrame:", len(inA_out))
        print(inA_out.head())  # Print a sample of the DataFrame
        print(inA_out.columns)
        print(inA)
        print("Columns in DataFrame:", inA_out.columns)
        print(f"Columns {adm_en} and/or {adm_code} do not exist in the DataFrame.")
        df_zones = inA_out[["Shape_Area", adm_code, adm_en]]
        geom = inA_out[['geometry', "Shape_Area"]].values.tolist()
        final_df = pd.DataFrame()

        #creating the binary tiff files for each smod value- 
        for val in smod_vals:
            cur_smod = (smod_file == val).astype(int)
            #smod = (smod_file == val)*pop_file
            cur_pop = pop_file * cur_smod
            total_curpop = cur_pop.sum()
            perUrban = (total_curpop.sum() / total_pop * 100)
            
            
            #this is the name and filepath of the smod_pop raster file

            out_name = os.path.join(output_dir, f"{year}_{iso3}_{val}_smod_pop.tif")
            
            print("out_name:", out_name)
            
            cur_pop = cur_pop.squeeze()

            mem_raster = rasterio.MemoryFile()
            with mem_raster.open(driver='GTiff', 
                        width=cur_pop.shape[1],  # Adjust width to match the shape of cur_pop
                        height=cur_pop.shape[0],  # Adjust height to match the shape of cur_pop
                        count=1,  # Single band
                        dtype=cur_pop.dtype, 
                        transform=out_meta['transform'],  # Use metadata from out_meta
                        crs=out_meta['crs']) as dataset:
                #Write the population data to the raster
                dataset.write(cur_pop, 1)
            
            #if os.path.exists(out_name):
                #print(f"File {out_name} already exist.")
            #else:
                #with rasterio.open(out_name, 'w', **out_meta) as out_urban:
                    #out_urban.write(cur_pop)
                    #print(f"Raster written successfully for {out_name}")             

            # Zonal Statistics, reference: https://carpentries-incubator.github.io/geospatial-python/10-zonal-statistics/index.html
            smod_pop = rioxarray.open_rasterio(mem_raster).squeeze()
            #print(f"Raster opened successfully for {out_name}")
            
            
            #we used rasterized geom for the zonal statistic because we only have the geometry so we created a rasterized version of your zones, where each zone is represented as a raster with unique values.
            fields_rasterized = features.rasterize(geom, out_shape=smod_pop.shape, transform=smod_pop.rio.transform())
            fields_rasterized_xarr = smod_pop.copy()
            fields_rasterized_xarr.data = fields_rasterized

            results= zonal_stats(fields_rasterized_xarr, smod_pop, stats_funcs=['sum'])

            # disable chained assignments
            pd.options.mode.chained_assignment = None

            df_zones['Shape_Area'] = df_zones['Shape_Area'].astype(np.float32)
            results = results.rename(columns={'sum': 'sum_'+ str(val) } )
            final = df_zones.merge(results, how="left", left_on='Shape_Area', right_on='zone')
            final = final.drop('zone', axis = 1)
            final.iloc[:, -1:] = final.iloc[:, -1].apply(pd.to_numeric).round(5)

            if final_df.empty:
                final_df = final
            else:
                final_df = pd.concat([final_df, final], axis= 1)
                final_df = final_df.loc[:, ~final_df.columns.duplicated()].copy()


        output_file = os.path.join(output_dir, year + "_" + iso3 + "_" + adm + ".csv")
        final_df.to_csv(os.path.join(output_file))

    #this is basically saying find the country shapefile or create it- as you can see is that the python code starts frm the bottom and goes up- this is why some of the variables make more sense as you scroll down
    def find_country_shapefile(year):
        shape_files = os.listdir()
        adm0 = ""
        for files in shape_files:
            if (files.endswith(".shp")) & ("adm0" in files):
                adm0 = files
                break
        return adm0
    #The function to find the global POP and SMOD file in each year
    def find_global_file_location(year, type):
        tif_files = os.listdir()
        global_file = ''
        for f in tif_files:
            if type == 'SMOD':
                if (f.endswith(".tif")) & ('SMOD' in f) & (year in f) & ('GLOBE' in f):
                    global_file = f
            elif (f.endswith(".tif")) & ('POP' in f) & (year in f) & ('GLOBE' in f):
                    global_file = f
        return global_file

    #clipping the global rasters files
    os.chdir(admin_input_dir)
    adm0 = find_country_shapefile(str(year))
    inAOI = gpd.read_file(adm0)
    os.chdir(input_dir)
    if not os.path.exists(ghssmod_file):
        global_smod = find_global_file_location(year, 'SMOD')
        global_smod = os.path.join(input_dir, global_smod)
        inR = rasterio.open(global_smod)
        inAOI = inAOI.to_crs(inR.crs)
        rMisc.clipRaster(inR, inAOI, ghssmod_file)

    if (not os.path.exists(aoi_pop)) & (adm0 != ''):
        global_pop = find_global_file_location(year, 'POP')
        global_pop = os.path.join(input_dir, global_pop)
        inR = rasterio.open(global_pop)
        inAOI = inAOI.to_crs(inR.crs)
        rMisc.clipRaster(rasterio.open(global_pop), inAOI, aoi_pop)

    SMOD = rasterio.open(ghssmod_file).read()
    inPop = rasterio.open(aoi_pop)
    inP = rasterio.open(aoi_pop)
    if inAOI.crs != inPop.crs:
        inAOI = inAOI.to_crs(inPop.crs)

    out_meta = inPop.meta
    inPop = inPop.read()
    inPop = inPop * (inPop > 0)
    total_pop = inPop.sum()

    os.chdir(admin_input_dir)
    shape_files = os.listdir()
    adm = []
    for file in shape_files:
        if file.endswith(".shp"):
            if "adm0" in file:
                shortnm = 'adm0'
            elif "adm1" in file:
                shortnm = 'adm1'
            elif "adm2" in file:
                shortnm = 'adm2'
            elif "adm3" in file:
                shortnm = 'adm3'    

            inA = gpd.read_file(file)
            if inA.crs != inP.crs:
                inA = inAOI.to_crs(inP.crs)
            urban_cal(year, shortnm, file, SMOD, inPop, ghssmod_file)
    os.chdir(homedir)
    
    