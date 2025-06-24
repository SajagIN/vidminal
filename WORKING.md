# WORKING.md

## How This Project Works (For Total Beginners)
This document explains every part of the code and the tools it uses, so you can understand how it all fits together—even if you're new to Python, ffmpeg, or terminal video! It covers each function, complex algorithm, and the overall architecture.

---

## What does this project do?
This is a terminal-based Python program that:
- Takes a video file (like an mp4).
- **Optimizes:** If the video is higher than 144p, it automatically downscales it to 144p for faster processing.
- **Converts:** Extracts video frames as images and converts them into colored ASCII art (text pictures) *on the fly* during playback.
- **Plays:** Displays the ASCII video in your terminal, dynamically adapting to your terminal's size.
- **Synchronizes:** Plays the audio in sync with the video.
- **Controls:** Lets you pause, quit, seek (rewind/forward), and control volume/mute.
- **Cleans Up:** Automatically deletes all temporary files after use.

---

## Key Concepts & Tools

### 1. ffmpeg
- **What is it?**
  - ffmpeg is a command-line tool for processing video and audio files. It can convert, extract, and manipulate media.
- **How it's used here:**
  - The code uses `ffmpeg` (often via the `moviepy` library, but sometimes directly via `subprocess`) to:
    - Extract audio from the video file.
    - Extract individual video frames as image files (PNGs).
    - **Downscale** the video to 144p if the original resolution is higher.
  - The ffmpeg binary is bundled in a compressed archive (7z) for each OS (Windows, Mac, Linux).
  - The code extracts the right ffmpeg binary at runtime and sets an environment variable so `moviepy` can find and use it.

### 2. moviepy
- **What is it?**
  - A Python library that makes it easy to work with video files. It uses ffmpeg under the hood.
- **How it's used here:**
  - To open the video file (`VideoFileClip`).
  - To extract the audio track (`clip.audio.write_audiofile`).
  - To iterate through video frames (`clip.iter_frames`).
  - To perform video resizing (e.g., `clip.resize`) for the 144p downscaling.

### 3. pygame
- **What is it?**
  - A Python library for making games, but here it's used just for playing audio.
- **How do we use it?**
  - To play, pause, stop, and control the volume/mute of the audio in sync with the video.

### 4. PIL (Pillow)
- **What is it?** A powerful Python Imaging Library (PIL) fork for image processing.
- **How it's used here:**
  - To load video frames (which are raw pixel data) into `Image` objects.
  - To convert images to grayscale (`convert('L')`) and RGB (`convert('RGB')`).
  - To resize images (`resize`) to fit the terminal dimensions.
  - To extract pixel data (`getdata()`) for ASCII conversion.

### 5. colorama
- **What is it?** A Python library to make ANSI escape sequences (for colors and cursor movement) work on all terminals, including Windows.
- **How it's used here:**
  - To add foreground colors (`Fore`), background colors (`Back`), and text styles (`Style`) to the terminal output.
  - Used for the ASCII art colors and the UI elements.

### 6. py7zr
- **What is it?** A Python library to extract 7z (7-zip) archives.
- **How it's used here:**
  - To decompress the bundled `ffmpeg` binaries from their `.7z` archives.

### 7. threading
- **What is it?** Python's module for running multiple parts of a program concurrently within the same process. Useful for I/O-bound tasks.
- **How it's used here:**
  - For the `keyboard_listener` to read user input without blocking the main video playback.
  - For the `extract_frames_worker` to extract video frames in the background while the main loop plays.

### 8. multiprocessing
- **What is it?** Python's module for running multiple parts of a program in separate processes. Useful for CPU-bound tasks, as it bypasses Python's Global Interpreter Lock (GIL).
- **How it's used here:**
  - Primarily for `multiprocessing.freeze_support()`, which is crucial for `multiprocessing` to work correctly when the script is bundled into an executable on Windows.

---

## How the Code Works (Overview)

