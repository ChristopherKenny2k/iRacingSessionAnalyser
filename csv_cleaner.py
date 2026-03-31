import pandas as pd

def clean_csv(csv_path):
    session_info = {}

    # Read session metadata for user,car,track (first 8 lines)
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [next(f).strip() for _ in range(8)]

    for line in lines:
        parts = line.split(",", 1)
        if len(parts) == 2:
            key, value = parts
            session_info[key.strip()] = value.strip()

    # Read telemetry data
    telemetry_df = pd.read_csv(
        csv_path,
        header=8,          # real header line
        low_memory=False   # prevents dtype fragmentation
    )

    # Clean column names
    telemetry_df.columns = [c.strip() for c in telemetry_df.columns]
    # DROP FIRST ROW (fixes nan Error)
    telemetry_df = telemetry_df.iloc[1:].reset_index(drop=True)

    # Convert Type
    for col in telemetry_df.columns:
        # Try numeric conversion
        converted = pd.to_numeric(telemetry_df[col], errors="coerce")

        # If conversion didn't destroy most values, keep it
        non_nan_ratio = converted.notna().mean()

        if non_nan_ratio > 0.7:   # 70% numeric = real numeric column
            telemetry_df[col] = converted
        else:
            # else, keep as string
            telemetry_df[col] = telemetry_df[col].astype(str)

    return session_info, telemetry_df
