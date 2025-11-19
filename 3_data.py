import os
import glob
import numpy as np
import rasterio
from rasterio.merge import merge
import geopandas as gpd
import pandas as pd  # <-- REQUIRED


# Load NFI shapefile
nfi_path = r"C:\Users\mabrown\Desktop\P6_admin\nfi_data\correct_NFI.shp"
nfi = gpd.read_file(nfi_path)

print(nfi.head())


# Input/output folders
input_folder = r"S:\mbrown\composite_force\mosaics"
base_folder = r"S:\mbrown\composite_force"

output_folder = os.path.join(base_folder, "extracts")
os.makedirs(output_folder, exist_ok=True)

# Print TIF files found
tif_files = glob.glob(os.path.join(input_folder, "*.tif"))
print("Found raster files:", tif_files)


# Function to load rasters into a stack
def stack_rasters(file_list):
    src_files = []
    for fp in file_list:
        print(f"Loading raster: {fp}")
        src = rasterio.open(fp)
        # Store (dataset, filename) together
        src_files.append((src, os.path.basename(fp)))
    return src_files

# Load rasters
stack_extract = stack_rasters(tif_files)

# Extract raster values at point locations
def extract_points_to_csv(raster_stack, shapefile, output_csv):
    """
    Extract raster values at point locations from a stack of rasters and
    write combined attributes + raster values to a CSV.
    """

    # --------------------------------
    # 1. Ensure CRS match
    # --------------------------------
    raster_crs = raster_stack[0][0].crs   # first element: (dataset, name)
    if shapefile.crs != raster_crs:
        shapefile = shapefile.to_crs(raster_crs)

    extracted_rows = []

    # --------------------------------
    # 2. Loop through all points
    # --------------------------------
    for idx, row in shapefile.iterrows():

        geom = row.geometry
        if geom.geom_type != "Point":
            continue

        coords = [(geom.x, geom.y)]
        value_dict = {}

        # --------------------------------
        # 3. Sample from each raster
        # --------------------------------
        for ras, ras_name in raster_stack:

            sampled = list(ras.sample(coords))[0]

            # If multi-band
            if len(sampled) > 1:
                for i, band_val in enumerate(sampled, start=1):
                    col_name = f"{ras_name}_band{i}"
                    value_dict[col_name] = band_val
            else:
                # single-band raster
                value_dict[ras_name] = sampled[0]

        # --------------------------------
        # 4. Combine shapefile attributes + raster values
        # --------------------------------
        row_dict = row.drop(labels="geometry").to_dict()
        row_dict.update(value_dict)

        extracted_rows.append(row_dict)

    # --------------------------------
    # 5. Save as CSV
    # --------------------------------
    df = pd.DataFrame(extracted_rows)
    df.to_csv(output_csv, index=False)

    print(f"\nExtraction complete. Saved: {output_csv}")
    print(df.head())


# ------------------------------------------------------------
# Run the extraction
# ------------------------------------------------------------
extract_points_to_csv(
    stack_extract,
    nfi,
    os.path.join(base_folder, "nfi_raster_extracts.csv")
)
