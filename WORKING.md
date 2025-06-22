# WORKING.md

## How This Project Works (For Total Beginners)

This document explains every part of the code and the tools it uses, so you can understand how it all fits together—even if you're new to Python, ffmpeg, or terminal video!

---

## What does this project do?

This is a terminal-based Python program that:
- Takes a video file (like an mp4)
- Converts it into ASCII art frames (text pictures)
- Plays the video as colored ASCII art in your terminal
- Plays the audio in sync
- Lets you pause, quit, and seek (rewind/forward)
- Cleans up after itself

---

## Key Concepts & Tools

### 1. ffmpeg
- **What is it?**
  - ffmpeg is a command-line tool for processing video and audio files. It can convert, extract, and manipulate media.
- **How do we use it?**
  - The code uses ffmpeg (via the `moviepy` library) to extract audio and frames from the video file.
  - The ffmpeg binary is bundled in a compressed archive (7z) for each OS (Windows, Mac, Linux).
  - The code extracts the right ffmpeg binary at runtime and sets an environment variable so `moviepy` can find and use it.

### 2. moviepy
- **What is it?**
  - A Python library that makes it easy to work with video files. It uses ffmpeg under the hood.
- **How do we use it?**
  - To open the video, extract audio, and get each frame as an image.

### 3. pygame
- **What is it?**
  - A Python library for making games, but here it's used just for playing audio.
- **How do we use it?**
  - To play, pause, and stop the audio in sync with the video.

### 4. PIL (Pillow)
- **What is it?**
  - A Python library for image processing.
- **How do we use it?**
  - To resize video frames and convert them to ASCII art.

### 5. colorama
- **What is it?**
  - A Python library for colored terminal output.
- **How do we use it?**
  - To color the ASCII art frames.

### 6. py7zr
- **What is it?**
  - A Python library to extract 7z (7-zip) archives.
- **How do we use it?**
  - To extract the ffmpeg binary from the right archive for your OS.

---

## How the Code Works (Line by Line)

### Imports
- The code imports a lot of modules. Each one is used for a specific job:
  - `os`, `sys`: File and system operations
  - `warnings`: Suppress annoying warnings
  - `contextlib`, `io`: For redirecting output and managing resources
  - `shutil`, `atexit`: For deleting temp files/folders and cleaning up
  - `time`, `threading`, `multiprocessing`: For timing, running things in parallel, and speed
  - `platform`: To detect your OS
  - `pygame`, `moviepy`, `py7zr`, `PIL`, `colorama`, `json`, `tempfile`, `queue`: See above

### SuppressStderr
- A class to silence all error output (so the terminal isn't spammed by ffmpeg/moviepy warnings).

### with SuppressStderr():
- All the heavy imports are done inside this block so their warnings are hidden.

### cleanup_temp_folder(temp_path)
- Deletes the temp folder and all its contents. Used to clean up after the program runs.

### find_resource_path(rel)
- Figures out where to find files (like ffmpeg or the default video) whether running normally or as a bundled executable.

### managed_ffmpeg()
- Context manager that:
  - Extracts the right ffmpeg binary for your OS from a 7z archive
  - Sets the `FFMPEG_BINARY` environment variable so moviepy uses it
  - Cleans up the temp ffmpeg file after

### get_stuff_from_video(vid, out, speed, wide)
- Converts the video to audio and image frames:
  - Extracts audio to an .ogg file
  - Extracts each frame as a PNG image, resized for ASCII art
  - Converts each frame to ASCII art (in parallel for speed)
  - Saves ASCII frames as .txt files

### load_options(options_path)
- Loads settings (like width, fps, temp folder) from `options.json`, or creates it with defaults if missing.

### pic_to_ascii_from_pil(pic, wide, high)
- Converts a PIL image to a string of colored ASCII art.
- Handles resizing, gamma/contrast, and color mapping.

### pic_to_ascii(img, wide, high)
- Opens an image file and calls `pic_to_ascii_from_pil`.

### convert_frame_to_ascii(args)
- Helper for multiprocessing: converts a frame image to ASCII art.

### play_sound(audio, pause_flag, stop_flag)
- Plays audio using pygame, with support for pause and stop.

### getch()
- Reads a single keypress from the user, non-blocking, works on Windows and Unix.

### clear_terminal()
- Clears the terminal screen (Windows or Unix).

### play_ascii_video_stream(...)
- Plays pre-rendered ASCII frames and audio in sync.
- Handles pause, quit, and keyboard controls.

### get_stuff_from_video_stream(...)
- Like `get_stuff_from_video`, but streams frames as they're extracted (for big videos).

### play_ascii_video_stream_streaming(...)
- The main playback loop for streaming mode:
  - Buffers frames
  - Handles keyboard controls (pause, quit, seek)
  - Keeps audio and video in sync
  - Only clears the terminal when needed (for performance)
  - Draws a seek bar and time display

### pic_from_ascii_txt(txt_path)
- Reads an ASCII art frame from a .txt file.

### main()
- The main entry point:
  - Shows a fancy intro box
  - Loads options
  - Gets the video file (from command line or prompt)
  - Calls the video extraction and playback functions
  - Handles errors and cleanup

### if __name__ == '__main__':
- Sets up signal handlers for cleanup
- Runs the main program loop
- Ensures temp files are always deleted, even if you Ctrl+C or close the terminal

---

## How does ffmpeg actually work here?
- ffmpeg is a separate program (not Python!) that can read and convert video/audio files.
- `moviepy` calls ffmpeg behind the scenes to:
  - Extract the audio track from the video
  - Extract each video frame as an image
- The code makes sure the right ffmpeg binary is available and tells moviepy where to find it.

---

## How does the ASCII art work?
- Each video frame is resized to fit the terminal
- Each pixel is converted to a colored ASCII character (darker = denser character)
- The result is a string of text with ANSI color codes, printed to the terminal

---

## How does the audio stay in sync?
- The code calculates how long each frame should be shown (based on fps)
- It starts the audio and video at the same time
- If you pause, both audio and video pause
- If you seek, both jump to the new position

---

## How do the controls work?
- Space: Pause/Unpause
- Q: Quit
- A/D: Rewind/Forward 5 seconds
- Arrow keys: Fine seek (left/right)

---

## How does cleanup work?
- The temp folder (with frames/audio) is deleted when the program exits, even if you quit early or force close.
- The ffmpeg binary is also deleted from temp after use.

---

## What if something breaks?
- The code tries to catch errors and print a message.
- If you see 'Nope, broke: ...', something went wrong (bad video, missing ffmpeg, etc).
- Check your video file, options.json, and that you have the right dependencies installed.

---

## Want to learn more?
- Look up the docs for: [ffmpeg](https://ffmpeg.org/), [moviepy](https://zulko.github.io/moviepy/), [pygame](https://www.pygame.org/docs/), [Pillow](https://pillow.readthedocs.io/en/stable/), [colorama](https://pypi.org/project/colorama/), [py7zr](https://pypi.org/project/py7zr/)
- Try changing the options in `options.json` (like width, fps, chars) and see what happens!

---

## TL;DR
- This code takes a video, turns it into colored ASCII art, and plays it in your terminal with sound.
- It uses ffmpeg (via moviepy) to extract frames/audio, Pillow to process images, colorama for color, pygame for sound, and a bunch of Python magic to keep it all in sync and clean up after itself.
- You can pause, quit, and seek. It works on Windows, Mac, and Linux.

Enjoy!
