# Youtube-Downloader

**YouTube Video & Subtitle Downloader with Translation**

A CLI tool to download YouTube videos and playlists with subtitle extraction, conversion, cleaning, and translation (with RTL support for Arabic).

This Python program downloads videos (or audio) from YouTube—including entire playlists and channels. It lets you choose video quality, download subtitles (both manual and auto-generated), convert them from VTT to SRT, clean duplicates, and even translate subtitles (with proper right-to-left formatting for languages like Arabic). Built using `yt-dlp` and `googletrans`, it’s designed for automated, hands-off operation once you provide your download preferences.

## Improved

### **Playlist Video Selection**
- For playlists, choose to download all videos, a range (e.g., videos 5 to 30), or specific videos (e.g., videos 5, 8, 9).

### **Subtitle Handling**
- Download manual or auto-generated subtitles.
- Convert VTT subtitles to SRT using FFmpeg.
- Clean duplicate subtitle lines.
- Translate subtitles to a target language with proper right-to-left formatting (for languages like Arabic).

### **Robust Error Handling**
- Supports automatic retries, increased socket timeout, and error skipping to reliably download large playlists.

### **Comments and Colors**
- Both scripts now have comments and output colors that exactly match the provided code segment.
- The comment style uses section headers with `---` lines and numbered sections where appropriate (e.g., `# 1) Import colorama...`).
- The color usage includes:
  - `Fore.RED` for errors
  - `Fore.GREEN` for success messages
  - `Fore.CYAN` for prompts/info
  - `Fore.YELLOW` for user input cues
  - `Fore.MAGENTA` for filenames
- All with `Style.BRIGHT` where applicable, matching the provided code.

## Notes
- For playlist download, you have to use the playlist link. If you use a video link from a playlist, it will not work.
- The script's translation works very well for short videos. However, for long videos, you may encounter this error:
```Error translating subtitles: The read operation timed out```
- This issue does not affect single long video downloads.