- Imports all needed modules for video/audio/image processing, terminal control, and cross-platform compatibility.
- Extracts and sets up ffmpeg for your OS.
- Loads user options from `options.json` (or creates it with defaults).
- Checks the video resolution:
  - If the video is higher than 144p, it's downscaled to 144p using `ffmpeg` and saved to a temporary file. This smaller video then becomes the source.
  - If the video is 144p or lower, the original video is used directly.
- **Background Extraction:** A separate thread extracts audio and saves video frames as temporary PNG image files.
- **On-the-Fly Conversion & Display:** The main playback loop reads these PNGs, converts them to ASCII art *just before displaying*, dynamically adjusting to the current terminal size.
- **Synchronized Playback:** Audio plays in sync with the ASCII video.
- **Interactive Controls:** A `keyboard_listener` thread handles user input for pause/play, quit, seeking, and volume/mute.
- **Dynamic UI:** A single-line seekbar is displayed, adapting to the terminal width, showing play/pause status, current time, total time, and a visual volume/mute indicator.
- **Cleanup:** All temporary files (PNGs, audio, downscaled video, extracted `ffmpeg`) are automatically deleted upon exit.

---

## Detailed Function Explanations

This section explains every function in `vidminal.py` and its role in the overall system.

### `cleanup_temp_folder(temp_path)`
- **Purpose:** Deletes the specified temporary folder and all its contents.
- **How it works:** It checks if the `temp_path` exists and is a directory, then uses `shutil.rmtree` to remove it. A `try-except` block is used to gracefully handle any errors during deletion (e.g., if files are still in use).
- **Called by:** `atexit.register` (to ensure cleanup on program exit) and `main()` (for explicit cleanup after playback or errors).

### `find_resource_path(rel)`
- **Purpose:** Helps locate bundled files (like `ffmpeg` archives or the default `BadApple.mp4`) whether the script is run directly or as a PyInstaller-generated executable.
- **How it works:** When run as an executable, PyInstaller sets `sys._MEIPASS` to the path of the temporary folder where bundled files are extracted. Otherwise, it assumes files are relative to the script's current directory.
- **Called by:** `managed_ffmpeg()` and `main()`.

### `managed_ffmpeg()`
- **Purpose:** A Python `context manager` that ensures the correct `ffmpeg` binary is available for `moviepy` and `subprocess` calls, and cleans it up afterward.
- **How it works:**
  1.  **Detects OS & Architecture:** Determines if the system is Windows, macOS, or Linux (and its specific ARM/x64 architecture).
  2.  **Locates Bundled `ffmpeg`:** Uses `find_resource_path` to find the correct `.7z` archive containing the `ffmpeg` binary for the detected OS/architecture.
  3.  **Extracts `ffmpeg`:** If a matching archive is found, it uses `py7zr` to extract the `ffmpeg` executable into a temporary directory.
  4.  **Sets Environment Variable:** Sets the `FFMPEG_BINARY` environment variable to the path of the extracted `ffmpeg` executable. This is how `moviepy` (and other tools) know where to find `ffmpeg`.
  5.  **Grants Permissions (Linux/macOS):** On non-Windows systems, it sets execute permissions (`0o755`) for the extracted `ffmpeg` binary.
  6.  **`yield`:** The `yield ffmpeg_path` statement makes this a context manager. The code inside the `with managed_ffmpeg():` block will execute here.
  7.  **Cleanup (`finally` block):** After the `with` block finishes (or an error occurs), the `finally` block ensures that the extracted `ffmpeg` binary is deleted and the `FFMPEG_BINARY` environment variable is reset to its original value (or removed).
- **Called by:** The `if __name__ == '__main__':` block to wrap the entire application's execution.

