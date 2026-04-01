# 📖 User Guide - iRacing Telemetry Analyser

## * *This application requires a .ibt to .csv converter* * #
## * *I recommend Mu Downloadable Here ---> **[Mu](https://github.com/patrickmoore/Mu)**

## Once installed watch the following video tutorial on converting .ibt to .csv and loading into iRacing Telemetry Analyser
## 📹 Video Tutorial
**[▶️ Watch the Full Tutorial on YouTube](https://www.youtube.com/watch?v=YOUR_VIDEO_ID)**

---

## 🚀 Quick Start

### Step 1: Download the Application
1. Go to the [Releases page]**(https://github.com/ChristopherKenny2k/iRacingSessionAnalyser/releases)**
2. Download `iRacing-Telemetry-Analyser.exe`
3. Save it to your preferred location

### Step 2: Convert your iRacing session .ibt to .csv using Mu
1. Locate your desired session telemetry (\Documents\iRacing\telemetry)
2. Place file in separate folder (Not neccessary but useful if telemetry file has a lot of recorded sessions)
3. Use Mu to convert .ibt to .csv  
    ↳ <ins>Mu Settings (Crucial) </ins> 
         - Exporter = Csv  
         - Units = Metric  
         - Import Directory = file location mentioned in .2 (if none made, then Documents\iRacing\Telemetry)
         - Export Directory = desired location   
         - Export Lap Threshol = 0  
         - Remove iRacing Telemetry = Never  
         - Show Settings on Startup = On  
         - Save Current Setup = Off  

### Step 3: Load Your Data
1. Double-click `iRacing-Telemetry-Analyser.exe` to launch
2. Click **"Browse"** and select your CSV file / Drag and drop your CSV file
3. Choose your session type:
   - 🏋️ **Practice** - Practice/Test sessions
   - ⏱️ **Qualifying** - Qualifying sessions
   - 🏁 **Race** - Full race analysis
4. Click **"Continue"**

---

## 📊 Feature Breakdown

### 🏁 Session Overview
**What it shows:**
- Overall session statistics specific to session type
- Weather conditions and track information

---

### ⏱️ Timing Data
**What it shows:**
- Lap-by-lap timing breakdown with sector splits
- Delta to your personal best lap
- Color-coded lap indicators:
  - 🟡 **Yellow** = In-lap (entering pits)
  - 🔵 **Blue** = Out-lap (exiting pits)
  - 🟢 **Green** = Your fastest lap
  - ⚪ **White** = Normal lap
  - Overview Statistics Bar with lap consistency and performance score

---

### 🦶 Pedal Usage Data
**What it shows:**
- Throttle and brake input graphs per lap
- Real-time playback of your pedal inputs
- Coasting detection

**How to use:**
1. Select a lap from the timeline
2. Click play to watch your pedal inputs
3. Look for:
   - Smooth throttle application (gradual curves)
   - Quick but controlled braking (sharp but not jerky)
   - Minimal input oscillation   

---

### 🔥 Lock-up Data
**What it shows:**
- Automatic tyre lockup detection
- Track map with lockup locations marked
- Per-wheel lockup analysis (LF, RF, LR, RR)
- Lockup duration and maximum temperature

**How to use:**
1. View the track map to see WHERE you're locking up
2. Use the wheel filter buttons to check specific corners
3. Click on a lockup in the table to highlight it on the map
4. Or vice-versa, double click a lockup on the track map to highlight it in the table
5. Review brake pressure % to understand how hard you were braking

**Pro Tip:** Repeated lockups in the same corner? Try braking earlier or adjusting brake bias!

---

### 🛞 Tyre Data
**What it shows:**
- Temperature monitoring for all four tyres
- Lap-by-lap temperature playback
- Heat distribution across tyre surface sections (Left, Middle, Right)
- Per-Lap playback with tyre display to see typre temperatures over each lap
- Correlation chart between Lap Time and Tyre Temperature

**How to use:**
1. Select a lap to view tyre temps
2. Press play to begin playback, option to speed up playback if desired
3. Look for temperature imbalances:
   - Too hot = sliding/overdriving
   - Too cold = not enough load/speed
   - Uneven temps = alignment or camber issues
   - Front/Wheel temperature imbalance in braking sections = potential brake bias change 

---

### ⛽ Fuel Usage Data
**What it shows:**
- Fuel consumption per lap (bar chart)
- Fuel load vs. lap time correlation (scatter plot)
- Average fuel usage statistics
- Full fuel level line chart over session, extremeley useful if practicing for an upcoming endurance event to calculate optimal refuelling strategies

**How to use:**
1. Click on bars to select specific laps
2. Review the correlation plot
3. Use average consumption to plan pit strategies

**Pro Tip:** IN and OUT laps are excluded from correlation analysis for accuracy!

---

### 📋 Data Previewer
**What it shows:**
- Raw CSV telemetry data viewer
- First 200 rows of your data
- All columns from iRacing export

**How to use:**
- Verify your data loaded correctly
- Check for any anomalies or missing data
- Inspect specific telemetry values
- Useful window to get a glimpse into the raw data, as opening the full csv file can be difficult under normal circumstances due to its high dimensionality

---

## 💡 Tips for Better Analysis

### Understanding Valid vs Invalid Laps
**Valid laps:**
- ✅ Car stayed on track
- ✅ No major speed anomalies
- ✅ Complete telemetry data

**Invalid laps (grayed out):**
- ❌ Went off track
- ❌ Incomplete data

### Color Code Reference
| Color | Meaning |
|-------|---------|
| 🟡 Yellow | In-lap (entering pits) |
| 🔵 Blue | Out-lap (exiting pits) |
| 🟢 Green | Your fastest lap |
| ⚪ White | Normal lap |

### Making the Most of Your Data
1. **Start with Session Overview** - Get the big picture
2. **Review Timing Data** - Find your fastest sectors
3. **Check Lockup Data** - Identify braking issues
4. **Analyze Pedal Inputs** - Smooth = fast
5. **Monitor Tyre Temps** - Balance is key
6. **Plan Fuel Strategy** - Know your consumption, plan for future pitting and refuelling strategies

---

## ❓ Frequently Asked Questions

**Q: What file format does the app accept?**  
A: CSV files directly converted from iRacing .ibt session data.

**Q: Why are some of my laps marked invalid?**  
A: Laps are invalid if you went off track, had major speed drops, or data is incomplete.

**Q: Can I analyze multiple sessions at once?**  
A: Not currently - load one CSV file at a time, future plans to implement session comparison between two sessions.

**Q: How do I export telemetry from iRacing?**  
A: Check my .ibt to .csv converting tutorial using Mu HERE

**Q: The app won't open - what do I do?**  
A: Some antivirus software flags unknown .exe files. Add it to your exceptions or download from official releases only.

**Q: Can I use this for league racing?**  
A: Absolutely! Perfect for reviewing race performance and finding improvements.

---

## 🐛 Troubleshooting

### App Won't Launch
- **Check:** Windows Defender or antivirus blocking it
- **Fix:** Add exception or download from official GitHub releases

### CSV Won't Load
- **Check:** File has been converted from .ibt to .csv and has remained unaltered
- **Fix:** Re-export from iRacing, ensure file isn't corrupted or altered in any way

### Missing Data/Features
- **Check:** CSV contains all required columns
- **Fix:** Use complete telemetry export, not partial data

### Performance Issues
- **Check:** Available RAM and CPU usage
- **Fix:** Close other applications, analyze shorter sessions

---

## 📞 Need Help?

- 🐛 **Bug Reports:** [Open an issue](https://github.com/ChristopherKenny2k/iRacingSessionAnalyser/issues)
- 💡 **Feature Requests:** [Submit a suggestion](https://github.com/ChristopherKenny2k/iRacingSessionAnalyser/issues)
- 📧 **Contact:** email - christopherkenny16@gmail.com

---

**Happy Racing! 🏁**

*Made by an avid sim racer for the iRacing community*