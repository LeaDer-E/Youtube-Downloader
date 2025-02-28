import os
import yt_dlp
from googletrans import Translator
import re
import subprocess
import time

# -----------------------------------------------
# Import colorama for colored console output
# -----------------------------------------------
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)  # Auto-reset colors after each print
except ImportError:
    # Define fallback if colorama is not installed
    class _NoColor:
        def __getattr__(self, item):
            return ''
    Fore = Style = _NoColor()

# -----------------------------------------------
# Custom logger to minimize yt-dlp verbosity
# -----------------------------------------------
class MinimalLogger:
    def debug(self, msg):
        pass  # Suppress debug messages
    def info(self, msg):
        pass  # Suppress info messages
    def warning(self, msg):
        print(f"{Fore.YELLOW}{Style.BRIGHT}[Warning]{Style.RESET_ALL} {msg}")
    def error(self, msg):
        print(f"{Fore.RED}{Style.BRIGHT}[Error]{Style.RESET_ALL} {msg}")

# -----------------------------------------------
# Initialize translator for subtitle translation
# -----------------------------------------------
translator = Translator()

# -----------------------------------------------
# Utility Functions
# -----------------------------------------------
def sanitize_filename(filename):
    """Remove invalid characters from filenames."""
    invalid_chars = r'[<>:"/\\|?*]'
    return re.sub(invalid_chars, '_', filename)

def convert_vtt_to_srt(vtt_file):
    """Convert VTT to SRT using ffmpeg."""
    srt_file = vtt_file.rsplit('.', 1)[0] + '.srt'
    try:
        cmd = ['ffmpeg', '-y', '-i', vtt_file, srt_file]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"{Fore.GREEN}{Style.BRIGHT}Converted subtitles to:{Style.RESET_ALL} {srt_file}")
        return srt_file
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error converting {vtt_file} to srt:{Style.RESET_ALL} {e}")
        return None

