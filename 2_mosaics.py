import os
import glob
import numpy as np
import rasterio
from rasterio.merge import merge

# ------------------------------------------------------------
# Step 1: Define input/output folders
# ------------------------------------------------------------
input_folder = r"S:\mbrown\composite_force"
output_folder = os.path.join(input_folder, "mosaics")
os.makedirs(output_folder, exist_ok=True)

print("Input folder:", input_folder)
print("Output folder:", output_folder)

# ------------------------------------------------------------
# Step 2: Collect ALL .tif files in the input folder
# ------------------------------------------------------------
tif_files = glob.glob(os.path.join(input_folder, "*.tif"))
print(f"Found {len(tif_files)} .tif files")

# ------------------------------------------------------------
# Step 3: Define the groups we want to mosaic
# ------------------------------------------------------------
groups = {
    "July_2017":   {"year": "2017", "month": "JulyMedian"},
    "August_2017": {"year": "2017", "month": "AugustMedian"},
    "July_2018":   {"year": "2018", "month": "JulyMedian"},
    "August_2018": {"year": "2018", "month": "AugustMedian"},
}

# ------------------------------------------------------------
# Step 4: Process each group separately
# ------------------------------------------------------------
for group_name, filters in groups.items():
    print(f"\n--- Processing group: {group_name} ---")

    # Filter files that contain BOTH the month and the year
    group_files = [f for f in tif_files if filters["year"] in f and filters["month"] in f]
    print(f"  Files matched: {len(group_files)}")

    if len(group_files) == 0:
        print(f"  No files found for {group_name}, skipping.")
        continue

    # ------------------------------------------------------------
    # Step 5: Open rasters, convert nodata to np.nan, divide by 10000
    # ------------------------------------------------------------
    datasets = []
    for f in group_files:
        print(f"  Reading: {f}")
        src = rasterio.open(f)
        data = src.read(1).astype("float32")

        # Convert nodata to np.nan
        if src.nodata is not None:
            data[data == src.nodata] = np.nan

        # Scale
        data /= 10000

        # Create memory dataset
        mem_profile = src.profile.copy()
        mem_profile.update(dtype="float32", nodata=np.nan)

        memfile = rasterio.io.MemoryFile()
        with memfile.open(**mem_profile) as mem_dst:
            mem_dst.write(data, 1)
        datasets.append(memfile.open())

        src.close()  # close original file

    # ------------------------------------------------------------
    # Step 6: Mosaic the rasters while preserving np.nan
    # ------------------------------------------------------------
    print("  Mosaicking files...")
    mosaic, mosaic_transform = merge(datasets, nodata=np.nan)

    # ------------------------------------------------------------
    # Step 7: Write output without overwriting
    # ------------------------------------------------------------
    output_path = os.path.join(output_folder, f"{group_name}_mosaic.tif")

    # Ensure unique output name
    if os.path.exists(output_path):
        base = output_path.replace(".tif", "")
        i = 1
        while os.path.exists(f"{base}_{i}.tif"):
            i += 1
        output_path = f"{base}_{i}.tif"

    print(f"  Writing mosaic to: {output_path}")

    out_meta = datasets[0].profile.copy()
    out_meta.update({
        "height": mosaic.shape[1],
        "width": mosaic.shape[2],
        "transform": mosaic_transform,
        "dtype": "float32",
        "nodata": np.nan
    })

    with rasterio.open(output_path, "w", **out_meta) as dst:
        dst.write(mosaic[0], 1)

    # ------------------------------------------------------------
    # Step 8: Close memory datasets to free memory
    # ------------------------------------------------------------
    for ds in datasets:
        ds.close()

    print(f"  :) Finished writing {output_path}")

print("\nAll mosaics completed successfully.")
