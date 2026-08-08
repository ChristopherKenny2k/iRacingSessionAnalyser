def detect_all_lockups(telemetry_df):
    """Detect wheel lockup events across a session.

    iracing's ibt data does not have any lockup detection included

    therefore I manually created a check for lockups by comparing vehicle velocity to each individual tyres rotational speed
    by doing this, lockups become easily detectable

    Consecutive flagged samples (within GAP_THRESHOLD ticks of each other)
    are grouped into a single discrete event rather than counted
    individually, since one real lockup produces many consecutive flagged
    rows at 60Hz sampling.

    Returns a dict keyed by wheel name ('LF', 'RF', 'LR', 'RR') -> list of grouped lockup events
    """
    MIN_WHEEL_SPEED = 0.5   # m/s
    MIN_GPS_SPEED = 20      # m/s
    GAP_THRESHOLD = 5       # ticks
    MIN_DURATION = 0.01     # seconds

    all_lockups = {'LF': [], 'RF': [], 'LR': [], 'RR': []}

    temp_cols_surface = {
        'LF': ['LFtempL', 'LFtempM', 'LFtempR'],
        'RF': ['RFtempL', 'RFtempM', 'RFtempR'],
        'LR': ['LRtempL', 'LRtempM', 'LRtempR'],
        'RR': ['RRtempL', 'RRtempM', 'RRtempR'],
    }

    for _, row in telemetry_df.iterrows():
        lap_num = row['Lap']
        if lap_num <= 0:
            continue

        speed = row['Speed']
        if speed < MIN_GPS_SPEED:
            continue

        idx = row.name

        wheels = {
            'LF': row['LFspeed'],
            'RF': row['RFspeed'],
            'LR': row['LRspeed'],
            'RR': row['RRspeed'],
        }

        for wheel_name, wheel_speed in wheels.items():
            if wheel_speed < MIN_WHEEL_SPEED:
                start_idx = max(0, idx - 5)
                end_idx = min(len(telemetry_df), idx + 5)
                window = telemetry_df.iloc[start_idx:end_idx]

                max_temp = window[temp_cols_surface[wheel_name]].max().max()

                lockup_data = {
                    'idx': idx,
                    'lap': int(lap_num),
                    'wheel': wheel_name,
                    'lon': row['Lon'],
                    'lat': row['Lat'],
                    'speed': speed * 3.6,
                    'brake': row['Brake'],
                    'max_temp': max_temp,
                }
                all_lockups[wheel_name].append(lockup_data)

    # consecutive flagged samples are grouped with the midpoint sample of each group for location of the lockup
    for wheel_name in all_lockups:
        if not all_lockups[wheel_name]:
            continue

        grouped = []
        current_group = [all_lockups[wheel_name][0]]

        for i in range(1, len(all_lockups[wheel_name])):
            if all_lockups[wheel_name][i]['idx'] - current_group[-1]['idx'] <= GAP_THRESHOLD:
                current_group.append(all_lockups[wheel_name][i])
            else:
                first_tick = telemetry_df.iloc[current_group[0]['idx']]['SessionTick']
                last_tick = telemetry_df.iloc[current_group[-1]['idx']]['SessionTick']
                duration = (last_tick - first_tick) / 60

                if duration >= MIN_DURATION:
                    mid_idx = len(current_group) // 2
                    middle_event = current_group[mid_idx].copy()
                    middle_event['duration'] = duration
                    grouped.append(middle_event)

                current_group = [all_lockups[wheel_name][i]]

        if current_group:
            first_tick = telemetry_df.iloc[current_group[0]['idx']]['SessionTick']
            last_tick = telemetry_df.iloc[current_group[-1]['idx']]['SessionTick']
            duration = (last_tick - first_tick) / 60

            if duration >= MIN_DURATION:
                mid_idx = len(current_group) // 2
                middle_event = current_group[mid_idx].copy()
                middle_event['duration'] = duration
                grouped.append(middle_event)

        all_lockups[wheel_name] = grouped

    return all_lockups
