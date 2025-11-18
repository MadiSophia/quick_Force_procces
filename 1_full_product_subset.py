import os
import glob
import numpy as np
import rasterio

# ---------------------------------------------------------
# 1. Paths
# ---------------------------------------------------------
base = r"S:\mbrown\FORCE_Sentinel_TK"
out_dir = r"S:\mbrown\composite_force"
os.makedirs(out_dir, exist_ok=True)

# ---------------------------------------------------------
# 2. Process tiles
# ---------------------------------------------------------
for tile in os.listdir(base):
    tile_path = os.path.join(base, tile)
    
    if not os.path.isdir(tile_path):
        continue

    print("\n---", tile, "---")

    # Get all .tif files
    tif_files = glob.glob(os.path.join(tile_path, "*.tif"))
    ndv_files = [f for f in tif_files if "NDV" in os.path.basename(f)]

    for f in ndv_files:
        print("Processing:", os.path.basename(f))

        with rasterio.open(f) as src:
            descriptions = src.descriptions
            nodata = src.nodata

            # Read all bands as float32 for NaN handling
            all_bands = src.read().astype('float32')
            
            # Replace nodata values with np.nan
            if nodata is not None:
                all_bands[all_bands == nodata] = np.nan

            # Identify July and August band indices
            month_indices = {"07": [], "08": []}
            for i, desc in enumerate(descriptions):
                try:
                    date = desc.split("_")[0]  # 'YYYYMMDD'
                    month = date[4:6]
                    if month in month_indices:
                        month_indices[month].append(i)
                except Exception:
                    continue

            # Compute medians per month
            for month, month_name in [("07", "July"), ("08", "August")]:
                idx = month_indices[month]
                if not idx:
                    continue

                median = np.nanmedian(all_bands[idx, :, :], axis=0).astype('float32')

                # Optional: set NaNs back to nodata
                if nodata is not None:
                    median[np.isnan(median)] = nodata

                # Save median raster
                base_name = os.path.splitext(os.path.basename(f))[0]
                out_path = os.path.join(out_dir, f"{tile}_{base_name}_{month_name}Median.tif")

                with rasterio.open(
                    out_path,
                    'w',
                    driver='GTiff',
                    height=median.shape[0],
                    width=median.shape[1],
                    count=1,
                    dtype='float32',
                    crs=src.crs,
                    transform=src.transform,
                    nodata=nodata
                ) as dst:
                    dst.write(median, 1)

                print(f"  → Saved {month_name} median: {out_path}")
