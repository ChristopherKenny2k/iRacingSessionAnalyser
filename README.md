# iRacing Telemetry Analyser
## **[▶️ Video: Showcase & Demo](https://www.youtube.com/watch?v=4drDeOGHRqY)**

**[📥 Download Latest Release](https://github.com/ChristopherKenny2k/iRacingSessionAnalyser/releases/tag/V1.1.0)**


Comprehensive telemetry analysis tool for iRacing sessions. Load your CSV telemetry files and gain deep insights into your driving performance.

## ✨ Features

- **Session Overview** - Environmental data and race-specific data, qualifying-specific data, or practice session-specific data
- **Lap Timing Analysis** - Sector-by-sector breakdown with track map visualization and delta comparisons
- **Pedal Telemetry** - Throttle and brake usage visualization with real-time playback
- **Fuel Management** - Usage tracking, correlation analysis, and consumption patterns
- **Tire Analysis** - Temperature monitoring with lap-by-lap playback and per-tyre heat map visualization
- **Brake Analysis** - Automatic lockup detection with track map plotting
- **G-Force Analysis** - View G-G Diagram aswell as a steering input / lateral Accelleration line graph
- **Data Preview** - Built-in CSV viewer for raw telemetry inspection


## 🚀 Quick Start

### For Users (No coding required!)
1. [Download the latest .exe](https://github.com/ChristopherKenny2k/iRacingSessionAnalyser/releases/tag/V1.1.0)
2. Run `iRacing-Telemetry-Analyzer.exe`
3. Load your iRacing CSV telemetry file (tutorial for csv conversion here → https://youtu.be/9JIT0l2SJ9c)
4. Analyze your performance!

### For Developers
```bash
# Clone the repository
git clone https://github.com/ChristopherKenny2k/iRacingSessionAnalyser.git
cd iRacingSessionAnalyser

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## 🛠️ Tech Stack

- **Python 3.14+**
- **PySide6** - Qt framework for GUI
- **pandas** - Data manipulation and analysis
- **matplotlib** - Telemetry visualization
- **numpy** - Numerical computations
- **pyirsdk** - iRacing SDK integration

## 📊 Screenshots

**Session Overview Screen**
<img width="866" height="798" alt="screenshot6" src="https://github.com/user-attachments/assets/89051d03-0deb-4b0c-afea-619da4711173" />

**Lap Timing Data Screen**
<img width="1698" height="974" alt="screenshot1" src="https://github.com/user-attachments/assets/625396da-0a24-4235-b9ba-12531cfdcf56" />

**Pedal Usage Data Screen**
<img width="1687" height="760" alt="screenshot2" src="https://github.com/user-attachments/assets/2b017797-c868-4c03-8693-ad3f708db602" />

**Fuel Usage Data Screen**
<img width="1687" height="967" alt="screenshot5" src="https://github.com/user-attachments/assets/ef87298f-a4b2-4c95-b219-2aad1467164a" />

**Lock-Up / Braking Analysis Screen**
<img width="1703" height="740" alt="screenshot3" src="https://github.com/user-attachments/assets/ae5f26d3-96e4-472e-b164-1a9d8bac4366" />

**G-Force / Steering Input Analysis Screen**
<img width="1702" height="833" alt="screenshot9" src="https://github.com/user-attachments/assets/d4a30910-3f7a-4eae-b557-3724ba26ac31" />



## 📝 License

This project is open source, if anything here is used in any future commercial or open source project, acknowledgements would be appreciated but are not neccessary.

## 🏁 Acknowledgments

Built for the iRacing community by an avid sim-racer, for sim racers.