### `load_options(options_path='options.json')`
- **Purpose:** Loads user-configurable settings from `options.json`. If the file doesn't exist or is invalid, it creates one with default values..
- **How it works:**
    1.  Defines a `defaults` dictionary with a comprehensive set of options:
      - `chars`, `gamma`, `contrast`: For ASCII rendering.
      - `temp`, `wide`, `fps`: For general playback.
      - `ascii_chars_set`: Pre-defined character sets (`default`, `detailed`, `simple`).
      - `audio_volume_start`: Initial volume.
      - `default_video_path`: A fallback video to use.
      - `show_ui_on_start`: Toggles the welcome message.
      - `clear_screen_on_resize`: Controls terminal clearing behavior.
      - `seek_jump_seconds`, `fine_seek_seconds`: Configurable seek times.

  2.  If `options.json` doesn't exist, it creates it with these defaults.
  3.  If it exists, it loads the JSON. It then iterates through the `defaults` to ensure all expected keys are present in the loaded options, filling in any missing or empty values with their defaults.
- **Called by:** `main()` and `pic_to_ascii_from_pil()`.

### `pic_to_ascii_from_pil(pic, wide=None, high=None)`
- **Purpose:** The core function that converts a Pillow `Image` object into a string of colored ASCII art, dynamically adapting to terminal size.
- **How it works:**
  1.  **Loads Options:** Retrieves ASCII character settings, gamma, and contrast from `options.json`. It supports multiple character sets (`default`, `detailed`, `simple`) and a user-defined `custom` set.
  2.  **Determines Output Dimensions:**
      *   If `wide` or `high` are `None` (which they are during real-time playback), it uses `shutil.get_terminal_size()` to get the current terminal's width and height. It then calculates the optimal `wide` and `tall` (height) for the ASCII art, preserving the video's aspect ratio and ensuring it fits within the terminal.
      *   It uses a `0.55` factor for `tall` calculation because terminal characters are typically taller than they are wide.
  3.  **Resizes Images:** Converts the input `pic` to grayscale (`'L'`) and RGB (`'RGB'`) modes, then resizes both to the calculated `(wide, tall)` dimensions.
  4.  **Pixel Iteration:** Iterates through each pixel of the resized grayscale image (`px`) and its corresponding color pixel (`px_color`).
  5.  **ASCII Character Mapping:** For each grayscale pixel value `p` (0-255), it maps it to a character from the `chars` string (e.g., "█▓▒░"). Darker pixels map to denser characters.
  6.  **Color Application:** For each RGB pixel, it applies `gamma` and `contrast` adjustments to the R, G, and B values. It then generates an ANSI escape code (`\033[38;2;R;G;B;m`) to set the foreground color for the character.
  7.  **Line Breaks:** Adds a newline character (`\n`) and resets the color (`Style.RESET_ALL`) after every `wide` characters to form the rows of ASCII art.
- **Called by:** `pic_to_ascii()`.

### `pic_to_ascii(img_path, wide=None, high=None)`
- **Purpose:** A wrapper function that loads an image from a file path and then calls `pic_to_ascii_from_pil` to convert it to ASCII.
- **How it works:** Opens the image file specified by `img_path` using `PIL.Image.open()` and passes the resulting Pillow `Image` object to `pic_to_ascii_from_pil`.
- **Called by:** `play_ascii_video_stream_streaming()` during real-time playback.

### `getch()`
- **Purpose:** Reads a single character from the keyboard without requiring the user to press Enter, and without blocking the program's execution. It's designed to be cross-platform.
- **How it works:**
  - **Windows:** Uses `msvcrt.kbhit()` to check if a key has been pressed, and `msvcrt.getch()` to read it.
  - **Linux/macOS (Unix-like):** Manipulates terminal settings (`termios`, `tty`) to put the terminal into "cbreak" mode, allowing single-character input. It uses `select.select` to check for input availability without blocking.
- **Called by:** `keyboard_listener()` to detect user key presses.

### `clear_terminal()`
- **Purpose:** A utility function to clear the entire terminal screen by executing system-specific commands (`cls` or `clear`). The main playback loop uses more direct ANSI escape codes for efficiency.

