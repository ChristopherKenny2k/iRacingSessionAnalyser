import os
import csv
from irsdk import IRSDK

def ibt_to_csv(ibt_path):
    if not os.path.exists(ibt_path):
        raise FileNotFoundError(f"IBT file not found: {ibt_path}")

    ir = IRSDK()
    ir.startup(ibt_path)  # Load IBT file
    print("IBT loaded successfully")

    # Get all variable names from the first frame
    ir.startup(ibt_path)
    ir.freeze_var_buffer_behind()
    ir.tick()  # Load first frame

    variables = list(ir.varnames)  # Correct way to get all telemetry variable names
    print(f"Telemetry variables found: {len(variables)}")

    csv_path = os.path.splitext(ibt_path)[0] + ".csv"
    print(f"Writing CSV to: {csv_path}")

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(variables)

        frame_count = 0
        while ir.tick() is not None:
            row = [ir[var] for var in variables]
            writer.writerow(row)
            frame_count += 1

    print(f"CSV created: {csv_path}, frames: {frame_count}")
    ir.shutdown()
    return csv_path

# Example usage
if __name__ == "__main__":
    ibt_file = "[Initial]LOW.ibt"  # replace with your file
    ibt_to_csv(ibt_file)
