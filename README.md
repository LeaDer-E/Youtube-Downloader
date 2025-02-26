# Youtube-Downloader

A CLI tool to download YouTube videos and playlists with subtitle extraction, conversion, cleaning, and translation (with RTL support for Arabic).

## Features

- **Multiple Download Types:**  
  Choose between video (MP4) and audio (MP3).

- **Content Options:**  
  Download a single video, an entire playlist, or a channel.

- **Quality Selection:**  
  Interactively select from available video resolutions.

- **Subtitle Handling:**  
  - Download manual or auto-generated subtitles.  
  - Convert VTT subtitles to SRT using FFmpeg.  
  - Clean duplicate subtitle lines.  
  - Translate subtitles to a target language with proper right‑to‑left formatting (for languages like Arabic).

- **Robust Error Handling:**  
  Supports automatic retries, increased socket timeout, and error skipping to reliably download large playlists.

## Prerequisites

- **Python 3.7+**
- **FFmpeg:**  
  This tool uses FFmpeg to convert subtitle files from VTT to SRT.  
  - **Ubuntu/Debian:**  
    ```bash
    sudo apt update && sudo apt install ffmpeg
    ```
  - **Windows:**  
    Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) and add the `bin` folder to your system's PATH.
  - **macOS:**  
    Install via Homebrew:  
    ```bash
    brew install ffmpeg
    ```

## Installation

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/LeaDer-E/Youtube-Downloader.git
   cd Youtube-Downloader
2. Install Python Dependencies:
   ```bash
   pip install -r requirements.txt

## Usage
  Run the program from the command line:
  ```bash
  python3 your_script.py
  python3 Youtube\ Downloader.py
  ```
**Follow the interactive prompts to select:**
* Download type (Video or Audio)
* Content type (Single video, Playlist, or Channel)
* YouTube URL
* Video quality
* Subtitle download options (including conversion and translation and Auto Generator if needed)
Once you have answered all the prompts, the download process will start and run unattended.

## Future Enhancements
* **Configuration File:**
  Save user preferences (e.g., default quality, subtitle language).
* **Graphical Interface:**
  Develop a GUI version for ease of use.
* **Advanced Error Logging:**
  Write logs to a file for easier troubleshooting.
* **Batch Processing:**
  Support for scheduling multiple downloads.
* **Extended Language Support:**
  Integrate additional translation APIs for improved accuracy.
* **Progress Notifications:**
  Add desktop notifications or email alerts upon download completion.
* **Cloud Integration:**
  Automatically upload downloads to cloud storage services.

## License
  This project is licensed under the MIT License.

## Acknowledgments
* **yt-dlp** – For robust video downloading functionality.
* **googletrans** – For subtitle translation.
* **FFmpeg** – For subtitle conversion.