### `get_stuff_from_video_stream(vid, out, speed=24, buffer_size=24)`
- **Purpose:** Extracts the audio from a video and starts a background thread to extract video frames as PNG images, putting their file paths into a queue for the main playback loop.- **How it works:**
  1.  **Temporary Folder Setup:** Ensures the `out` directory exists.
  2.  **Audio Extraction:** Uses `moviepy` to extract the audio track from the `vid` file and saves it as `audio.ogg`. `contextlib.redirect_stdout/stderr` are used to suppress `moviepy`'s verbose output.
  3.  **`frame_queue`:** Initializes a `thread_queue.Queue` (a thread-safe queue) to hold the paths of the extracted PNG frames. This queue acts as a buffer between the frame extraction thread and the main playback thread.
  4.  **`extract_frames_worker()` (Threaded):**      *   This nested function runs in a separate `threading.Thread`.
      *   It iterates through `clip.iter_frames()`, saving each frame as a PNG file (e.g., `frame_00001.png`) in the `out` directory.
      *   The path of each saved PNG is put into `frame_queue`.
      *   A `None` sentinel is put into the queue when all frames are extracted, signaling the end.
      *   A `finally` block ensures `clip.close()` is called to release the video file handle, preventing resource leaks.
  5.  **Starts Thread:** The `extract_frames_worker` is started in a `threading.Thread` with `daemon=True` (so it exits when the main program exits).
  6.  **Returns:** The temporary folder path, audio path, `frame_queue`, total frames, and video duration.
- **Called by:** `main()`.

### `play_ascii_video_stream_streaming(...)`
- **Purpose:** This is the heart of the video player. It plays the ASCII video and audio in real-time, handles user input, dynamic resizing, seeking, and volume control.
- **How it works:**
  1.  **Initialization:**
      *   Loads options from `options.json` to get settings like initial volume and seek durations.
      *   Initializes `pygame.mixer` for audio playback.
      *   Sets `delay` per frame based on `speed` (FPS).
      *   Uses `threading.Event` objects (`stop_flag`, `pause_flag`) for inter-thread communication (to signal quit/pause).
      *   `playback_state` dictionary stores `volume` and `is_muted` status, shared between threads.
      *   `rewind_forward` is a `thread_queue.Queue` used to pass seek commands from the keyboard listener.
  2.  **`keyboard_listener()` (Threaded):**
      *   Runs in a separate `threading.Thread` to continuously read keyboard input using `getch()`.
      *   Handles `Space` (pause/play), `Q` (quit), `M` (mute/unmute), `+/-` (volume up/down), `A/D` (seek), and arrow keys (fine seek). The seek durations are configurable in `options.json`.
      *   Updates `pause_flag`, `stop_flag`, `playback_state`, and `rewind_forward` queue based on input.
  3.  **`play_audio_from(pos)`:** Loads and plays the audio from a specific `pos` (timestamp). It also sets the volume based on `playback_state`. It includes a fade-in effect for smoother audio transitions after seeking.
  4.  **`format_time(t)`:** Formats a time in seconds into `HH:MM:SS` string.
  5.  **Pre-buffering:** Fills `frames_buffer` with an initial set of PNG paths from `frame_queue`.
  6.  **Main Playback Loop:** `while not stop_flag.is_set() and frames_buffer:`
      *   **Seek Handling:** Checks `rewind_forward` queue for jump commands. If a jump occurs:
          *   Calculates `target_i` (target frame index).
          *   Pauses and fades out audio.
          *   Clears the internal frame buffer.
          *   **Robust Seek:** Waits for the specific target PNG file to exist on disk (extracted by `extract_frames_worker`).
          *   Refills `frames_buffer` with the target PNG and subsequent PNGs from disk.
          *   Resumes audio from the new position.
      *   **Pause Handling:** If `pause_flag` is set, it pauses audio and waits until unpaused or quit.
      *   **Frame Synchronization:** Calculates `sleep_for` to maintain the target FPS.
      *   **Volume Application:** Continuously checks `playback_state` and calls `pygame.mixer.music.set_volume()` if the volume or mute status has changed.
      *   **Dynamic Terminal Resizing:**
          *   Uses `shutil.get_terminal_size()` to detect if the terminal size has changed.
          *   If it has, it clears the screen (`\x1b[2J\x1b[H`) to redraw everything cleanly.
      *   **ASCII Conversion & Display:**
          *   Takes the first PNG path from `frames_buffer`.
          *   Calls `pic_to_ascii(png_path, wide=None, high=None)`. Passing `None` for `wide` and `high` tells `pic_to_ascii` to automatically determine dimensions based on the *current terminal size*. This is the core of dynamic resizing.
          *   Prints the resulting `ascii_frame_output`.
      *   **UI Rendering:** Constructs and prints the seekbar at the bottom, including:
          *   Play/pause emoji.
          *   Progress bar (`█` and `-`).
          *   Current time and total time.
          *   Volume icon (`🔇`/`🔊`) and a visual volume bar (`█` and `-`).
      *   **Buffer Management:**
          *   Deletes the PNG file that was just displayed (`os.remove(frames_buffer[0])`) to save disk space.
          *   Removes the displayed frame from `frames_buffer`.
          *   Attempts to `get_nowait()` a new PNG path from `frame_queue` to refill the buffer.
  7.  **Cleanup:** After the loop finishes (quit or end of video), it stops audio, joins the keyboard thread, and quits `pygame.mixer`.
