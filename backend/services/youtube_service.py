# import yt_dlp  # Commented out - replaced with pytube
from pytube import YouTube
import os
import logging
from typing import Dict, List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re
import subprocess

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        # Cookie file paths (in order of preference) - COMMENTED OUT: pytube doesn't support cookies
        # Resolve path relative to backend directory (parent of services)
        # backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # self.cookies_dir = os.path.join(backend_dir, "cookies")
        # Ensure cookies directory exists
        # os.makedirs(self.cookies_dir, exist_ok=True)
        # self.uploaded_cookies_path = os.path.join(self.cookies_dir, "cookies.txt")
        
    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    # COMMENTED OUT: Cookie validation - pytube doesn't support cookies
    # def _validate_cookie_file(self, cookie_path: str) -> bool:
    #     """Validate that the cookie file exists and has valid content"""
    #     try:
    #         if not os.path.exists(cookie_path):
    #             logger.error(f"Cookie file does not exist: {cookie_path}")
    #             return False
    #         
    #         file_size = os.path.getsize(cookie_path)
    #         if file_size == 0:
    #             logger.error(f"Cookie file is empty: {cookie_path}")
    #             return False
    #         
    #         # Read first few lines to check format
    #         with open(cookie_path, 'r', encoding='utf-8', errors='ignore') as f:
    #             first_lines = [f.readline().strip() for _ in range(5)]
    #             content = '\n'.join(first_lines)
    #             
    #             # Check for Netscape cookie format indicators
    #             # Valid formats: starts with # Netscape HTTP Cookie File, or has tab-separated cookie entries
    #             if '# Netscape HTTP Cookie File' in content:
    #                 logger.debug(f"Cookie file appears to be in Netscape format: {cookie_path}")
    #             elif '\t' in content:
    #                 # Tab-separated format (Netscape format without header)
    #                 logger.debug(f"Cookie file appears to be in tab-separated format: {cookie_path}")
    #             else:
    #                 logger.warning(f"Cookie file format may be invalid (no Netscape header or tabs): {cookie_path}")
    #                 # Still allow it, as yt-dlp might handle it
    #         
    #         logger.info(f"Cookie file validated: {cookie_path} (size: {file_size} bytes)")
    #         return True
    #     except Exception as e:
    #         logger.error(f"Error validating cookie file {cookie_path}: {str(e)}", exc_info=True)
    #         return False
    # 
    # def _get_cookies_file_path(self) -> Optional[str]:
    #     """Get cookie file path, checking multiple locations in priority order"""
    #     # 1. Check uploaded cookies file first
    #     abs_path = os.path.abspath(self.uploaded_cookies_path)
    #     if os.path.exists(abs_path):
    #         if self._validate_cookie_file(abs_path):
    #             file_size = os.path.getsize(abs_path)
    #             logger.info(f"Using uploaded cookies file: {abs_path} (size: {file_size} bytes)")
    #             return abs_path
    #         else:
    #             logger.error(f"Uploaded cookies file failed validation: {abs_path}")
    #     else:
    #         logger.warning(f"Uploaded cookies file not found at: {abs_path}")
    #     
    #     # 2. Check environment variable (backward compatibility)
    #     env_cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', None)
    #     if env_cookies_file:
    #         abs_env_path = os.path.abspath(env_cookies_file)
    #         if os.path.exists(abs_env_path):
    #             if self._validate_cookie_file(abs_env_path):
    #                 logger.info(f"Using cookies file from env var: {abs_env_path}")
    #                 return abs_env_path
    #             else:
    #                 logger.error(f"Cookies file from env var failed validation: {abs_env_path}")
    #         else:
    #             logger.debug(f"Cookies file from env var not found at: {abs_env_path}")
    #     
    #     logger.error("No valid cookies file found - YouTube downloads will likely fail with bot detection")
    #     return None
    # 
    # COMMENTED OUT: yt-dlp options builder - replaced with pytube
    # def _build_ydl_opts(self, output_path: str, use_cookies: bool = True) -> dict:
    #     """Build yt-dlp options with cookie support"""
    #     ydl_opts = {
    #         'format': 'bestaudio/best',
    #         'outtmpl': output_path,
    #         'postprocessors': [{
    #             'key': 'FFmpegExtractAudio',
    #             'preferredcodec': 'mp3',
    #             'preferredquality': '192',
    #         }],
    #         'quiet': False,
    #         'no_warnings': False,
    #         # Enhanced bot detection bypass
    #         'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    #         'referer': 'https://www.youtube.com/',
    #         'extractor_args': {
    #             'youtube': {
    #                 'skip': ['dash', 'hls'],
    #                 'player_client': ['android', 'ios', 'web'],  # Try multiple clients
    #             }
    #         },
    #         # Retry options
    #         'retries': 10,
    #         'fragment_retries': 10,
    #         'ignoreerrors': False,
    #     }
    #     
    #     if use_cookies:
    #         # Hybrid cookie strategy (in priority order):
    #         # 1. Uploaded cookies file (highest priority - user explicitly uploaded)
    #         # 2. Browser cookies (if env var set)
    #         # 3. Env var cookies file (backward compatibility)
    #         
    #         # Strategy 1: Check for uploaded cookies file first (highest priority)
    #         cookies_file = self._get_cookies_file_path()
    #         if cookies_file:
    #             ydl_opts['cookiefile'] = cookies_file
    #             # Add additional options for better cookie handling
    #             ydl_opts['no_check_certificate'] = False  # Ensure SSL verification is on
    #             logger.info(f"✓ Configured yt-dlp to use cookies file: {cookies_file}")
    #         else:
    #             # Strategy 2: Browser cookies (only if explicitly set via env)
    #             cookies_browser = os.getenv('YOUTUBE_COOKIES_BROWSER', None)
    #             if cookies_browser:
    #                 # Use explicit browser setting from env
    #                 ydl_opts['cookiesfrombrowser'] = cookies_browser.split(',')
    #                 logger.info(f"Using cookies from browser (env): {cookies_browser}")
    #             else:
    #                 logger.error("⚠️  NO COOKIES AVAILABLE - YouTube bot detection will likely fail!")
    #                 logger.error("   Please upload cookies.txt file via the web interface or set YOUTUBE_COOKIES_BROWSER env var")
    #     
    #     return ydl_opts
    
    async def download_audio(self, youtube_url: str) -> Optional[str]:
        """Download YouTube video as MP3 using pytube and return file path"""
        try:
            video_id = self._extract_video_id(youtube_url)
            mp3_path = os.path.join(self.upload_dir, f"{video_id}.mp3")
            
            logger.info(f"Attempting download with pytube for video: {youtube_url}")
            
            # Create YouTube object
            yt = YouTube(youtube_url)
            
            # Get the best audio stream
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            
            if not audio_stream:
                raise Exception("No audio stream available for this video")
            
            logger.info(f"Found audio stream: {audio_stream.abr} kbps, {audio_stream.mime_type}")
            
            # Download audio (pytube downloads as webm/mp4, we'll convert to mp3)
            temp_path = os.path.join(self.upload_dir, f"{video_id}.{audio_stream.subtype}")
            logger.info(f"Downloading audio to temporary file: {temp_path}")
            audio_stream.download(output_path=self.upload_dir, filename=f"{video_id}.{audio_stream.subtype}")
            
            # Convert to MP3 using ffmpeg if needed
            if audio_stream.subtype != 'mp3':
                logger.info(f"Converting {audio_stream.subtype} to MP3 using ffmpeg...")
                try:
                    # Use ffmpeg to convert to MP3
                    subprocess.run(
                        [
                            'ffmpeg', '-i', temp_path,
                            '-acodec', 'libmp3lame',
                            '-ab', '192k',
                            '-y',  # Overwrite output file
                            mp3_path
                        ],
                        check=True,
                        capture_output=True
                    )
                    # Remove temporary file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    logger.info(f"Successfully converted to MP3: {mp3_path}")
                except subprocess.CalledProcessError as e:
                    logger.error(f"FFmpeg conversion failed: {e.stderr.decode() if e.stderr else str(e)}")
                    # If conversion fails but we have the audio file, return it anyway
                    if os.path.exists(temp_path):
                        logger.warning(f"Conversion failed, but audio file exists. Returning original format.")
                        return temp_path
                    raise Exception(f"Failed to convert audio to MP3: {str(e)}")
                except FileNotFoundError:
                    logger.error("FFmpeg not found. Please install ffmpeg to convert audio to MP3.")
                    # If ffmpeg is not available but we have the audio file, return it
                    if os.path.exists(temp_path):
                        logger.warning(f"FFmpeg not found, but audio file exists. Returning original format.")
                        return temp_path
                    raise Exception("FFmpeg not found. Please install ffmpeg to convert audio to MP3.")
            else:
                # Already MP3, just rename if needed
                if temp_path != mp3_path and os.path.exists(temp_path):
                    os.rename(temp_path, mp3_path)
            
            # Verify MP3 file exists
            if os.path.exists(mp3_path):
                file_size = os.path.getsize(mp3_path)
                logger.info(f"✓ Successfully downloaded audio to {mp3_path} ({file_size} bytes)")
                return mp3_path
            else:
                raise Exception(f"MP3 file not found at expected path: {mp3_path}")
                
        except Exception as e:
            logger.error(f"Error downloading audio with pytube: {str(e)}", exc_info=True)
            raise Exception(f"Failed to download audio: {str(e)}")
    
    async def get_transcript(self, youtube_url: str) -> Dict:
        """Get transcript with timecodes from YouTube"""
        try:
            video_id = self._extract_video_id(youtube_url)
            
            # Try to get transcript
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            except Exception as e:
                logger.error(f"Error getting transcript: {str(e)}")
                raise Exception(f"Transcript not available for this video: {str(e)}")
            
            # Format transcript with timecodes
            transcript_with_timecodes = []
            full_transcript_text = ""
            
            for entry in transcript_list:
                text = entry['text'].strip()
                start = entry['start']
                duration = entry.get('duration', 0)
                
                transcript_with_timecodes.append({
                    'text': text,
                    'start': start,
                    'duration': duration,
                    'end': start + duration
                })
                full_transcript_text += text + " "
            
            # Get video info using yt-dlp
            video_info = await self._get_video_info(youtube_url)
            
            return {
                'transcript': full_transcript_text.strip(),
                'transcript_with_timecodes': transcript_with_timecodes,
                'title': video_info.get('title', ''),
                'duration': video_info.get('duration', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}", exc_info=True)
            raise
    
    async def _get_video_info(self, youtube_url: str) -> Dict:
        """Get video metadata using pytube"""
        try:
            yt = YouTube(youtube_url)
            # pytube provides title and length directly
            title = yt.title or ''
            duration = yt.length or 0  # Length is in seconds
            
            logger.debug(f"Got video info - Title: {title}, Duration: {duration}s")
            return {
                'title': title,
                'duration': duration
            }
        except Exception as e:
            logger.warning(f"Could not get video info with pytube: {str(e)}")
            return {'title': '', 'duration': 0}
