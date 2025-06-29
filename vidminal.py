# imports: chaos and magic
import os  # file goblin
import sys  # sys go brr
import warnings  # shhh
import contextlib  # context is king
import io  # string jail
import shutil  # delete stuff fast
import atexit  # clean up my mess
import subprocess  # command line wizard
import signal
import re
import shutil
from colorama import Fore, Style

warnings.filterwarnings('ignore')  # no warnings, only vibes
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'  # pygame, shut up

# stderr: go to sleep
class SuppressStderr:
    def __enter__(self):
        self._stderr = sys.stderr
        sys.stderr = open(os.devnull, 'w')
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stderr.close()
        sys.stderr = self._stderr

with SuppressStderr():  # silence is golden
        import time  # tick tock
        from PIL import Image  # pixel wizard
        import threading  # spaghetti parallel
        import platform  # what planet am I on
        import pygame  # sound go beep
        from moviepy import VideoFileClip  # video wrangler
        import py7zr  # zip zap
        import queue  # line up!
        import colorama  # color go brr
        import multiprocessing  # more chaos
        import json  # config soup
        import tempfile  # temp trash

# nuke temp folder
def cleanup_temp_folder(temp_path):
    if os.path.exists(temp_path) and os.path.isdir(temp_path):
        try:
            shutil.rmtree(temp_path)
        except Exception:
            pass

# find stuff, pyinstaller pain
def find_resource_path(rel):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.abspath('.')
    return os.path.join(base, rel)

# ffmpeg: now you see me
@contextlib.contextmanager
def managed_ffmpeg():
    sysname = platform.system().lower()
    arch = platform.machine().lower()
    ffmpeg_bin_dir = find_resource_path(os.path.join('ffmpeg_bin'))
    if sysname == 'windows':
        zip_path = os.path.join(ffmpeg_bin_dir, 'windows.7z')
        ffmpeg_in_zip = 'ffmpeg.exe'
        suffix = '.exe'
    elif sysname == 'darwin':
        zip_path = os.path.join(ffmpeg_bin_dir, 'mac.7z')
        ffmpeg_in_zip = 'ffmpeg'
        suffix = ''
    elif sysname == 'linux':
        suffix = ''
        if 'arm' in arch:
            if '64' in arch:
                zip_path = os.path.join(ffmpeg_bin_dir, 'linux-arm-64.7z')
                ffmpeg_in_zip = 'linux-arm-64/ffmpeg'
            else:
                zip_path = os.path.join(ffmpeg_bin_dir, 'linux-armhf-32.7z')
                ffmpeg_in_zip = 'linux-armhf-32/ffmpeg'
        elif '64' in arch:
            zip_path = os.path.join(ffmpeg_bin_dir, 'linux-64.7z')
            ffmpeg_in_zip = 'linux-64/ffmpeg'
        else:
            zip_path = os.path.join(ffmpeg_bin_dir, 'linux-32.7z')
            ffmpeg_in_zip = 'linux-32/ffmpeg'
    ffmpeg_path = None
    original_ffmpeg_binary = os.environ.get('FFMPEG_BINARY')
    try:
        if zip_path and ffmpeg_in_zip and os.path.exists(zip_path):
            with tempfile.TemporaryDirectory() as extract_dir:
                with py7zr.SevenZipFile(zip_path, 'r') as archive:
                    archive.extract(targets=[ffmpeg_in_zip], path=extract_dir)
                extracted_ffmpeg = os.path.join(extract_dir, ffmpeg_in_zip)
                with open(extracted_ffmpeg, 'rb') as src_f, tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_f:
                    tmp_f.write(src_f.read())
                    ffmpeg_path = tmp_f.name
            if sysname != 'windows':
                os.chmod(ffmpeg_path, 0o755)
            os.environ['FFMPEG_BINARY'] = ffmpeg_path
            yield ffmpeg_path
        else:
            os.environ['FFMPEG_BINARY'] = 'ffmpeg'
            yield 'ffmpeg'
    finally:
        if ffmpeg_path and os.path.exists(ffmpeg_path):
            os.remove(ffmpeg_path)
        if original_ffmpeg_binary:
            os.environ['FFMPEG_BINARY'] = original_ffmpeg_binary
        elif 'FFMPEG_BINARY' in os.environ:
            del os.environ['FFMPEG_BINARY']