- **Called by:** `main()`.

### `main()`
- **Purpose:** The main entry point of the program. It orchestrates the entire video playback process.
- **How it works:**
  1.  **Intro UI:** Prints a fancy welcome box with basic controls using `colorama`.
  2.  **Load Options:** Calls `load_options()` to get user settings.
  3.  **Get Video Path:**
      *   Checks `sys.argv` for a video file path provided as a command-line argument.
      *   If no argument, it prompts the user for a video file path.
      *   If the user provides no input, it checks for a `default_video_path` in `options.json`.
      *   If still no path, it defaults to `BadApple.mp4` (located via `find_resource_path`).
      *   Validates that the chosen video file exists.
  4.  **Temporary Folder Setup:** Gets the `temp` folder path from options and registers `cleanup_temp_folder` with `atexit` to ensure cleanup on exit.
  5.  **Optimization: 144p Downscaling (using `subprocess`):**
      *   Before any other processing, it checks the video's resolution.
      *   If the height is greater than 144, it constructs an `ffmpeg` command using `subprocess.run` to downscale the video to 144p (`scale=-2:144`) using `libx264` codec (`ultrafast` preset for speed) and copies the audio.
      *   The `vid` variable is then updated to point to this new, downscaled temporary video.
      *   This ensures that the entire processing pipeline works with a smaller, more performant video file.
  6.  **Start Streaming Pipeline:** Calls `get_stuff_from_video_stream()` to begin background frame extraction.
  7.  **Start Playback:** Calls `play_ascii_video_stream_streaming()` to start the main video and audio playback, passing in the configurable seek durations from the options.
  8.  **Error Handling:** Uses `try-except` blocks to catch `KeyboardInterrupt` (Ctrl+C) and other exceptions, ensuring `cleanup_temp_folder` is always called.
- **Called by:** The `if __name__ == '__main__':` block.

### `if __name__ == '__main__':` block
- **Purpose:** This standard Python construct ensures that the code inside it only runs when the script is executed directly (not when imported as a module). It sets up the overall application environment.
- **How it works:**
  1.  **`multiprocessing.freeze_support()`:** Crucial for `multiprocessing` to work correctly when the script is bundled into an executable on Windows.
  2.  **`managed_ffmpeg()` Context:** Wraps the main logic within the `managed_ffmpeg()` context manager, ensuring `ffmpeg` is available and cleaned up.
  3.  **Signal Handling:** Sets up `signal.SIGINT` (Ctrl+C) and `signal.SIGTERM` handlers to call `handle_exit`, which performs cleanup and exits gracefully.
  4.  **Interactive Loop:** It checks if a command-line argument was provided.
      - If yes, it calls `main()` once.
      - If no, it enters a `while True:` loop, calling `main()` repeatedly. This allows the user to play another video after one finishes without restarting the script.
  5.  **Final Cleanup:** A `finally` block ensures `cleanup_temp_folder` is called one last time.

