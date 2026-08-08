def calculate_lap_timings(telemetry_df):
    """Compute per-lap timing, sector splits, and validity for a session.

    A lap is considered valid only if it passes all three independent
    checks below
      - car remained on-track for entire lap (easily identifiable using the IsOnTrack column in the iracing ibt data)
      - continuously progressing lap distance (ensures no driving backwards which would indicate an on-track spin / tomfoolery, mainly ensuring no on track spin)
      - no extended low-speed anomaly (similar to above, this is to check for a potential spin/error where the car did not leave the track which would pass the on-track check)

    This function returns:
        (lap_timings, best_lap, best_lap_time)
        lap_timings: dict keyed by lap number -> dict of timing/validity data
        best_lap: lap number of the fastest valid, non-pit lap
        best_lap_time: that lap's time in seconds 
    """
    lap_timings = {}

    valid_laps = sorted(telemetry_df[telemetry_df["Lap"] > 0]["Lap"].unique())

    for lap in valid_laps:
        lap_data = telemetry_df[(telemetry_df["Lap"] == lap)].copy()

        if len(lap_data) == 0:
            continue

        lap_data_sorted = lap_data.sort_values("SessionTime")
        is_outlap = lap_data_sorted["OnPitRoad"].iloc[0] == 1
        is_inlap = lap_data_sorted["OnPitRoad"].iloc[-1] == 1

        """ iRacing does not report the lap time of the session's final lap,
            since the cooldown lap never fully completes
            session ticks (60/sec) are used as a fallback instead (usually accurate to +/- .006s).
        """
        lap_time_rows = telemetry_df[
            (telemetry_df["Lap"] == lap + 1) &
            (telemetry_df["LapLastLapTime"] > 0)
        ]["LapLastLapTime"]

        if len(lap_time_rows) > 0:
            lap_time = lap_time_rows.iloc[-1]
        else:
            if len(lap_data) > 1:
                lap_time = (lap_data["SessionTick"].iloc[-1] - lap_data["SessionTick"].iloc[0]) / 60
            else:
                continue

        if lap_time <= 0:
            continue

        is_on_track = (lap_data["IsOnTrack"] == 1).all()

        # Check for distance anomalies (going backwards / off track)
        dist_pct = lap_data_sorted["LapDistPct"].values
        is_monotonic = True
        if len(dist_pct) > 1:
            for i in range(1, len(dist_pct)):
                if dist_pct[i] < dist_pct[i - 1] - 5:
                    is_monotonic = False
                    break

        # Check for extended low-speed anomaly (car stuck below 15km/h, 15 used as initial inference of an adequate value but may be refactored once various vehicle/track combinations have been tested/properly considered)
        speeds = lap_data_sorted["Speed"].values * 3.6
        has_speed_anomaly = False
        if len(speeds) > 10:
            slow_count = (speeds < 15).sum()
            if slow_count > 60:
                has_speed_anomaly = True

        is_valid = is_on_track and is_monotonic and not has_speed_anomaly

        if len(lap_data_sorted) > 0:
            lap_start_time = lap_data_sorted["SessionTime"].iloc[0]
            lap_end_time = lap_data_sorted["SessionTime"].iloc[-1]

            sector1_rows = lap_data_sorted[lap_data_sorted["LapDistPct"] <= 33.33]
            sector1_end_time = sector1_rows["SessionTime"].iloc[-1] if len(sector1_rows) > 0 else lap_start_time

            sector2_rows = lap_data_sorted[lap_data_sorted["LapDistPct"] <= 66.66]
            sector2_end_time = sector2_rows["SessionTime"].iloc[-1] if len(sector2_rows) > 0 else sector1_end_time

            sector1_time = sector1_end_time - lap_start_time
            sector2_time = sector2_end_time - sector1_end_time
            sector3_time = lap_time - (sector1_time + sector2_time)
        else:
            sector1_time = 0
            sector2_time = 0
            sector3_time = 0

        minutes = int(lap_time // 60)
        seconds = int(lap_time % 60)
        millis = int((lap_time - int(lap_time)) * 1000)
        lap_time_str = f"{minutes:02}:{seconds:02}.{millis:03}"

        lap_timings[int(lap)] = {
            'time': lap_time,
            'time_str': lap_time_str,
            'sector1': sector1_time,
            'sector2': sector2_time,
            'sector3': sector3_time,
            'is_valid': is_valid,
            'is_outlap': is_outlap,
            'is_inlap': is_inlap,
        }

    # Drop the final lap due to it being an incomplete cooldown lap, not a real one.
    if len(lap_timings) > 0:
        last_lap = max(lap_timings.keys())
        if last_lap in lap_timings:
            del lap_timings[last_lap]

    valid_lap_times = {
        lap: data['time'] for lap, data in lap_timings.items()
        if data['is_valid'] and data['time'] != float('inf')
        and not data['is_outlap'] and not data['is_inlap']
    }

    if valid_lap_times:
        best_lap = min(valid_lap_times, key=valid_lap_times.get)
        best_lap_time = valid_lap_times[best_lap]
    else:
        best_lap = None
        best_lap_time = None

    if best_lap is not None:
        for lap in lap_timings:
            delta = lap_timings[lap]['time'] - best_lap_time
            lap_timings[lap]['delta'] = delta
            if abs(delta) < 0.001:
                lap_timings[lap]['delta_str'] = "—"
            elif delta > 0:
                lap_timings[lap]['delta_str'] = f"+{delta:.3f}s"
            else:
                lap_timings[lap]['delta_str'] = f"{delta:.3f}s"

    return lap_timings, best_lap, best_lap_time