def translate_srt(src_file, subtitle_lang, target_lang, batch_size=10):
    """Translate SRT subtitles in batches to handle large files and avoid timeouts."""
    try:
        with open(src_file, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # Split SRT content into individual subtitle blocks
        blocks = srt_content.strip().split('\n\n')
        translated_blocks = []
        
        # Process subtitles in batches
        for i in range(0, len(blocks), batch_size):
            batch = blocks[i:i + batch_size]
            batch_text = '\n\n'.join([block.split('\n', 2)[2] for block in batch if len(block.split('\n')) >= 3])
            if not batch_text:
                continue
            
            # Translate the batch
            translated_batch = translator.translate(batch_text, src=subtitle_lang, dest=target_lang).text
            if target_lang == 'ar':
                translated_batch = "\u202B" + translated_batch + "\u202C"  # RTL support for Arabic
            
            # Reconstruct translated blocks with timing
            translated_lines = translated_batch.split('\n\n')
            for j, translated_text in enumerate(translated_lines):
                if i + j < len(blocks):
                    lines = blocks[i + j].split('\n')
                    if len(lines) >= 3:
                        index = lines[0]
                        timing = lines[1]
                        translated_blocks.append(f"{index}\n{timing}\n{translated_text}")
            
            time.sleep(0.5)  # Avoid rate limits with a small delay
        
        # Write translated subtitles to a new file
        translated_srt = '\n\n'.join(translated_blocks)
        translated_file = src_file.replace(f'.{subtitle_lang}.srt', f'.{target_lang}.srt')
        
        with open(translated_file, 'w', encoding='utf-8') as f:
            f.write(translated_srt)
        print(f"{Fore.GREEN}{Style.BRIGHT}Translated subtitles saved to:{Style.RESET_ALL} {translated_file}")
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Error translating subtitles:{Style.RESET_ALL} {e}")

def clean_srt_duplicates(srt_file):
    """Remove duplicate or merged lines in SRT files."""
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
    print(f"{Fore.GREEN}{Style.BRIGHT}Cleaned subtitles saved to:{Style.RESET_ALL} {srt_file}")

# -----------------------------------------------
# Progress Hook for Download Feedback
# -----------------------------------------------
def progress_hook(d, subtitle_lang, translate_subtitles, target_lang):
    """Display download progress and handle subtitle post-processing."""
    if d['status'] == 'finished':
        filename_colored = f"{Fore.MAGENTA}{d.get('filename', 'Unknown file')}{Style.RESET_ALL}"
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Download completed:{Style.RESET_ALL} {filename_colored}")
        if 'filename' in d and (d['filename'].endswith('.srt') or d['filename'].endswith('.vtt')):
            subtitle_filename = d['filename']
            if subtitle_filename.endswith('.vtt'):
                new_filename = convert_vtt_to_srt(subtitle_filename)
                if new_filename:
                    subtitle_filename = new_filename
            clean_srt_duplicates(subtitle_filename)
            if translate_subtitles:
                print(f"{Fore.CYAN}{Style.BRIGHT}Translating subtitles from {subtitle_lang} to {target_lang}...{Style.RESET_ALL}")
                translate_srt(subtitle_filename, subtitle_lang, target_lang)

# -----------------------------------------------
# Prompt Function with Validation
# -----------------------------------------------
def prompt_with_validation(prompt, valid_options, allow_quit=True):
    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        lines = prompt.split('\n')
        for line in lines:
            print(f"{Fore.CYAN}{Style.BRIGHT}{line}{Style.RESET_ALL}")
        if allow_quit:
            print(f"{Fore.YELLOW}[q] Quit{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        choice = input(f"{Fore.YELLOW}{Style.BRIGHT}Enter your choice: {Style.RESET_ALL}").strip().lower()

        if allow_quit and choice == 'q':
            print(f"{Fore.RED}{Style.BRIGHT}Exiting program.{Style.RESET_ALL}")
            exit()

        if choice in valid_options:
            return choice

        print(f"{Fore.RED}{Style.BRIGHT}Invalid choice. Please try again.\n{Style.RESET_ALL}")

# -----------------------------------------------
# Gather User Inputs
# -----------------------------------------------
def get_user_inputs():
    config = {}

    choice = prompt_with_validation(
        "Choose content type:\n1. Single Video\n2. Playlist\n3. Channel",
        ['1', '2', '3']
    )
    config['content_type'] = ['single', 'playlist', 'channel'][int(choice) - 1]

    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Enter the YouTube link:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[q] Quit{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        link = input(f"{Fore.YELLOW}{Style.BRIGHT}Link: {Style.RESET_ALL}").strip()

        if link.lower() == 'q':
            print(f"{Fore.RED}{Style.BRIGHT}Exiting program.{Style.RESET_ALL}")
            exit()

        if 'youtube.com' in link or 'youtu.be' in link:
            config['link'] = link
            break

        print(f"{Fore.RED}{Style.BRIGHT}Invalid YouTube link. Please try again.\n{Style.RESET_ALL}")

    if config['content_type'] == 'playlist':
        ydl_opts_flat = {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'logger': MinimalLogger()
        }
        print(f"{Fore.CYAN}{Style.BRIGHT}\nRetrieving playlist info...{Style.RESET_ALL}")
        with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
            info_flat = ydl.extract_info(config['link'], download=False)
            entries = info_flat.get('entries')
            total_videos = len(entries) if entries else 0
        if total_videos == 0:
            print(f"{Fore.RED}{Style.BRIGHT}No videos found in the playlist.{Style.RESET_ALL}")
            exit()
        print(f"{Fore.GREEN}{Style.BRIGHT}Total videos in the playlist: {total_videos}{Style.RESET_ALL}")
        choice = prompt_with_validation(
            "Choose how to select videos:\n1. All videos\n2. A range of videos (e.g., 5-30)\n3. Specific videos (e.g., 5,8,9)",
            ['1', '2', '3']
        )
        if choice == '1':
            config['playlist_items'] = None
        elif choice == '2':
            while True:
                start = input(f"{Fore.YELLOW}{Style.BRIGHT}Enter start index (1-{total_videos}): {Style.RESET_ALL}").strip()
                if start.lower() == 'q':
                    print(f"{Fore.RED}{Style.BRIGHT}Exiting program.{Style.RESET_ALL}")
                    exit()
                end = input(f"{Fore.YELLOW}{Style.BRIGHT}Enter end index (1-{total_videos}): {Style.RESET_ALL}").strip()
                if end.lower() == 'q':
                    print(f"{Fore.RED}{Style.BRIGHT}Exiting program.{Style.RESET_ALL}")
                    exit()
                try:
                    start = int(start)
                    end = int(end)
                    if 1 <= start <= end <= total_videos:
                        config['playlist_items'] = f"{start}-{end}"
                        break
                    else:
                        print(f"{Fore.RED}{Style.BRIGHT}Invalid range. Ensure 1 ≤ start ≤ end ≤ {total_videos}.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}{Style.BRIGHT}Please enter valid integers.{Style.RESET_ALL}")
        elif choice == '3':
            while True:
                indices_str = input(f"{Fore.YELLOW}{Style.BRIGHT}Enter comma-separated indices (e.g., 5,8,9): {Style.RESET_ALL}").strip()
                if indices_str.lower() == 'q':
                    print(f"{Fore.RED}{Style.BRIGHT}Exiting program.{Style.RESET_ALL}")
                    exit()
                try:
                    indices = [int(idx.strip()) for idx in indices_str.split(',')]
                    if all(1 <= idx <= total_videos for idx in indices) and len(indices) == len(set(indices)):
                        config['playlist_items'] = ','.join(map(str, indices))
                        break
                    else:
                        print(f"{Fore.RED}{Style.BRIGHT}Invalid indices. Ensure all are unique and between 1 and {total_videos}.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED}{Style.BRIGHT}Please enter valid integers separated by commas.{Style.RESET_ALL}")
    else:
        config['playlist_items'] = None

    while True:
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Enter subtitle language code (e.g., 'en' for English, 'ar' for Arabic):{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[q] Quit{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
        subtitle_lang = input(f"{Fore.YELLOW}{Style.BRIGHT}Language code: {Style.RESET_ALL}").strip().lower()

        if subtitle_lang == 'q':
            print(f"{Fore.RED}{Style.BRIGHT}Exiting program.{Style.RESET_ALL}")
            exit()

        if len(subtitle_lang) == 2 and subtitle_lang.isalpha():
            config['subtitle_lang'] = subtitle_lang
            break

        print(f"{Fore.RED}{Style.BRIGHT}Invalid language code. Please try again.\n{Style.RESET_ALL}")

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
        while True:
            print(f"\n{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{Style.BRIGHT}Enter target language code (e.g., 'ar', 'en'):{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[q] Quit{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{Style.BRIGHT}{'─'*60}{Style.RESET_ALL}")
            target_lang = input(f"{Fore.YELLOW}{Style.BRIGHT}Target language code: {Style.RESET_ALL}").strip().lower()

            if target_lang == 'q':
                print(f"{Fore.RED}{Style.BRIGHT}Exiting program.{Style.RESET_ALL}")
                exit()

            if len(target_lang) == 2 and target_lang.isalpha():
                config['target_lang'] = target_lang
                break

            print(f"{Fore.RED}{Style.BRIGHT}Invalid language code. Please try again.\n{Style.RESET_ALL}")
    else:
        config['translate_subtitles'] = False
        config['target_lang'] = None

    return config

# -----------------------------------------------
# Main Program Execution
# -----------------------------------------------
def main():
    os.makedirs("Downloaded", exist_ok=True)
    config = get_user_inputs()

    if config['content_type'] == 'single':
        output_template = 'Downloaded/%(title)s.%(ext)s'
    elif config['content_type'] == 'playlist':
        ydl_opts_flat = {
            'quiet': True,
            'extract_flat': True,
            'no_warnings': True,
            'logger': MinimalLogger()
        }
        print(f"{Fore.CYAN}{Style.BRIGHT}\nRetrieving playlist info...{Style.RESET_ALL}")
        with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
            info_flat = ydl.extract_info(config['link'], download=False)
            entries = info_flat.get('entries')
            total_videos = len(entries) if entries else 1
        num_digits = max(2, len(str(total_videos)))
        output_template = f"Downloaded/%(playlist_title)s/%(playlist_index)0{num_digits}d - %(title)s.%(ext)s"
    else:  # channel
        output_template = 'Downloaded/%(uploader)s/%(title)s.%(ext)s'

    ydl_opts = {
        'outtmpl': output_template,
        'progress_hooks': [lambda d: progress_hook(
            d,
            config['subtitle_lang'],
            config['translate_subtitles'],
            config['target_lang']
        )],
        'skip_download': True,
        'writesubtitles': True,
        'subtitleslangs': [config['subtitle_lang']],
        'writeautomaticsub': config['auto_subs'] == '1',
        'convertsubtitles': 'srt',
        'encoding': 'utf-8',
        'no_clean_info': True,
        'ignoreerrors': True,
        'retries': 10,
        'fragment_retries': 10,
        'socket_timeout': 60,
        'quiet': True,
        'no_warnings': True,
        'logger': MinimalLogger()
    }

    if config['content_type'] == 'single':
        ydl_opts['noplaylist'] = True

    if config['content_type'] == 'playlist' and config['playlist_items']:
        ydl_opts['playlist_items'] = config['playlist_items']

    print(f"\n{Fore.GREEN}{Style.BRIGHT}Starting subtitle download...{Style.RESET_ALL}\n")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([config['link']])
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}An error occurred during download:{Style.RESET_ALL} {e}")
        exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}{Style.BRIGHT}Program interrupted by user. Exiting.{Style.RESET_ALL}")
        exit()