### `SuppressStderr` class
- **Purpose:** A context manager to temporarily redirect the standard error stream (`sys.stderr`) to `os.devnull` (a black hole).
- **How it's used here:** It's used to wrap the `import` statements for libraries like `pygame` and `moviepy`. This prevents them from printing their welcome messages or other noisy output to the terminal when the script starts, resulting in a cleaner user experience.

---

## Historical/Less Used Functions (Present in Code, but not in Primary Workflow)

The provided `vidminal.py` contains some functions that represent older approaches or were part of previous iterations of the project. They are not part of the current, optimized playback pipeline but are explained here for completeness.

### `get_stuff_from_video(vid, out, speed=24, wide=160)`
- **Purpose (Historical):** This was an older method for processing video. It would extract *all* frames, convert *all* of them to ASCII, and save them as `.txt` files *before* playback began.
- **Why it's less used now:** For long videos, this pre-processing could take a very long time and consume a lot of disk space. The current `get_stuff_from_video_stream` and `play_ascii_video_stream_streaming` functions use a more efficient streaming approach where frames are extracted and converted on-the-fly, or extracted as PNGs and converted on-the-fly, reducing initial load time and disk usage.

### `convert_frame_to_ascii(args)`
- **Purpose (Historical):** This was a helper function specifically designed to be used with `multiprocessing.Pool.map()` in the older `get_stuff_from_video` function. It would take a PNG file path and convert it to ASCII.
- **Why it's less used now:** The current dynamic resizing approach converts PNGs to ASCII directly within the `play_ascii_video_stream_streaming` function, making this separate helper (and the `multiprocessing.Pool` it served) unnecessary for the main playback pipeline.

### `play_sound(audio, pause_flag, stop_flag)`
- **Purpose (Historical):** An older, separate function for managing audio playback.
- **Why it's less used now:** Audio playback and control are now fully integrated directly into the `play_ascii_video_stream_streaming` function, allowing for tighter synchronization and control (like volume and mute) directly within the main loop.

### `play_ascii_video_stream(folder, audio, speed=24, wide=160, buffer_size=24)`
- **Purpose (Historical):** This function was designed to play ASCII video frames that had *already been pre-converted and saved as `.txt` files* (by `get_stuff_from_video`).
- **Why it's less used now:** It has been superseded by `play_ascii_video_stream_streaming`, which handles the more complex and efficient streaming of PNGs and on-the-fly ASCII conversion, along with dynamic resizing and more advanced controls.

### `pic_from_ascii_txt(txt_path)`
- **Purpose (Historical):** A simple utility to read a pre-saved ASCII art frame from a `.txt` file.
- **Why it's less used now:** Since the current approach converts PNGs to ASCII on-the-fly, there are no `.txt` files of ASCII frames to read during playback.

---

## How does `ffmpeg` actually work here?
- `ffmpeg` is a powerful, standalone command-line program. `moviepy` is a Python library that acts as a convenient wrapper around `ffmpeg`, calling it behind the scenes.
- The code ensures the correct `ffmpeg` binary is extracted and available.
- **Audio Extraction:** `moviepy` uses `ffmpeg` to extract the audio track from the video and save it as an `.ogg` file.
- **Frame Extraction:** `moviepy` uses `ffmpeg` to efficiently iterate through the video and provide individual frames as raw pixel data (which are then saved as PNGs).
- **144p Downscaling:** For videos higher than 144p, the `main()` function directly calls `ffmpeg` via `subprocess.run`. This command tells `ffmpeg` to:
  - `-i [input_video]` : Take the original video as input.
  - `-vf scale=-2:144` : Apply a video filter to scale the height to 144 pixels, automatically calculating the width to maintain aspect ratio (`-2`).
  - `-c:v libx264 -preset ultrafast -crf 28` : Encode the video using the `libx264` codec with an `ultrafast` preset (for speed, not quality) and a constant rate factor (`crf`) for compression.
  - `-c:a copy` : Copy the audio stream without re-encoding it.
  - `[output_path]` : Save the result to a new temporary MP4 file.

