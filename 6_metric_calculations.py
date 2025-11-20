import pandas as pd
import numpy as np

#script to calculate resistance, resilience, and recovery metrics from spectral data 


# 1- load in spectral dataset from CSV (currently dummy data) 
df = pd.read_csv(r"S:\mbrown\Tasks_20_10_26_10\NFI\NFI_WGS_full.csv")


# 2- Replace -9999 values with NaN
df = df.replace(-9999, np.nan).replace(-9999.0, np.nan)


# 3- Select index of choice 

ndvi_cols = [col for col in df.columns if col.startswith("NDVI")]

keep_cols = ndvi_cols + ["ID", "BART", "Species"]

df = df[keep_cols]

# 4 - Calculate Resilience (Rs)
df["Rs_2018"] = df["NDVI_2018"] / df["NDVI_2017"]
df["Rs_2022"] = df["NDVI_2022"] / df["NDVI_2021"]

# 5. Calculate Recovery (Rc)

df["Rc_2018"] = df["NDVI_2021"] / df["NDVI_2017"]
df["Rc_2022"] = df["NDVI_2025"] / df["NDVI_2021"]


# 6. Calculate Resistance (Rr)

df["Rr_2018"] = df["NDVI_2021"] / (df["NDVI_2018"] * 3)
df["Rr_2022"] = df["NDVI_2025"] / (df["NDVI_2021"] * 3)

# 7. Calculate Persistence (Pe)

df["Pe_2018"] = ((df["Rc_2018"] - df["Rs_2018"])**2) / (2 * df["Rr_2018"])
df["Pe_2022"] = ((df["Rc_2022"] - df["Rs_2022"])**2) / (2 * df["Rr_2022"])


# 8. (Optional) Show first few rows

print(df.head())


# 9. (Optional) Save to new CSV

# df.to_csv(r"S:\mbrown\Tasks_20_10_26_10\NFI\NFI_resilience_metrics.csv", index=False)