# video to frames & noise
def get_stuff_from_video(vid, out, speed=24, wide=160):
    if not os.path.exists(out):
        os.makedirs(out)
    audio = os.path.join(out, 'audio.ogg')
    print('Doing video things...')
    clip = VideoFileClip(vid)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        clip.audio.write_audiofile(audio, codec='libvorbis')
        frame_paths = []
        for i, frame in enumerate(clip.iter_frames(fps=speed, dtype='uint8')):
            img = Image.fromarray(frame)
            ratio = img.height / img.width
            tall = int(ratio * wide * 0.55)
            img = img.resize((wide, tall))
            frame_path = os.path.join(out, f'frame_{i+1:05d}.png')
            img.save(frame_path)
            frame_paths.append(frame_path)
        with multiprocessing.Pool() as pool:
            ascii_results = pool.map(convert_frame_to_ascii, [(fp, wide) for fp in frame_paths])
        for i, (ascii_txt, _) in enumerate(ascii_results):
            txt_path = os.path.join(out, f'frame_{i+1:05d}.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(ascii_txt)
    print('Done.')
    return out, audio

# read config, hope for best
def load_options(options_path='options.json'):
    defaults = {
        'chars': "█▓▒░",
        'gamma': 1.2,
        'contrast': 1.5,
        'temp': 'temp',
        'wide': 160,
        'fps': 24,
        'ascii_chars_set': "default",
        'audio_volume_start': 1.0,
        'default_video_path': "",
        'show_ui_on_start': True,
        'clear_screen_on_resize': True,
        'buffering_message': "Buffering...",
        'seek_jump_seconds': 5,
        'fine_seek_seconds': 1
    }
    if not os.path.exists(options_path):
        with open(options_path, 'w', encoding='utf-8') as f:
            json.dump(defaults, f, indent=2)
        return defaults
    try:
        with open(options_path, 'r', encoding='utf-8') as f:
            opts = json.load(f)
        for k in defaults:
            if k not in opts or opts[k] == '' or opts[k] is None:
                opts[k] = defaults[k]
        opts['gamma'] = float(opts['gamma'])
        opts['contrast'] = float(opts['contrast'])
        opts['wide'] = int(opts['wide'])
        opts['fps'] = int(opts['fps'])
        opts['audio_volume_start'] = float(opts['audio_volume_start'])
        opts['seek_jump_seconds'] = int(opts['seek_jump_seconds'])
        opts['fine_seek_seconds'] = int(opts['fine_seek_seconds'])
        return opts
    except Exception:
        return defaults

# image to ascii, rainbow puke
def pic_to_ascii_from_pil(pic, wide=None, high=None):
    opts = load_options()
    CHAR_SETS = {
        "default": "█▓▒░",
        "detailed": "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. ",
        "simple": " .:-=+*#%@"
    }
    chars_key = opts.get('ascii_chars_set', 'default')
    if chars_key == 'custom':
        chars = opts.get('chars', CHAR_SETS['default'])
    else:
        chars = CHAR_SETS.get(chars_key, CHAR_SETS['default'])
    gamma = float(opts['gamma'])
    contrast = float(opts['contrast'])
    if wide is None or high is None:
        try:
            size = shutil.get_terminal_size()
            term_w = int(size.columns * 0.9)
            term_h = int(size.lines * 0.9)
            if wide is None:
                wide = max(20, term_w)
            if high is None:
                high = max(10, term_h)
        except Exception:
            if wide is None:
                wide = 160
            if high is None:
                high = 24
    ratio = pic.height / pic.width
    tall = int(ratio * wide * 0.55)
    if tall > high:
        tall = high
        wide = int(tall / (ratio * 0.55))
    gray = pic.convert('L').resize((wide, tall))
    color = pic.convert('RGB').resize((wide, tall))
    px = list(gray.getdata())
    px_color = list(color.getdata())
    out = ''
    for i, (p, rgb) in enumerate(zip(px, px_color)):
        r, g, b = rgb
        r = int(255 * pow((r / 255), gamma) * contrast)
        g = int(255 * pow((g / 255), gamma) * contrast)
        b = int(255 * pow((b / 255), gamma) * contrast)
        r = min(max(r, 0), 255)
        g = min(max(g, 0), 255)
        b = min(max(b, 0), 255)
        out += f'\033[38;2;{r};{g};{b}m{chars[p * (len(chars) - 1) // 255]}'
        if (i + 1) % wide == 0:
            out += Fore.RESET + '\n'
    out += Fore.RESET
    return out, wide

# open image, get ascii
def pic_to_ascii(img, wide=None, high=None):
    pic = Image.open(img)
    return pic_to_ascii_from_pil(pic, wide, high)

# frame to ascii, multiprocessing pain
def convert_frame_to_ascii(args):
    frame_path, wide = args
    pic = Image.open(frame_path)
    return pic_to_ascii_from_pil(pic, wide)

# play sound, hope for best
def play_sound(audio, pause_flag, stop_flag):
    pygame.mixer.init()
    pygame.mixer.music.load(audio)
    pygame.mixer.music.play()
    paused_at = 0
    was_paused = False
    while not stop_flag.is_set():
        if pause_flag.is_set():
            if not was_paused:
                paused_at = pygame.mixer.music.get_pos() / 1000.0
                pygame.mixer.music.pause()
                was_paused = True
        else:
            if was_paused:
                pygame.mixer.music.play(start=paused_at)
                was_paused = False
        if not pygame.mixer.music.get_busy() and not pause_flag.is_set():
            break
        pygame.time.wait(100)
    pygame.mixer.music.stop()
    pygame.mixer.quit()

# get one char, maybe
def getch():
    if platform.system() == 'Windows':
        import msvcrt
        if msvcrt.kbhit():
            return msvcrt.getch().decode('utf-8', errors='ignore')
        return None
    else:
        import sys, select, tty, termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            dr, _, _ = select.select([sys.stdin], [], [], 0)
            if dr:
                return sys.stdin.read(1)
            return None
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

# clear screen, magic
def clear_terminal():
    os.system('cls' if platform.system() == 'Windows' else 'clear')

# play ascii frames, chaos
def play_ascii_video_stream(folder, audio, speed=24, wide=160, buffer_size=24):
    pygame.mixer.init()
    delay = 1.0 / speed
    frames = sorted([f for f in os.listdir(folder) if f.startswith('frame_') and f.endswith('.txt')])
    total = len(frames)
    stop_flag = threading.Event()
    pause_flag = threading.Event()
    pause_flag.clear()

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

    def play_audio_from(pos):
        pygame.mixer.music.load(audio)
        pygame.mixer.music.play(start=pos)

    i = 0
    print('\x1b[2J', end='')  # clear screen
    start = time.time()
    play_audio_from(0)
    while i < total and not stop_flag.is_set():
        if pause_flag.is_set():
            pygame.mixer.music.pause()
            paused_at = i * delay
            while pause_flag.is_set() and not stop_flag.is_set():
                time.sleep(0.1)
            if stop_flag.is_set():
                break
            play_audio_from(paused_at)
            start = time.time() - paused_at
        tgt = start + i * delay
        now = time.time()
        sleep_for = tgt - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        print('\x1b[H', end='')  # move cursor home
        # Batch terminal output: print whole frame at once
        print(pic_from_ascii_txt(os.path.join(folder, frames[i])), end='')
        i += 1
    stop_flag.set()
    pygame.mixer.music.stop()
    key_thread.join()
    pygame.mixer.quit()

# streams video/audio in parallel, starts playback after buffer fills
def get_stuff_from_video_stream(vid, out, speed=24, buffer_size=24):
    if not os.path.exists(out):
        os.makedirs(out)
    audio = os.path.join(out, 'audio.ogg')
    print('Doing video things...')
    clip = VideoFileClip(vid)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        clip.audio.write_audiofile(audio, codec='libvorbis')
    frame_queue = queue.Queue(maxsize=buffer_size*2)
    total_frames = int(clip.fps * clip.duration)
    video_duration = clip.duration
    def extract_frames():
        for i, frame in enumerate(clip.iter_frames(fps=speed, dtype='uint8')):
            frame_path = os.path.join(out, f'frame_{i+1:05d}.png')
            Image.fromarray(frame).save(frame_path)
            try:
                frame_queue.put_nowait(frame_path)
            except queue.Full:
                pass  # Don't block extraction, just skip putting in queue
        frame_queue.put(None)
    threading.Thread(target=extract_frames, daemon=True).start()
    return out, audio, frame_queue, total_frames, video_duration

# plays ascii video + audio from stream, handles pause/quit
def play_ascii_video_stream_streaming(folder, audio, frame_queue, total_frames, speed=24, wide=160, buffer_size=24, video_duration=None, seek_jump_seconds=5, fine_seek_seconds=1):
    import queue as pyqueue
    pygame.mixer.init()
    delay = 1.0 / speed
    stop_flag = threading.Event()
    pause_flag = threading.Event()
    pause_flag.clear()
    opts = load_options()
    playback_state = {
        'volume': float(opts.get('audio_volume_start', 1.0)),
        'is_muted': False,
    }
    rewind_forward = pyqueue.Queue()

    def keyboard_listener():
        import platform
        is_windows = platform.system() == 'Windows'
        while not stop_flag.is_set():
            key = getch()
            if not key:
                time.sleep(0.05)
                continue
            if key == ' ':
                if pause_flag.is_set():
                    pause_flag.clear()
                else:
                    pause_flag.set()
            elif key in ('q', 'Q'):
                stop_flag.set()
            elif key in ('m', 'M'):
                playback_state['is_muted'] = not playback_state['is_muted']
            elif key in ('-', '_'):
                # Decrease volume, ensure it doesn't go below 0
                playback_state['volume'] = max(0.0, round(playback_state['volume'] - 0.1, 1))
            elif key in ('+', '='):
                playback_state['volume'] = min(1.0, round(playback_state['volume'] + 0.1, 1))
                playback_state['is_muted'] = False
            elif key in ('a', 'A'):
                rewind_forward.put(-seek_jump_seconds * speed)
            elif key in ('d', 'D'):
                rewind_forward.put(seek_jump_seconds * speed)
            elif is_windows:
                # Windows arrow keys: first getch() returns '\xe0', next is code
                if key in ('\xe0', '\x00'):
                    next_key = getch()
                    if next_key == 'M':  # right arrow
                        rewind_forward.put(fine_seek_seconds * speed)
                    elif next_key == 'K':  # left arrow
                        rewind_forward.put(-fine_seek_seconds * speed)
            else:
                # Unix: arrow keys are '\x1b', '[', 'C'/'D'
                if key == '\x1b':
                    next1 = getch()
                    if next1 == '[':
                        next2 = getch()
                        if next2 == 'C':  # right arrow
                            rewind_forward.put(fine_seek_seconds * speed)
                        elif next2 == 'D':  # left arrow
                            rewind_forward.put(-fine_seek_seconds * speed)
            time.sleep(0.05)

    key_thread = threading.Thread(target=keyboard_listener, daemon=True)
    key_thread.start()

    def play_audio_from(pos, fade_ms=100):
        pygame.mixer.music.load(audio)
        pygame.mixer.music.set_volume(0.0 if playback_state['is_muted'] else playback_state['volume'])
        pygame.mixer.music.play(start=pos, fade_ms=fade_ms)

    def format_time(t):
        t = int(t)
        return f"{t//3600:02}:{(t%3600)//60:02}:{t%60:02}"

    print('\x1b[2J', end='')  # clear screen
    start = time.time()
    play_audio_from(0, fade_ms=0)
    i = 0
    frames_buffer = []
    # Pre-buffer
    while len(frames_buffer) < buffer_size:
        frame_path = frame_queue.get()
        if frame_path is None:
            break
        frames_buffer.append(frame_path)
    total_time = video_duration if video_duration is not None else (total_frames / speed if total_frames > 0 else 0)
    import shutil
    last_term_size = shutil.get_terminal_size()
    last_audio_seek = 0
    while not stop_flag.is_set() and frames_buffer:
        # Handle rewind/forward requests
        jump = 0
        while not rewind_forward.empty():
            jump += rewind_forward.get()
        if jump != 0:
            target_i = max(0, min(i + jump, total_frames - 1))
            pygame.mixer.music.fadeout(50)  # fade out audio before seek
            frames_buffer.clear()
            frame_path = os.path.join(folder, f'frame_{target_i+1:05d}.png')
            wait_count = 0
            while not os.path.exists(frame_path):
                print('\x1b[2J\x1b[H', end='')
                print('Buffering...'.center(wide), end='\n')
                time.sleep(0.02)
                wait_count += 1
                if wait_count > 400:
                    break
            if os.path.exists(frame_path):
                frames_buffer.append(frame_path)
            for idx in range(target_i+1, min(target_i+1+buffer_size, total_frames)):
                next_path = os.path.join(folder, f'frame_{idx+1:05d}.png')
                if os.path.exists(next_path):
                    frames_buffer.append(next_path)
                else:
                    break
            i = target_i
            start = time.time() - i * delay
            if frames_buffer:
                play_audio_from(i * delay, fade_ms=50)
                last_audio_seek = time.time()
        if pause_flag.is_set():
            pygame.mixer.music.pause()
            paused_at = i * delay
            while pause_flag.is_set() and not stop_flag.is_set():
                time.sleep(0.1)
            if stop_flag.is_set():
                break
            play_audio_from(paused_at, fade_ms=50)
            last_audio_seek = time.time()
            start = time.time() - paused_at
        tgt = start + i * delay
        now = time.time()
        sleep_for = tgt - now
        if sleep_for > 0:
            time.sleep(sleep_for)
        current_vol = 0.0 if playback_state['is_muted'] else playback_state['volume']
        if pygame.mixer.music.get_volume() != current_vol:
            pygame.mixer.music.set_volume(current_vol)
        try:
            term_size = shutil.get_terminal_size()
        except Exception:
            term_size = last_term_size
        if term_size != last_term_size:
            if opts.get('clear_screen_on_resize', True):
                print('\x1b[2J\x1b[H', end='')
            last_term_size = term_size
        else:
            print('\x1b[H', end='')
        actual_frame_wide = wide
        if frames_buffer:
            ascii_frame_output, actual_frame_wide = pic_to_ascii(frames_buffer[0], wide)
            print(ascii_frame_output, end='')
        else:
            print('Buffering...'.center(actual_frame_wide), end='\n')
        play_emoji = '⏸️' if not pause_flag.is_set() else '▶️'
        vol_bar_width = 10
        vol_icon = '🔇' if playback_state['is_muted'] or playback_state['volume'] == 0 else '🔊'
        if playback_state['is_muted']:
            vol_bar = '-' * vol_bar_width
        else:
            vol_level = int(round(playback_state['volume'] * vol_bar_width))
            vol_bar = '█' * vol_level + '-' * (vol_bar_width - vol_level)
        vol_str = f" {vol_icon}[{vol_bar}]"
        time_str = f"{format_time(i / speed)} / {format_time(total_time)}"
        fixed_len = 2 + 4 + len(time_str) + len(vol_str)
        bar_width = max(1, actual_frame_wide - fixed_len)
        bar_pos = int((i / (total_frames - 1)) * bar_width) if total_frames > 1 else 0
        bar = '█' * bar_pos + '-' * (bar_width - bar_pos)
        print(f"{play_emoji} [{bar}] {time_str}{vol_str}")
        i += 1
        if frames_buffer:
            frames_buffer.pop(0)
        next_idx = i + len(frames_buffer)
        if next_idx < total_frames:
            next_path = os.path.join(folder, f'frame_{next_idx+1:05d}.png')
            if os.path.exists(next_path):
                frames_buffer.append(next_path)
    stop_flag.set()
    pygame.mixer.music.stop()
    key_thread.join()
    pygame.mixer.quit()

def pic_from_ascii_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()

# main thing, asks stuff, runs stuff
def main():
    box_width = 64
    box_color = Fore.CYAN + Style.BRIGHT
    text_color = Fore.YELLOW + Style.BRIGHT
    reset = Style.RESET_ALL
    def box_line(text, color=text_color):
        # Remove ANSI codes for length calculation
        ansi_escape = re.compile(r'\x1b\[[0-9;]*m')
        visible = ansi_escape.sub('', text)
        pad = box_width - 2 - len(visible)
        return f"{box_color}║{reset}{color}{text}{' ' * pad}{reset}{box_color}║{reset}"
    lines = [
        "",
        f"{box_color}╔{'═'* (box_width-2)}╗{reset}",
        box_line("  Turns videos into ugly terminal art. With sound.  "),
        box_line("  Made by a lazy coder. " + Fore.MAGENTA + "@github/SajagIN" + text_color + "  "),
        box_line(f"  {Fore.GREEN}Space{reset}{text_color} = pause/play   {Fore.GREEN}Q{reset}{text_color} = quit"),
        box_line(f"  {Fore.GREEN}A/D{reset}{text_color} = seek 5s      {Fore.GREEN}←/→{reset}{text_color} = seek 1s"),
        box_line(f"  {Fore.GREEN}M{reset}{text_color} = mute           {Fore.GREEN}+/-{reset}{text_color} = volume"),
        f"{box_color}╚{'═'* (box_width-2)}╝{reset}",
        ""
    ]
    opts = load_options('options.json') # Load options again to ensure latest are used
    if opts['show_ui_on_start']:
        print("\n".join(lines))


    vid_path = sys.argv[1] if len(sys.argv) > 1 else ""
    is_from_arg = bool(vid_path)

    if not vid_path:
        # If no argument, prompt the user
        vid_path = input(Fore.CYAN + Style.BRIGHT + 'Video file?' + reset + f' (default: {Fore.YELLOW}BadApple.mp4{reset}): ').strip()

        if not vid_path: # If user pressed enter without input, and no sys.argv
            if opts['default_video_path']:
                vid_path = opts['default_video_path']
            else:
                vid_path = find_resource_path('BadApple.mp4') # Fallback to bundled BadApple

        if not vid_path: # If user pressed enter without input, and no sys.argv
            if opts['default_video_path']:
                vid_path = opts['default_video_path']
            else:
                vid_path = find_resource_path('BadApple.mp4') # Fallback to bundled BadApple

    if vid_path:
        if is_from_arg:
            print(Fore.CYAN + Style.BRIGHT + f"Opening: {os.path.basename(vid_path)}" + reset)
        vid = os.path.abspath(vid_path)
    else:
        # This else block should ideally not be reached if logic above is correct
        # but as a safeguard, use BadApple.mp4
        vid = find_resource_path('BadApple.mp4')

    if not os.path.exists(vid):
        print(Fore.RED + f'Error: File not found at "{vid}"' + reset)
        if is_from_arg:
            time.sleep(3) # Pause for user to see error
        sys.exit(1)


    temp = opts['temp']
    width = int(opts['wide'])
    fps = int(opts['fps'])
    atexit.unregister_all = getattr(atexit, 'unregister_all', lambda: None)  # For repeated runs in interactive mode
    atexit.unregister_all()
    atexit.register(lambda: cleanup_temp_folder(temp))

    # --- Downscale to 144p if needed ---
    # Ensure temp exists
    if not os.path.exists(temp):
        os.makedirs(temp)
    # Check video resolution
    try:
        clip = VideoFileClip(vid)
        w, h = clip.size
        clip.close()
        if h > 144:
            # Downscale to 144p and use as new source
            downscaled_path = os.path.join(temp, 'downscaled_144p.mp4')
            # Use ffmpeg from env or system
            ffmpeg_bin = os.environ.get('FFMPEG_BINARY', 'ffmpeg')
            # -y to overwrite, -vf scale=-2:144 to keep aspect
            cmd = [ffmpeg_bin, '-y', '-i', vid, '-vf', 'scale=-2:144', '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28', '-c:a', 'copy', downscaled_path]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                vid = downscaled_path
            except Exception as e:
                print(Fore.RED + f"Downscaling failed: {e}" + reset)
                sys.exit(1)
        # else: use original vid
    except Exception as e:
        print(Fore.RED + f"Failed to check video resolution: {e}" + reset)
        sys.exit(1)
    # --- End downscale logic ---

    try: # Pass new seek parameters to streaming function
        frames, audio, frame_queue, total_frames, video_duration = get_stuff_from_video_stream(vid, temp, speed=fps, buffer_size=fps) # Note: get_stuff_from_video_stream doesn't need wide
        print(Fore.GREEN + Style.BRIGHT + 'Streaming ASCII video...' + reset)
        play_ascii_video_stream_streaming(frames, audio, frame_queue, total_frames, speed=fps, wide=width, buffer_size=fps, video_duration=video_duration,
                                           seek_jump_seconds=opts['seek_jump_seconds'], fine_seek_seconds=opts['fine_seek_seconds'])
    except (KeyboardInterrupt, SystemExit):
        cleanup_temp_folder(temp)
        raise
    except Exception as e:
        print(Fore.RED + f'Nope, broke: {e}' + reset)
        cleanup_temp_folder(temp)
        sys.exit(1)
    cleanup_temp_folder(temp)

if __name__ == '__main__':
    opts = load_options('options.json')
    temp = opts['temp']
    def handle_exit(*args):
        cleanup_temp_folder(temp)
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    try:
        with managed_ffmpeg():
            if len(sys.argv) > 1:
                main()
            else:
                while True:
                    main()
    finally:
        cleanup_temp_folder(temp)