---

## How does the ASCII art work?
- **Dynamic Sizing:** When a frame is about to be displayed, `pic_to_ascii` (which calls `pic_to_ascii_from_pil`) first checks the *current* width and height of your terminal window using `shutil.get_terminal_size()`.
- **Aspect Ratio Correction:** It then calculates the optimal dimensions for the ASCII art, taking into account that terminal characters are typically taller than they are wide (using a `0.55` factor). This ensures the video doesn't look stretched.
- **Grayscale Conversion:** The original color image frame is converted to grayscale.
- **Pixel-to-Character Mapping:** Each grayscale pixel's brightness value (0-255) is mapped to a character from a predefined set (e.g., "█▓▒░"). Brighter pixels get lighter characters, and darker pixels get denser characters.
- **Color Application:** The original color pixel's RGB values are adjusted for `gamma` and `contrast`. Then, ANSI escape codes (`\033[38;2;R;G;B;m`) are inserted before each character to set its foreground color in the terminal.
- **Output:** The result is a long string of characters and ANSI codes that, when printed to the terminal, forms the colored ASCII art frame.

---

## How does the audio stay in sync?
- **Initial Sync:** The audio (`pygame.mixer.music.play(start=0)`) and video playback loop start at roughly the same time.
- **Frame Timing:** The `delay` variable (1.0 / FPS) determines how long each frame should be displayed. The main loop calculates `sleep_for` to pause just enough to maintain the correct frame rate.
- **Pause/Resume:** When you press `Space`, both `pygame.mixer.music.pause()` and the video display loop pause. When you resume, `pygame.mixer.music.play(start=paused_at)` ensures audio resumes from the correct point, and the video loop continues from where it left off.
- **Seeking:** When you seek (`A/D` or arrow keys), the `play_audio_from(i * delay)` function is called to jump the audio to the new position, and the video buffer is cleared and refilled from the new frame.
- **Volume/Mute:** The `playback_state` dictionary is shared between the keyboard listener and the main loop. Any changes to `volume` or `is_muted` are immediately applied to `pygame.mixer.music.set_volume()` in the main loop, ensuring real-time control.

---

## How do the controls work?
- **Non-Blocking Input:** The `keyboard_listener` runs in a separate thread and uses `getch()` to read key presses without stopping the video playback.
- **Shared State:** Key presses update shared variables (`stop_flag`, `pause_flag`, `playback_state`) or queues (`rewind_forward`) that the main playback loop constantly monitors.
- **Specific Key Mappings:**
  - `Space`: Toggles `pause_flag`.
  - `Q`: Sets `stop_flag` to signal program exit.
  - `A`/`D`: Puts `-5 * speed` or `+5 * speed` into `rewind_forward` queue for 5-second jumps.
  - `←`/`→` (Arrow keys): Puts `-speed` or `+speed` into `rewind_forward` queue for 1-second jumps. (Handles platform-specific arrow key codes).
  - `M`: Toggles `is_muted` in `playback_state`.
  - `+/-`: Adjusts `volume` in `playback_state` by `0.1` (clamped between 0.0 and 1.0) and unmutes.

---

## How does cleanup work?
- **`atexit` Module:** The `cleanup_temp_folder` function is registered with `atexit.register()`. This guarantees that `cleanup_temp_folder` will be called automatically when the Python program is about to exit normally (e.g., after `main()` finishes, or if `sys.exit()` is called).
- **Signal Handling:** `signal.SIGINT` (Ctrl+C) and `signal.SIGTERM` are caught, and a custom `handle_exit` function is called. This function also calls `cleanup_temp_folder` before exiting, ensuring graceful termination even if the user forces a quit.
- **Temporary Files:**
  - The initial downscaled 144p video (if created) is in the `temp` folder and gets deleted.
  - Each extracted PNG frame is saved to the `temp` folder, but then `os.remove()` is called on it immediately after it's displayed, minimizing disk usage.
  - The extracted audio file (`audio.ogg`) is in the `temp` folder and gets deleted.
