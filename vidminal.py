import argparse
import os
import subprocess
import sys
import time
from PIL import Image
import threading

# Lazy dev's guide to making video outta text and sound

def get_stuff_from_video(video_file, where_to_dump, speed=24):
    # Ya know, just rip out frames and audio with FFmpeg. Easy peasy.
    if not os.path.exists(where_to_dump):
        os.makedirs(where_to_dump) # Gotta make the folder if it's not there, duh.
    
    frame_naming = os.path.join(where_to_dump, 'frame_%05d.png')
    audio_file = os.path.join(where_to_dump, 'audio.wav')
    
    # Frames first. Don't care about errors, just make it happen.
    subprocess.run(['ffmpeg', '-i', video_file, '-vf', f'fps={speed}', frame_naming, '-hide_banner', '-loglevel', 'error', '-y'], check=True)
    
    # Then the audio. Same deal.
    subprocess.run(['ffmpeg', '-i', video_file, '-q:a', '0', '-map', 'a', audio_file, '-y', '-hide_banner', '-loglevel', 'error'], check=True)
    
    return where_to_dump, audio_file

def pic_to_ascii(image_path, wide=80):
    # Turn a picture into those cool text characters. Whatever.
    chars_to_use = "@%#*+=-:. " # These look good, I guess.
    
    pic = Image.open(image_path).convert('L') # Greyscale, 'cause colors are too much work.
    
    # Gotta shrink it down so it fits in the terminal. Math stuff.
    ratio = pic.height / pic.width
    new_tall = int(ratio * wide * 0.55)
    pic = pic.resize((wide, new_tall))
    
    pixels = pic.getdata()
    ascii_output = ""
    for i, pixel_value in enumerate(pixels):
        ascii_output += chars_to_use[pixel_value * len(chars_to_use) // 256]
        if (i + 1) % wide == 0:
            ascii_output += '\n' # New line for the next row.
            
    return ascii_output

def prepare_ascii_frames(frames_folder, wide=80):
    # Loop through all the ripped frames and turn 'em into ASCII. So tedious.
    all_frames = sorted([f for f in os.listdir(frames_folder) if f.startswith('frame_') and f.endswith('.png')])
    
    ready_ascii_frames = []
    for f in all_frames:
        frame_path = os.path.join(frames_folder, f)
        ready_ascii_frames.append(pic_to_ascii(frame_path, wide))
        
    return ready_ascii_frames

def play_sound(audio_path):
    # Just play the damn audio. FFplay handles it, thank god.
    subprocess.run(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', audio_path])

def play_ascii_video(ascii_frames_list, audio_path, speed=24):
    # Show the ASCII frames and play the audio. Hope it's synced.
    frame_delay = 1.0 / speed
    
    # Clear the screen. Don't ask me what these codes mean.
    sys.stdout.write('\x1b[2J\x1b[H')
    sys.stdout.flush()
    
    # Audio in a separate thread 'cause I'm not waiting for that.
    audio_thread = threading.Thread(target=play_sound, args=(audio_path,))
    audio_thread.start()
    
    start_time = time.time()
    for idx, ascii_frame in enumerate(ascii_frames_list):
        # Try to keep time, whatever.
        target_time = start_time + idx * frame_delay
        now = time.time()
        sleep_for = target_time - now
        if sleep_for > 0:
            time.sleep(sleep_for) # Zzzzz...
            
        sys.stdout.write('\x1b[H' + ascii_frame) # Move cursor home and print.
        sys.stdout.flush() # Make it show up.
    
    audio_thread.join() # Wait for the audio to finish. If it ever does.

def main():
    # The main thing, I guess.
    parser = argparse.ArgumentParser(description='Turns videos into ugly terminal art. With sound.')
    parser.add_argument('video', help='The video file. Give it to me.')
    parser.add_argument('--temp', default='temp', help='Where to put all the temporary junk. "temp" by default, '
                                                       'cause I\'m not creative.')
    parser.add_argument('--width', type=int, default=80, help='How wide the ASCII art should be. 80 is fine.')
    parser.add_argument('--fps', type=int, default=24, help='Frames per second. 24 is good enough for me.')
    args = parser.parse_args()
    
    try:
        frames_folder, audio_file = get_stuff_from_video(args.video, args.temp, speed=args.fps)
        print('Making frames into ASCII... this takes a while.')
        prepped_ascii_frames = prepare_ascii_frames(frames_folder, wide=args.width)
        print('Playing the "video"... good luck.')
        play_ascii_video(prepped_ascii_frames, audio_file, speed=args.fps)
    except Exception as e:
        print(f'Ugh, something broke: {e}')
        sys.exit(1) # Just exit. I'm done.

if __name__ == '__main__':
    main() # Run it. Or don't. Whatever.