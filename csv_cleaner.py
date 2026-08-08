import pandas as pd


def clean_csv(csv_path):
    session_info = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [next(f).strip() for _ in range(8)]

    for line in lines:
        parts = line.split(",", 1)
        if len(parts) == 2:
            key, value = parts
            session_info[key.strip()] = value.strip()

    telemetry_df = pd.read_csv(
        csv_path,
        header=8,          
        low_memory=False   
    )

    telemetry_df.columns = [c.strip() for c in telemetry_df.columns]
    telemetry_df = telemetry_df.iloc[1:].reset_index(drop=True)

    # Convert type
    for col in telemetry_df.columns:
        converted = pd.to_numeric(telemetry_df[col], errors="coerce")

        non_nan_ratio = converted.notna().mean()

        if non_nan_ratio > 0.7:   
            telemetry_df[col] = converted
        else:
            telemetry_df[col] = telemetry_df[col].astype(str)

    return session_info, telemetry_df
