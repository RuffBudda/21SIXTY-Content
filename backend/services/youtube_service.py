import yt_dlp
# from pytube import YouTube  # Commented out - replaced with yt-dlp due to HTTP 400 errors
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
        # Cookie file paths (in order of preference) - Re-enabled for yt-dlp bot detection bypass
        # Resolve path relative to backend directory (parent of services)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cookies_dir = os.path.join(backend_dir, "cookies")
        # Ensure cookies directory exists
        os.makedirs(self.cookies_dir, exist_ok=True)
        self.uploaded_cookies_path = os.path.join(self.cookies_dir, "cookies.txt")
        
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
    
    def _validate_cookie_file(self, cookie_path: str) -> bool:
        """Validate that the cookie file exists and has valid content"""
        try:
            if not os.path.exists(cookie_path):
                logger.error(f"Cookie file does not exist: {cookie_path}")
                return False
                
            file_size = os.path.getsize(cookie_path)
            if file_size == 0:
                logger.error(f"Cookie file is empty: {cookie_path}")
                return False
                
            # Read first few lines to check format
            with open(cookie_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_lines = [f.readline().strip() for _ in range(5)]
                content = '\n'.join(first_lines)
                
                # Check for Netscape cookie format indicators
                # Valid formats: starts with # Netscape HTTP Cookie File, or has tab-separated cookie entries
                if '# Netscape HTTP Cookie File' in content:
                    logger.debug(f"Cookie file appears to be in Netscape format: {cookie_path}")
                elif '\t' in content:
                    # Tab-separated format (Netscape format without header)
                    logger.debug(f"Cookie file appears to be in tab-separated format: {cookie_path}")
                else:
                    logger.warning(f"Cookie file format may be invalid (no Netscape header or tabs): {cookie_path}")
                    # Still allow it, as yt-dlp might handle it
            
            logger.info(f"Cookie file validated: {cookie_path} (size: {file_size} bytes)")
            return True
        except Exception as e:
            logger.error(f"Error validating cookie file {cookie_path}: {str(e)}", exc_info=True)
            return False
    
    def _get_cookies_file_path(self) -> Optional[str]:
        """Get cookie file path, checking multiple locations in priority order"""
        # 1. Check uploaded cookies file first
        abs_path = os.path.abspath(self.uploaded_cookies_path)
        if os.path.exists(abs_path):
            if self._validate_cookie_file(abs_path):
                file_size = os.path.getsize(abs_path)
                logger.info(f"✓ Using uploaded cookies file: {abs_path} (size: {file_size} bytes)")
                return abs_path
            else:
                logger.error(f"✗ Uploaded cookies file failed validation: {abs_path}")
        else:
            logger.debug(f"Uploaded cookies file not found at: {abs_path}")
        
        # 2. Check environment variable (backward compatibility)
        env_cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', None)
        if env_cookies_file:
            abs_env_path = os.path.abspath(env_cookies_file)
            if os.path.exists(abs_env_path):
                if self._validate_cookie_file(abs_env_path):
                    logger.info(f"✓ Using cookies file from env var: {abs_env_path}")
                    return abs_env_path
                else:
                    logger.error(f"✗ Cookies file from env var failed validation: {abs_env_path}")
            else:
                logger.debug(f"Cookies file from env var not found at: {abs_env_path}")
        
        logger.debug("No valid cookies file found - will attempt download without cookies (may fail for protected videos)")
        return None
    
    def _build_ydl_opts(self, output_path: str, use_cookies: bool = True) -> dict:
        """Build yt-dlp options with enhanced bot detection bypass and optional cookie support"""
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            # Enhanced bot detection bypass
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_client': ['android', 'ios', 'web'],  # Try multiple clients as fallback
                }
            },
            # Retry options for network issues
            'retries': 10,
            'fragment_retries': 10,
            'ignoreerrors': False,
            # Additional bot detection bypass strategies
            'no_check_certificate': False,  # Ensure SSL verification is on
            'prefer_insecure': False,
            'socket_timeout': 30,
        }
        
        if use_cookies:
            # Hybrid cookie strategy (in priority order):
            # 1. Uploaded cookies file (highest priority - user explicitly uploaded)
            # 2. Browser cookies (if env var set)
            # 3. Env var cookies file (backward compatibility)
            
            # Strategy 1: Check for uploaded cookies file first (highest priority)
            cookies_file = self._get_cookies_file_path()
            if cookies_file:
                ydl_opts['cookiefile'] = cookies_file
                logger.info(f"✓ Configured yt-dlp to use cookies file: {cookies_file}")
            else:
                # Strategy 2: Browser cookies (only if explicitly set via env)
                cookies_browser = os.getenv('YOUTUBE_COOKIES_BROWSER', None)
                if cookies_browser:
                    # Use explicit browser setting from env
                    ydl_opts['cookiesfrombrowser'] = cookies_browser.split(',')
                    logger.info(f"✓ Using cookies from browser (env): {cookies_browser}")
                else:
                    logger.debug("⚠️  No cookies available - will attempt download without cookies")
                    logger.debug("   Some videos may require cookies. Upload cookies.txt file or set YOUTUBE_COOKIES_BROWSER env var")
        
        return ydl_opts
    
    # COMMENTED OUT: YouTube download and conversion feature - now using audio file upload instead
    # async def download_audio(self, youtube_url: str) -> Optional[str]:
    #     """Download YouTube video as MP3 using yt-dlp and return file path"""
    #     try:
    #         video_id = self._extract_video_id(youtube_url)
    #         mp3_path = os.path.join(self.upload_dir, f"{video_id}.mp3")
    #         
    #         logger.info(f"Attempting download with yt-dlp for video: {youtube_url}")
    #         
    #         # Build yt-dlp options with enhanced bot detection bypass and optional cookie support
    #         # Note: FFmpegExtractAudio postprocessor will convert to .mp3, so we set outtmpl without extension
    #         base_output_path = os.path.join(self.upload_dir, video_id)
    #         ydl_opts = self._build_ydl_opts(
    #             output_path=base_output_path + '.%(ext)s',
    #             use_cookies=True  # Try to use cookies if available, but works without them for most videos
    #         )
    #         
    #         # Use yt-dlp to download and convert to MP3
    #         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    #             try:
    #                 ydl.download([youtube_url])
    #             except yt_dlp.utils.DownloadError as e:
    #                 error_msg = str(e)
    #                 logger.error(f"yt-dlp download error: {error_msg}")
    #                 # Check if it's a bot detection error
    #                 if 'Sign in to confirm you\'re not a bot' in error_msg or 'bot' in error_msg.lower():
    #                     logger.warning("⚠️  Bot detection encountered. This video requires authentication.")
    #                     logger.warning("   Solution: Upload cookies.txt file via web interface or set YOUTUBE_COOKIES_BROWSER env var")
    #                     logger.warning("   See: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp")
    #                 elif 'HTTP Error 400' in error_msg:
    #                     logger.warning("⚠️  HTTP 400 error - YouTube API may have changed. Try updating yt-dlp: pip install --upgrade yt-dlp")
    #                 raise Exception(f"Failed to download audio: {error_msg}")
    #         
    #         # FFmpegExtractAudio postprocessor should have created .mp3 file
    #         # Check if MP3 file exists at expected path
    #         if os.path.exists(mp3_path):
    #             file_size = os.path.getsize(mp3_path)
    #             logger.info(f"Successfully downloaded audio to {mp3_path} ({file_size} bytes)")
    #             return mp3_path
    #         
    #         # yt-dlp might have created the file with a slightly different name, check for variations
    #         possible_files = [f for f in os.listdir(self.upload_dir) if f.startswith(video_id)]
    #         if possible_files:
    #             # Find .mp3 file first
    #             mp3_files = [f for f in possible_files if f.endswith('.mp3')]
    #             if mp3_files:
    #                 found_file = os.path.join(self.upload_dir, mp3_files[0])
    #                 if found_file != mp3_path:
    #                     logger.info(f"Found downloaded file: {found_file}, renaming to {mp3_path}")
    #                     os.rename(found_file, mp3_path)
    #                 return mp3_path
    #             # If no .mp3, check for other audio formats (shouldn't happen with postprocessor)
    #             found_file = os.path.join(self.upload_dir, possible_files[0])
    #             logger.warning(f"Expected .mp3 file not found, but found: {found_file}")
    #             raise Exception(f"MP3 conversion failed. File exists but is not MP3: {found_file}")
    #         
    #         raise Exception(f"MP3 file not found at expected path: {mp3_path}")
    #             
    #     except Exception as e:
    #         logger.error(f"Error downloading audio with yt-dlp: {str(e)}", exc_info=True)
    #         raise Exception(f"Failed to download audio: {str(e)}")
    
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
        """Get video metadata using yt-dlp"""
        try:
            # Build options with cookie support for video info extraction
            base_output_path = os.path.join(self.upload_dir, "temp_info")
            ydl_opts = self._build_ydl_opts(
                output_path=base_output_path + '.%(ext)s',
                use_cookies=True
            )
            # Override for info extraction only
            ydl_opts.update({
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
            })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                title = info.get('title', '') if info else ''
                duration = info.get('duration', 0) if info else 0  # Duration is in seconds
                
                logger.debug(f"Got video info - Title: {title}, Duration: {duration}s")
                return {
                    'title': title,
                    'duration': duration
                }
        except Exception as e:
            logger.warning(f"Could not get video info with yt-dlp: {str(e)}")
            return {'title': '', 'duration': 0}
