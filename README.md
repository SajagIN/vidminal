# 📺 Vidminal: Terminal Video as ASCII Art

### A little sneek peek:
https://github.com/user-attachments/assets/fbd1eaeb-4037-465c-b473-fa1c6f9ca26e

Ever wanted to watch videos as colored ASCII art in your terminal, with sound, and full keyboard controls? Now you can! This project turns any video into a glorious, eye-straining ASCII art experience—right in your terminal, with audio, seeking, and more.

---

## 🚀 How to Run

### 1. Download a Release (Recommended)
- Get the right executable for your OS from the [Releases](https://github.com/sajagin/vidminal/releases) page.
- No Python or dependencies needed. Just run it!
- All required files (including BadApple.mp4 and ffmpeg) are bundled.

### 2. Run from Python Source
- **Python 3.8+** required.
- Install dependencies:
  ```bash
  pip install Pillow moviepy pygame py7zr colorama
  ```
- Run the script:
  ```bash
  python vidminal.py
  ```

---

## 🆕 Playback Controls
- **Space**: Pause/Resume
- **Q**: Quit
- **A/D**: Rewind/Forward 5 seconds
- **←/→ (Arrow keys)**: Skip 1 second

---

## 🍿 Usage
- Run the script or binary. It will prompt for a video file (or use the default BadApple.mp4).
- All settings (width, fps, temp folder) are stored in `options.json` after first run. Edit this file to change defaults.
- The program will extract and use the correct ffmpeg binary for your OS automatically—no setup needed!

---

## ⚙️ Options
- `options.json` is created on first run. You can edit it to set:
  - Video file (default: BadApple.mp4)
  - Temp folder (default: temp)
  - Width (default: 160)
  - FPS (default: 24)
- No more prompts for width, fps, or temp folder—just set and forget!

---

## 🧹 Cleanup
- All temporary files (frames, audio, temp ffmpeg) are deleted automatically when the program exits, even if you quit early or force close.

---

## 📖 How Does It Work?
- See [WORKING.md](./WORKING.md) for a full, beginner-friendly explanation of every part of the code, how ffmpeg works, and how everything fits together.

---

## ⚠️ Known Issues / Notes
- **Terminal Size Matters:** If your terminal is too small, the video will look bad. Make it big!
- **Performance:** It's Python and ASCII. It might stutter on slow machines or huge videos.
- **ffmpeg:** You do NOT need to install ffmpeg yourself. The right binary is extracted and used automatically.
- **Full video path is required (No relative path)**

---

## Contributing
Pull requests and issues are welcome! See the code and [WORKING.md](./WORKING.md) for details.

---

## License
MIT or similar. Use at your own risk. Don't blame me if your terminal melts.

---

## Credits
- Bad Apple!! video for testing
- All the open-source libraries used

---

For a full technical breakdown, see [WORKING.md](./WORKING.md).
