import pandas as pd

def clean_csv(csv_path):
    session_info = {}

    # Read top 8 lines manually
    with open(csv_path, "r") as f:
        for i in range(8):
            line = f.readline().strip()
            parts = line.split(",")
            if len(parts) >= 2:
                key = parts[0].strip()
                value = ",".join(parts[1:]).strip()
                session_info[key] = value

    # Read telemetry data starting at line 9
    telemetry_df = pd.read_csv(csv_path, header=8, low_memory=False)

    # Convert numeric columns safely
    for col in telemetry_df.columns:
        telemetry_df[col] = pd.to_numeric(telemetry_df[col], errors='coerce')

    cleaned_info = {
        "Driver": session_info.get("Driver", "Unknown"),
        "Vehicle": session_info.get("Vehicle", "Unknown"),
        "Venue": session_info.get("Venue", "Unknown"),
        "Session": session_info.get("Session", ""),
        "Session Date": session_info.get("Session Date", ""),
        "Session Time": session_info.get("Session Time", ""),
    }

    return cleaned_info, telemetry_df
