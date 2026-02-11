import pandas as pd
import numpy as np

# 1. Leer datos
file_path = "data/2014_2022.xls"
df = pd.read_excel(file_path, sheet_name="fermigbrst")

# 2. Limpieza básica
required_cols = [
    "t90", "t50",
    "t90_start", "t50_start",
    "flux_64",
    "t90_error", "t50_error",
    "flux_64_error",
    "dec"
]

df = df.dropna(subset=required_cols)

# Asegurar valores físicos
df = df[
    (df["t90"] > 0) &
    (df["t50"] > 0) &
    (df["flux_64"] > 0)
].copy()

# 3. Cortes temporales

# (a) GRBs cortos
df["cut_t90"] = (df["t90"] - df["t90_error"]) < 3.5

# (b) Pico principal temprano
df["relative_peak_time"] = (
    (df["t50_start"] - df["t90_start"]) / df["t90"]
)
# Propagación con error de t90
numerator = df["t50_start"] - df["t90_start"]

df["relative_peak_time_error"] = (
    np.abs(numerator) / df["t90"]**2
) * df["t90_error"]

df["cut_peak_time"] = (
    df["relative_peak_time"] - df["relative_peak_time_error"]
) < 0.2

# (c) Duración comparable del pulso principal
df["t50_t90"] = df["t50"] / df["t90"]

df["t50_t90_error"] = df["t50_t90"] * np.sqrt(
    (df["t50_error"] / df["t50"])**2 +
    (df["t90_error"] / df["t90"])**2
)

df["cut_duration_ratio"] = (
    (df["t50_t90"] + df["t50_t90_error"] > 0.1) &
    (df["t50_t90"] - df["t50_t90_error"] < 0.7)
)

# (d) Corte en flujo pico a 64 ms
df["cut_flux64"] = (df["flux_64"] - df["flux_64_error"]) < 10.0  # ph cm^-2 s^-1

# (e) Corte en declinación
df["cut_dec"] = (df["dec"] >= -10) & (df["dec"] <= 50)

# 4. Corte global
df["passes_all_cuts"] = (
    df["cut_t90"] &
    df["cut_peak_time"] &
    df["cut_duration_ratio"] &
    df["cut_flux64"] &
    df["cut_dec"]
)

# 5. Resumen de cortes
print("Eventos totales:", len(df))
print("Después de t90 < 3.5 s:", df["cut_t90"].sum())
print("Después de pico temprano:",
      (df["cut_t90"] & df["cut_peak_time"]).sum())
print("Después de t50/t90:",
      (df["cut_t90"] & df["cut_peak_time"] & df["cut_duration_ratio"]).sum())
print("Después de declinación:", df["passes_all_cuts"].sum())


# 6. Guardar prueba de cortes completa
columns_full = [
    "name",
    "t90", "t90_error",
    "t50", "t50_error",
    "flux_64", "flux_64_error",
    "dec",
    "relative_peak_time", "relative_peak_time_error",
    "t50_t90", "t50_t90_error",
    "cut_t90", "cut_peak_time",
    "cut_duration_ratio", "cut_flux64",
    "cut_dec",
    "passes_all_cuts"
]

df[columns_full].to_csv(
    "cortes/grbs_temporal_cuts_full_2022.csv",
    index=False
)

# 7. Guardar muestra final
df[df["passes_all_cuts"]].to_csv(
    "cortes/grbs_temporal_cuts_selected_2022.csv",
    index=False
)
