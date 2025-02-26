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
