# Screen Recording Guide

This guide provides instructions for creating the required unedited screen recording of the Face ID + Blockchain Pipeline.

## Requirements

- **Duration:** Full end-to-end pipeline execution (typically 2-3 minutes)
- **Format:** Video (MP4, MOV, or WebM)
- **Editing:** Unedited - no cuts, effects, or transitions
- **Audio:** Recommended to include system audio or commentary

## Recording Setup (Recommended Tools)

### macOS
- **QuickTime Player** (built-in, free)
- **OBS Studio** (free, advanced)
- **ScreenFlow** (paid, $99)

### Windows
- **OBS Studio** (free)
- **Windows 10/11 Game Bar** (built-in, free)
- **Camtasia** (paid, $99)

### Linux
- **OBS Studio** (free)
- **SimpleScreenRecorder** (free)

## Step-by-Step Recording Instructions

### Using QuickTime (macOS - Easiest)

1. **Open QuickTime Player**
   - Applications → Utilities → QuickTime Player

2. **Start Recording**
   - File → New Screen Recording
   - Click the red "Record" button
   - Select area to record (select full screen)
   - Click "Start Recording"

3. **Run Pipeline**
   ```bash
   cd /path/to/face-id-blockchain
   source venv/bin/activate
   python demo.py
   ```
   Or for full pipeline:
   ```bash
   python pipeline.py --image sample_images/test_face.jpg --demo
   ```

4. **Stop Recording**
   - Click the stop icon in menu bar
   - File → Save (or press Cmd+S)
   - Choose location and format

5. **Export**
   - File → Export As
   - Format: MP4 or MOV
   - Quality: 1080p recommended

### Using OBS Studio (Cross-Platform)

1. **Install OBS Studio**
   - Download from https://obsproject.com
   - Install and launch

2. **Configure**
   - Scene: Add "Display Capture"
   - Audio: Enable microphone if desired
   - Output: Video folder

3. **Record**
   - Click "Start Recording"
   - Run pipeline commands
   - Click "Stop Recording"

4. **File Location**
   - File → Settings → Output → Recording Path
   - Videos saved automatically

## What to Record

### Option 1: Demo Script (Recommended)
This shows the complete pipeline with professional formatting:

```bash
# Run demo (shows all steps with nice formatting)
python demo.py
```

**Duration:** ~2 minutes  
**Shows:** Face detection → Image search → Blockchain record → Output  
**Advantage:** Educational, complete, formatted output

### Option 2: Full Pipeline with Real Mock Data
```bash
# Run full pipeline with demo mode (no APIs needed)
python pipeline.py --image sample_images/test_face.jpg --demo
```

**Duration:** ~30 seconds  
**Shows:** Actual pipeline execution and result output  
**Advantage:** Realistic, shows real code execution

### Option 3: Pipeline with Debug Output
```bash
# Run with verbose debugging (shows all internals)
python pipeline.py --image sample_images/test_face.jpg --demo --debug
```

**Duration:** ~1-2 minutes  
**Shows:** All system logging and internal steps  
**Advantage:** Comprehensive, educational

## Recommended Recording

### Best Option: Combine Both

**Part 1: Demo Script (~2 min)**
```bash
python demo.py
```
Shows:
- Step-by-step process
- Face detection results
- Image search simulation
- Blockchain recording
- JSON output format

**Part 2: Pipeline Execution (~30 sec)**
```bash
python pipeline.py --image sample_images/test_face.jpg --demo
```
Shows:
- Actual CLI tool
- Real output generation
- Results saved to file

**Total Recording:** ~2.5-3 minutes  
**File Size:** ~50-200 MB (depending on resolution)

## Recording Checklist

Before recording, ensure:

- [ ] Terminal window is visible and readable
- [ ] Font size is large enough (14pt+ recommended)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Sample image exists (`sample_images/test_face.jpg`)
- [ ] Virtual environment activated
- [ ] No errors when running locally
- [ ] Microphone works (if including audio)

## Terminal Setup for Recording

