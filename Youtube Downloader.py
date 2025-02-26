import os
import yt_dlp
from googletrans import Translator
import re
from datetime import timedelta
import subprocess

# Initialize the translator for subtitle translation
translator = Translator()

# Function to sanitize filenames by replacing invalid characters
def sanitize_filename(filename):
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', filename)

# Function to convert VTT subtitles to SRT using ffmpeg
def convert_vtt_to_srt(vtt_file):
    srt_file = vtt_file.rsplit('.', 1)[0] + '.srt'
    try:
        cmd = ['ffmpeg', '-y', '-i', vtt_file, srt_file]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Converted subtitles to: {srt_file}")
        return srt_file
    except Exception as e:
        print(f"Error converting {vtt_file} to srt: {e}")
        return None

# Function to translate SRT subtitle files to a target language
def translate_srt(src_file, subtitle_lang, target_lang):
    try:
        with open(src_file, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        blocks = srt_content.strip().split('\n\n')
        translated_blocks = []
        
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                index = lines[0]
                timing = lines[1]
                text = '\n'.join(lines[2:])
                # Translate text from subtitle_lang to target_lang
                translated_text = translator.translate(text, src=subtitle_lang, dest=target_lang).text
                # For Arabic, wrap the text with RTL embedding markers
                if target_lang == 'ar':
                    # U+202B: Right-to-left Embedding, U+202C: Pop Directional Formatting
                    translated_text = "\u202B" + translated_text + "\u202C"
                translated_blocks.append(f"{index}\n{timing}\n{translated_text}")
        
        translated_srt = '\n\n'.join(translated_blocks)
        # Replace the language code in filename (e.g., from .en.srt to .ar.srt)
        translated_file = src_file.replace(f'.{subtitle_lang}.srt', f'.{target_lang}.srt')
        
        with open(translated_file, 'w', encoding='utf-8') as f:
            f.write(translated_srt)
        print(f"Translated subtitles saved to: {translated_file}")
    except Exception as e:
        print(f"Error translating subtitles: {e}")

# Function to clean duplicate lines in SRT subtitle files
def clean_srt_duplicates(srt_file):
    with open(srt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_blocks = []
    prev_text = None
    prev_end_time = None
    prev_start_time = None
    index = 1
    
    i = 0
    while i < len(lines):
        if lines[i].strip().isdigit():  # Start of a subtitle block
            timing_line = lines[i + 1].split(' align:')[0].strip()
            start_time, end_time = timing_line.split(' --> ')
            
            text_lines = []
            j = i + 2
            while j < len(lines) and lines[j].strip() and not lines[j].strip().isdigit():
                text_lines.append(lines[j].strip())
                j += 1
            text = '\n'.join(text_lines)
            
            if text == prev_text and prev_end_time == start_time:
                cleaned_blocks[-1] = f"{index-1}\n{prev_start_time} --> {end_time}\n{prev_text}\n"
            else:
                cleaned_blocks.append(f"{index}\n{timing_line}\n{text}\n")
                prev_text = text
                prev_end_time = end_time
                prev_start_time = start_time
                index += 1
            
            i = j
        else:
            i += 1
    
    with open(srt_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_blocks))
    print(f"Cleaned subtitles saved to: {srt_file}")

# Progress hook to display download progress and manage subtitles
def progress_hook(d, subtitle_lang, translate_subtitles, target_lang, video_duration=None):
    if d['status'] == 'downloading':
        filename = d.get('filename', 'Unknown file')
        downloaded = d.get('downloaded_bytes', 0)
        total = d.get('total_bytes', 0)
        speed = d.get('speed', 0) or 0
        if total:
            progress = (downloaded / total) * 100
            print(f"\rDownloading {filename} - {progress:.2f}% at {speed / 1024:.2f} KB/s", end='')
        else:
            print(f"\rDownloading {filename} - {downloaded / 1024:.2f} KB (Unknown size) at {speed / 1024:.2f} KB/s", end='')
    elif d['status'] == 'finished':
        print(f"\nDownload completed: {d.get('filename', 'Unknown file')}")
        if subtitle_lang and 'filename' in d and (d['filename'].endswith('.srt') or d['filename'].endswith('.vtt')):
            subtitle_filename = d['filename']
            # If the file is in VTT format, convert it to SRT first
            if subtitle_filename.endswith('.vtt'):
                new_filename = convert_vtt_to_srt(subtitle_filename)
                if new_filename:
                    subtitle_filename = new_filename
            clean_srt_duplicates(subtitle_filename)
            if translate_subtitles:
                print(f"Translating subtitles from {subtitle_lang} to {target_lang}...")
                translate_srt(subtitle_filename, subtitle_lang, target_lang)

# Function to prompt user with input validation and quit option
def prompt_with_validation(prompt, valid_options, allow_quit=True):
    while True:
        print(prompt)
        if allow_quit:
            print("[q] Quit")
        choice = input("Enter your choice: ").strip().lower()
        if allow_quit and choice == 'q':
            print("Exiting program.")
            exit()
        if choice in valid_options:
            return choice
        print("Invalid choice. Please try again.\n")

# Function to collect all user inputs at the beginning
def get_user_inputs():
    config = {}
    # Download type
    choice = prompt_with_validation(
        "Choose download type:\n1. Video (MP4)\n2. Audio (MP3)",
        ['1', '2']
    )
    config['download_type'] = 'video' if choice == '1' else 'audio'

    # Content type
    choice = prompt_with_validation(
        "Choose content type:\n1. Single Video\n2. Playlist\n3. Channel",
        ['1', '2', '3']
    )
    config['content_type'] = ['single', 'playlist', 'channel'][int(choice) - 1]

    # YouTube link
    while True:
        link = input("Enter the YouTube link: ").strip()
        if link.lower() == 'q':
            print("Exiting program.")
            exit()
        if 'youtube.com' in link or 'youtu.be' in link:
            break
        print("Invalid YouTube link. Please try again.\n")
    config['link'] = link

    # For single video with video download, fetch info and select quality
    if config['content_type'] == 'single' and config['download_type'] == 'video':
        ydl_opts_video = {'quiet': True, 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            info_video = ydl.extract_info(link, download=False)
        config['video_duration'] = info_video.get('duration', 0)
        config['raw_title'] = info_video.get('title', 'No title available')
        print(f"Raw title extracted: {config['raw_title']}")
        print(f"Video duration: {timedelta(seconds=int(config['video_duration']))}")

        formats = info_video.get('formats', [])
        video_formats = [f for f in formats if f['ext'] == 'mp4' and f.get('vcodec') and f.get('acodec')]
        video_formats.sort(key=lambda f: int(f.get('height', 0)), reverse=True)
        seen_heights = set()
        unique_formats = []
        for f in video_formats:
            height = f.get('height', 0)
            if height not in seen_heights:
                seen_heights.add(height)
                unique_formats.append(f)
        if not unique_formats:
            print("No suitable video formats found.")
            exit()
        print("Available qualities:")
        for i, f in enumerate(unique_formats, 1):
            height = f.get('height', 'Unknown')
            print(f"{i}. {height}p")
        while True:
            quality_choice = input("Choose quality (number): ").strip().lower()
            if quality_choice == 'q':
                print("Exiting program.")
                exit()
            try:
                index = int(quality_choice) - 1
                if 0 <= index < len(unique_formats):
                    config['format_option'] = unique_formats[index]['format_id'] + '+bestaudio'
                    break
                print("Invalid choice.")
            except ValueError:
                print("Invalid input. Please enter a number.\n")
    else:
        # For playlist or channel video downloads, ask for maximum resolution if video
        if config['download_type'] == 'video':
            resolutions = [
                ('1', '144', '144p'),
                ('2', '240', '240p'),
                ('3', '360', '360p'),
                ('4', '480', '480p'),
                ('5', '720', '720p'),
                ('6', '1080', '1080p'),
                ('7', '1440', '1440p'),
                ('8', '2160', '4K (2160p)'),
                ('9', '4320', '8K (4320p)')
            ]
            prompt = "Choose maximum resolution:\n" + "\n".join([f"{r[0]}. {r[2]}" for r in resolutions])
            choice = prompt_with_validation(prompt, [r[0] for r in resolutions])
            max_res = next(r[1] for r in resolutions if r[0] == choice)
            config['format_option'] = f"bestvideo[height<={max_res}]+bestaudio/best[height<={max_res}]"
        else:
            # For audio downloads, use bestaudio
            config['format_option'] = 'bestaudio'

    # Subtitle options
    subtitle_choice = prompt_with_validation(
        "Do you want to download subtitles?\n1. Yes\n2. No",
        ['1', '2']
    )
    if subtitle_choice == '1':
        while True:
            subtitle_lang = input("Enter subtitle language code (e.g., 'en' for English, 'ar' for Arabic): ").strip().lower()
            if subtitle_lang == 'q':
                print("Exiting program.")
                exit()
            if len(subtitle_lang) == 2 and subtitle_lang.isalpha():
                break
            print("Invalid language code. Please try again.\n")
        config['subtitle_lang'] = subtitle_lang
        auto_subs = prompt_with_validation(
            "Include auto-generated subtitles if available?\n1. Yes\n2. No",
            ['1', '2']
        )
        config['auto_subs'] = auto_subs
        translate_choice = prompt_with_validation(
            "Do you want to translate subtitles to another language?\n1. Yes\n2. No",
            ['1', '2']
        )
        if translate_choice == '1':
            config['translate_subtitles'] = True
            target_lang = input("Enter target language code (e.g., 'ar', 'en'): ").strip().lower()
            config['target_lang'] = target_lang
        else:
            config['translate_subtitles'] = False
            config['target_lang'] = None
    else:
        config['subtitle_lang'] = None
        config['auto_subs'] = '2'
        config['translate_subtitles'] = False
        config['target_lang'] = None

    return config

# Main program
def main():
    os.makedirs("Downloaded", exist_ok=True)
    config = get_user_inputs()

    # Configure output template based on content type
    if config['content_type'] == 'single':
        output_template = 'Downloaded/%(title)s.%(ext)s'
    elif config['content_type'] == 'playlist':
        ydl_opts_flat = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
            info_flat = ydl.extract_info(config['link'], download=False)
            entries = info_flat.get('entries')
            total_videos = len(entries) if entries else 1
        num_digits = max(2, len(str(total_videos)))
        output_template = f"Downloaded/%(playlist_title)s/%(playlist_index)0{num_digits}d - %(title)s.%(ext)s"
    else:
        output_template = 'Downloaded/%(uploader)s/%(title)s.%(ext)s'

    # Build yt-dlp options with added error handling and timeouts
    ydl_opts = {
        'outtmpl': output_template,
        'progress_hooks': [lambda d: progress_hook(d, config['subtitle_lang'], config['translate_subtitles'], config['target_lang'])],
        'format': config['format_option'],
        'merge_output_format': 'mp4' if config['download_type'] == 'video' else None,
        'encoding': 'utf-8',
        'no_clean_info': True,
        'ignoreerrors': True,
        'retries': 10,
        'fragment_retries': 10,
        'socket_timeout': 60,
    }
    if config['content_type'] == 'single':
        ydl_opts['noplaylist'] = True
    if config['download_type'] == 'audio':
        ydl_opts.update({
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    if config['subtitle_lang']:
        ydl_opts.update({
            'writesubtitles': True,
            'subtitleslangs': [config['subtitle_lang']],
            'writeautomaticsub': config['auto_subs'] == '1',
            'skip_download': False,
            'convertsubtitles': 'srt',
        })

    print("\nAll questions have been answered. Starting download...\n")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([config['link']])
    except Exception as e:
        print(f"An error occurred during download: {e}")
        exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Exiting.")
        exit()