- **`ffmpeg` Binary:** The temporary `ffmpeg` executable extracted by `managed_ffmpeg()` is explicitly deleted in its `finally` block.

---

## What if something breaks?
- The code uses `try-except` blocks around critical operations (like file I/O, `json` loading, `subprocess` calls) to catch errors.
- If a major error occurs, it prints a message like `'Nope, broke: [error message]'` to the terminal.
- Common issues include:
  - **File Not Found:** If the video path is incorrect.
  - **Missing Dependencies:** If `Pillow`, `moviepy`, `pygame`, `py7zr`, or `colorama` are not installed.
  - **`ffmpeg` Issues:** If `ffmpeg` is corrupted or cannot be extracted/executed (though the bundled `ffmpeg` should prevent most of these).
  - **Terminal Compatibility:** Very old or unusual terminals might not fully support ANSI escape codes or non-blocking input.
- **Debugging:** Check the error message, ensure your video file is valid, and verify all dependencies are installed.

---

## Want to learn more?
- Look up the docs for: ffmpeg, moviepy, pygame, Pillow, colorama, py7zr, threading, queue, multiprocessing
- Try changing the options in `options.json` (like `wide`, `fps`, `chars`) and see what happens!

---

## TL;DR
- This code takes a video, **downscales it to 144p if needed**, extracts frames as PNGs, and then converts them to **colored ASCII art on-the-fly**, playing it in your terminal with sound.
- It **dynamically adapts to your terminal's size** for the best visual fit.
- It uses `ffmpeg` (via `moviepy` and `subprocess`) for video/audio processing, `Pillow` for image manipulation, `colorama` for terminal colors, `pygame` for sound, and `threading` for responsive controls.
- You get **full playback controls**: pause/play, quit, **seek (5s and 1s jumps)**, and **volume/mute**.
- It's designed to be robust, cleaning up all temporary files automatically.

---

## How does ffmpeg actually work here?
- ffmpeg is a separate program (not Python!) that can read and convert video/audio files.
- `moviepy` calls ffmpeg behind the scenes to:
  - Extract the audio track from the video
  - Extract each video frame as an image
  - Downscale the video to 144p if needed
- The code makes sure the right ffmpeg binary is available and tells moviepy where to find it.

---

## How does the ASCII art work?
- Each video frame is resized to fit the terminal (or to 144p if the video is larger)
- Each pixel is converted to a colored ASCII character (darker = denser character)
- The result is a string of text with ANSI color codes, printed to the terminal

---

## How does the audio stay in sync?
- The code calculates how long each frame should be shown (based on fps)
- It starts the audio and video at the same time
- If you pause, both audio and video pause
- If you seek, both jump to the new position
- Volume and mute are always in sync with the seekbar display

---

## How do the controls work?
- Space: Pause/Unpause
- Q: Quit
- A/D: Rewind/Forward 5 seconds
- Arrow keys: Fine seek (left/right)
- M: Mute/Unmute
- +/-: Volume up/down

---

## How does cleanup work?
- The temp folder (with frames/audio and any downscaled video) is deleted when the program exits, even if you quit early or force close.
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
- This code takes a video, downscales it to 144p if needed, turns it into colored ASCII art, and plays it in your terminal with sound.
- It uses ffmpeg (via moviepy) to extract frames/audio, Pillow to process images, colorama for color, pygame for sound, and a bunch of Python magic to keep it all in sync and clean up after itself.
- You can pause, quit, seek, and control volume/mute. It works on Windows, Mac, and Linux.

Enjoy!
