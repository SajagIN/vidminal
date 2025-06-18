# 📺 Vidminal: 'Cause Who Needs Graphics Anyway? 🤷‍♀️
Ever wanted to watch videos but, like, without all those fancy pixels? Just good ol' text? And maybe with sound too? No? Well, too bad, 'cause this thing does it! 🙄

It's a super "optimized" tool that turns any video into a glorious, eye-straining ASCII art experience right in your terminal. Plus, it plays the audio. Because even a lazy developer knows you can't just have silent movies. 😴

## 🚀 How to Get This Masterpiece Running
 - Prerequisites (Stuff You Probably Already Have, Hopefully)
 - **Python**: 'Cause that's what this is written in. Duh.

 - **FFmpeg**: This is the real MVP here. It rips out frames and audio. Go get it if you don't have it. Seriously, this project is useless without it.

   - *Windows*: Just google "ffmpeg download" or use `Scoop` or `Chocolatey`. PS: I used `winget`, it works too.

   - *macOS*: `brew install ffmpeg` (if you have Homebrew, which you should).

   - *Linux*: `sudo apt install ffmpeg` or whatever your distro uses.

 - **Pillow**: For image magic.`pip install Pillow`

Installation (If You Can Even Call It That)
Clone this repo (or just copy-paste the code, I don't care):

```bash
git clone https://github.com/sajagin/vidminal.git
cd vidminal
```
## 🍿 Usage: "Watch" a Video
Just point it to your video file, and let the magic (or lack thereof) happen. ✨
```bash
python vidminal.py /path/to/your/video.mp4
```
### Options (If You're Feeling Fancy)
You can pass these command-line arguments to change how things work:

 - --temp <directory>: Sets a temporary directory for all the extracted frames and audio. Defaults to temp/.

Example: `python vidminal.py video.mp4 --temp my_temp_files`

 - --width <number>: Controls how wide your ASCII art will be. Fewer characters means crappier resolution, but faster processing. Defaults to 80.

Example: `python vidminal.py video.mp4 --width 120`

 - --fps <number>: Sets the frames per second for extraction and playback. Lower means choppier but less work for your CPU. Defaults to 24.

Example: `python vidminal.py video.mp4 --fps 15`

### ⚠️ Known Issues / "Features"
 - Terminal Size Matters: If your terminal is too small, things will look like a jumbled mess. Make it big! Or don't, I'm not your boss.

 - Performance: It's Python. It's ASCII. It might stutter. Don't come crying to me.

 - FFmpeg/FFplay: Relies heavily on these. If they're not set up right, nothing works. Period.

 - Temporary Files: It creates a bunch of image files and an audio file. It doesn't clean them up automatically. Why? **Because I'm lazy. Delete them yourself!** 🔥🗑️

## Contributing (LOL)
Sure, if you really wanna make this "better," feel free. But honestly, it works, right? So why bother? Issues and pull requests are technically welcome, I guess. 🙄

# License
This project is probably under some open-source license. Just assume you can do whatever with it, but don't blame me if it breaks your computer. Or your eyes. 😜



#### PS: It's fun sometimes written a README from hand without any tool. 😆
#### added `BadApple.mp4` in repo for testing.