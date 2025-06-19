import os
import sys
import time
from PIL import Image
import threading
import queue
import platform
import pygame
from moviepy import VideoFileClip
import contextlib
import io

# Helper function to find bundled resources, 'cause PyInstaller hides stuff
def find_resource_path(relative_path):
    try:
        # If running as a PyInstaller bundle, use the _MEIPASS path
        base_path = sys._MEIPASS
    except AttributeError:
        # Otherwise, we're probably running the .py script directly
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_stuff_from_video(video_file, where_to_dump, speed=24):
    # Use moviepy to extract frames and audio (no ffmpeg_bin needed, it was 500mb :sob: )
    if not os.path.exists(where_to_dump):
        os.makedirs(where_to_dump)
    frame_naming = os.path.join(where_to_dump, 'frame_%05d.png')
    audio_file = os.path.join(where_to_dump, 'audio.ogg')
    print('Loading and processing video...')
    clip = VideoFileClip(video_file)
    # Suppress moviepy and pygame hello messages
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        clip.audio.write_audiofile(audio_file, codec='libvorbis')
    # Write frames
    for idx, frame in enumerate(clip.iter_frames(fps=speed, dtype='uint8')):
        img = Image.fromarray(frame)
        img.save(os.path.join(where_to_dump, f'frame_{idx+1:05d}.png'))
    print('Video processing complete.')
    return where_to_dump, audio_file

def pic_to_ascii(image_path, wide=80):
    # Turn a pic into text junk. Basic conversion logic.
    chars_to_use = "@%#*+=-:. "
    pic = Image.open(image_path).convert('L') # Greyscale, less effort.
    
    ratio = pic.height / pic.width
    new_tall = int(ratio * wide * 0.55)
    pic = pic.resize((wide, new_tall)) # Squish it to fit.
    
    pixels = pic.getdata()
    ascii_output = ""
    for i, pixel_value in enumerate(pixels):
        ascii_output += chars_to_use[pixel_value * len(chars_to_use) // 256] # Char mapping.
        if (i + 1) % wide == 0:
            ascii_output += '\n' # New line.
            
    return ascii_output

def prepare_ascii_frames_stream(frames_folder, wide=80, buffer_size=24):
    # Converts frames to ASCII on the fly. Yields one at a time.
    all_frames = sorted([f for f in os.listdir(frames_folder) if f.startswith('frame_') and f.endswith('.png')])
    for f in all_frames:
        frame_path = os.path.join(frames_folder, f)
        yield pic_to_ascii(frame_path, wide)

def play_sound(audio_path, pause_flag, stop_flag):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_path)
    pygame.mixer.music.play()
    paused_at = 0
    was_paused = False
    while not stop_flag.is_set():
        if pause_flag.is_set():
            if not was_paused:
                paused_at = pygame.mixer.music.get_pos() / 1000.0  # seconds
                pygame.mixer.music.pause()
                was_paused = True
        else:
            if was_paused:
                # For OGG, we can resume from paused position
                pygame.mixer.music.play(start=paused_at)
                was_paused = False
        if not pygame.mixer.music.get_busy() and not pause_flag.is_set():
            break
        pygame.time.wait(100)
    pygame.mixer.music.stop()
    pygame.mixer.quit()

def getch():
    # Cross-platform single character input (non-blocking)
    if platform.system() == 'Windows':
        import msvcrt
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8', errors='ignore')
        else:
            return None
    else:
        import sys, select, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            dr, dw, de = select.select([sys.stdin], [], [], 0)
            if dr:
                return sys.stdin.read(1)
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def clear_terminal():
    # Cross-platform terminal clear
    os.system('cls' if platform.system() == 'Windows' else 'clear')

def play_ascii_video_stream(frames_folder, audio_path, speed=24, wide=80, buffer_size=24):
    import pygame
    pygame.mixer.init()
    frame_delay = 1.0 / speed
    all_frames = sorted([f for f in os.listdir(frames_folder) if f.startswith('frame_') and f.endswith('.png')])
    total_frames = len(all_frames)
    stop_flag = threading.Event()
    pause_flag = threading.Event()
    pause_flag.clear()  # Not paused at start

    def keyboard_listener():
        while not stop_flag.is_set():
            key = getch()
            if key == ' ':
                if pause_flag.is_set():
                    pause_flag.clear()
                else:
                    pause_flag.set()
            if key in ('q', 'Q'):
                stop_flag.set()
            time.sleep(0.05)

    key_thread = threading.Thread(target=keyboard_listener, daemon=True)
    key_thread.start()

    def play_audio_from(pos_sec):
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play(start=pos_sec)

    idx = 0
    print('\x1b[2J', end='')  # Clear screen once at the start
    start_time = time.time()
    play_audio_from(0)
    while idx < total_frames and not stop_flag.is_set():
        if pause_flag.is_set():
            pygame.mixer.music.pause()
            paused_at = idx * frame_delay
            while pause_flag.is_set() and not stop_flag.is_set():
                time.sleep(0.1)
            if stop_flag.is_set():
                break
            # Resume: restart both audio and video from paused_at
            play_audio_from(paused_at)
            start_time = time.time() - paused_at
        target_time = start_time + idx * frame_delay
        now = time.time()
        sleep_for = target_time - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        print('\x1b[H', end='')  # Move cursor to home position for smooth redraw
        frame_path = os.path.join(frames_folder, all_frames[idx])
        print(pic_to_ascii(frame_path, wide), end='')
        idx += 1
    stop_flag.set()
    pygame.mixer.music.stop()
    key_thread.join()
    pygame.mixer.quit()

def main():
    # The main show. Handles user questions.
    print('Turns videos into ugly terminal art. With sound.')
    print('Created by a bored programmer. @github/SajagIN')

    video = input('Enter the path to the video file (default: BadApple.mp4): ').strip() or 'BadApple.mp4'# Get video.
    temp = input('Where to put all the temporary junk? (default: temp): ').strip() or 'temp' # Temp dir.
    
    try:
        width = int(input('How wide should the ASCII art be? (default: 80): ').strip() or 80) # Art width.
    except ValueError:
        width = 80
        
    try:
        fps = int(input('Frames per second? (default: 24): ').strip() or 24) # Play speed.
    except ValueError:
        fps = 24
        
    try:
        frames_folder, audio_file = get_stuff_from_video(video, temp, speed=fps) # Setup video.
        print('Converting and playing video as ASCII... (streaming now!)')
        play_ascii_video_stream(frames_folder, audio_file, speed=fps, wide=width, buffer_size=fps) # Play.
    except Exception as e:
        print(f'Ugh, something broke: {e}')
        sys.exit(1)
 
if __name__ == '__main__':
    main() # Run it. Or don't. Whatever.