### Make Terminal More Visible

1. **Increase Font Size**
   ```bash
   # macOS Terminal
   Terminal → Preferences → Profiles → Font → Size: 14+
   
   # Linux/Windows Terminal
   Settings → Appearance → Font size: 14+
   ```

2. **Use Light Theme** (easier to read)
   - Terminal → Preferences → Profiles → Light theme

3. **Maximize Terminal Window**
   - Full screen or large window
   - Clear clutter

### Sample Terminal Commands Before Recording

```bash
# Navigate to project
cd /path/to/face-id-blockchain

# Activate environment
source venv/bin/activate

# Show Python version (verify setup)
python --version

# Show project files
ls -la

# Run demo or pipeline
python demo.py
# or
python pipeline.py --image sample_images/test_face.jpg --demo
```

## Recording Tips

### Do's
- ✓ Keep screen visible and clear
- ✓ Use readable font size (14pt+)
- ✓ Record in high resolution (1080p+)
- ✓ Include all output/results in video
- ✓ Speak clearly (if adding audio)
- ✓ Keep video continuous (unedited)

### Don'ts
- ✗ Don't edit the video
- ✗ Don't add transitions or effects
- ✗ Don't remove any segments
- ✗ Don't pause and resume
- ✗ Don't speed up or slow down
- ✗ Don't add background music

## File Format & Export

### Recommended Settings
- **Format:** MP4 (H.264)
- **Resolution:** 1920x1080 (1080p)
- **Frame Rate:** 30fps or 60fps
- **Bitrate:** 5000-8000 kbps
- **Audio Codec:** AAC

### File Size Estimates
- 2-minute video @ 1080p: ~50-100 MB
- 3-minute video @ 1080p: ~75-150 MB

## Uploading Video

### To GitHub
1. Create release on GitHub
2. Upload video file to release (max 2GB)
3. Or host on external service:
   - YouTube (private link)
   - Google Drive
   - Dropbox
   - Any file hosting service

### Video Hosting Link Example
Include in README or submission:
```markdown
**Screen Recording:** [YouTube Link](https://youtu.be/...)
or
**Video Demo:** [Download MP4](link-to-video.mp4)
```

## Troubleshooting Recording

### "Permission denied" when saving
- Check folder permissions
- Try recording to Documents folder

### "Recording won't start"
- Restart OBS or QuickTime
- Check screen recording permission (System Preferences)

### "Poor quality / pixelated"
- Increase resolution to 1080p
- Reduce screen clutter
- Use newer recording tool

### "Audio is muted"
- Check system audio isn't muted
- In OBS: verify audio inputs configured
- In QuickTime: might not have audio option

## Sample Recording Narration (Optional)

If adding audio commentary, here's a script:

```
"Welcome to the Face ID + Blockchain Verification Pipeline demo.

This tool detects faces in images, finds matching social media posts,
and records verification on the Ethereum blockchain.

We'll start by running the demonstration script, which will walk through
all three main components:

First, face detection using OpenCV edge detection algorithms.
The system will detect faces and generate a 512-dimensional encoding.

Next, reverse image search to find matching social media posts.

Finally, the verification is recorded on the Ethereum blockchain,
creating a tamper-evident record.

Let's run the demo now."
```

## Next Steps After Recording

1. **Export video** to MP4 format
2. **Test playback** to ensure quality
3. **Upload to GitHub** (release or file)
4. **Add link to README.md**
5. **Commit and push** to repository
6. **Include link in submission**

## Submission Checklist

- [ ] Screen recording created (unedited)
- [ ] Video is 2-3 minutes long
- [ ] Shows complete pipeline execution
- [ ] Clear and readable terminal output
- [ ] Video quality is acceptable (720p+)
- [ ] File format is MP4 or similar
- [ ] Video uploaded and accessible
- [ ] Link added to README or submission
- [ ] All source code on GitHub
- [ ] Documentation complete

---

**Good luck with your recording! 🎬**

For questions or issues, refer to the main README.md or SETUP_GUIDE.md.
