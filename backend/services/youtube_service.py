import yt_dlp
import os
import logging
from typing import Dict, List, Optional
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import re

logger = logging.getLogger(__name__)

class YouTubeService:
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        # Cookie file paths (in order of preference)
        # Resolve path relative to backend directory (parent of services)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cookies_dir = os.path.join(backend_dir, "cookies")
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
    
    def _get_cookies_file_path(self) -> Optional[str]:
        """Get cookie file path, checking multiple locations in priority order"""
        # 1. Check uploaded cookies file first
        if os.path.exists(self.uploaded_cookies_path):
            logger.info(f"Found uploaded cookies file: {self.uploaded_cookies_path}")
            return self.uploaded_cookies_path
        
        # 2. Check environment variable (backward compatibility)
        env_cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', None)
        if env_cookies_file and os.path.exists(env_cookies_file):
            logger.info(f"Found cookies file from env var: {env_cookies_file}")
            return env_cookies_file
        
        return None
    
    def _build_ydl_opts(self, output_path: str, use_cookies: bool = True) -> dict:
        """Build yt-dlp options with cookie support"""
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
                    'player_client': ['android', 'ios', 'web'],  # Try multiple clients
                }
            },
            # Retry options
            'retries': 10,
            'fragment_retries': 10,
            'ignoreerrors': False,
        }
        
        if use_cookies:
            # Hybrid cookie strategy (in priority order):
            # 1. Try browser cookies first (chrome, firefox, edge)
            # 2. Fall back to uploaded cookies file
            # 3. Fall back to env var (backward compatibility)
            
            cookies_browser = os.getenv('YOUTUBE_COOKIES_BROWSER', None)
            
            # Strategy 1: Browser cookies (automatic extraction)
            if cookies_browser:
                # Use explicit browser setting from env
                ydl_opts['cookiesfrombrowser'] = cookies_browser.split(',')
                logger.info(f"Using cookies from browser (env): {cookies_browser}")
            else:
                # Try to automatically extract from browsers (in order: chrome, firefox, edge)
                browsers_to_try = ['chrome', 'firefox', 'edge']
                browser_used = None
                for browser in browsers_to_try:
                    try:
                        # Test if we can use this browser's cookies
                        ydl_opts['cookiesfrombrowser'] = [browser]
                        browser_used = browser
                        logger.info(f"Attempting to use {browser} cookies automatically")
                        break
                    except Exception as e:
                        logger.debug(f"Could not use {browser} cookies: {e}")
                        continue
                
                # If no browser worked, try cookies file
                if not browser_used:
                    cookies_file = self._get_cookies_file_path()
                    if cookies_file:
                        ydl_opts.pop('cookiesfrombrowser', None)  # Remove if set
                        ydl_opts['cookiefile'] = cookies_file
                        logger.info(f"Using cookies file (fallback): {cookies_file}")
                    else:
                        logger.warning("No cookies available (no browser or file found)")
        
        return ydl_opts
    
    async def download_audio(self, youtube_url: str) -> Optional[str]:
        """Download YouTube video as MP3 and return file path"""
        try:
            video_id = self._extract_video_id(youtube_url)
            output_path = os.path.join(self.upload_dir, f"{video_id}.%(ext)s")
            
            # Try with cookies first
            strategies = [
                (True, "with cookies"),
                (False, "without cookies (fallback)"),
            ]
            
            last_error = None
            for use_cookies, strategy_name in strategies:
                try:
                    logger.info(f"Attempting download {strategy_name}")
                    ydl_opts = self._build_ydl_opts(output_path, use_cookies=use_cookies)
                    
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([youtube_url])
                    
                    # If we get here, download succeeded
                    break
                except Exception as e:
                    error_msg = str(e)
                    last_error = e
                    logger.warning(f"Download failed {strategy_name}: {error_msg}")
                    
                    # If it's a bot detection error and we haven't tried without cookies yet, continue
                    if "bot" in error_msg.lower() or "sign in" in error_msg.lower():
                        if use_cookies:
                            logger.info("Bot detection error with cookies, trying without cookies...")
                            continue
                    # For other errors, re-raise immediately
                    if not use_cookies:
                        raise
            
            # Return the path to the MP3 file
            mp3_path = os.path.join(self.upload_dir, f"{video_id}.mp3")
            if os.path.exists(mp3_path):
                logger.info(f"Successfully downloaded audio to {mp3_path}")
                return mp3_path
            else:
                logger.warning(f"MP3 file not found at expected path: {mp3_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}", exc_info=True)
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
        """Get video metadata using yt-dlp"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'referer': 'https://www.youtube.com/',
                'extractor_args': {
                    'youtube': {
                        'skip': ['dash', 'hls'],
                        'player_client': ['android', 'ios', 'web'],
                    }
                },
            }
            
            # Cookie support - use same hybrid strategy as download
            cookies_browser = os.getenv('YOUTUBE_COOKIES_BROWSER', None)
            
            if cookies_browser:
                ydl_opts['cookiesfrombrowser'] = cookies_browser.split(',')
                logger.debug(f"Using cookies from browser (env) for video info: {cookies_browser}")
            else:
                # Try browser cookies automatically
                browsers_to_try = ['chrome', 'firefox', 'edge']
                browser_used = None
                for browser in browsers_to_try:
                    try:
                        ydl_opts['cookiesfrombrowser'] = [browser]
                        browser_used = browser
                        logger.debug(f"Using {browser} cookies for video info")
                        break
                    except Exception:
                        continue
                
                # Fall back to cookies file if no browser worked
                if not browser_used:
                    cookies_file = self._get_cookies_file_path()
                    if cookies_file:
                        ydl_opts.pop('cookiesfrombrowser', None)
                        ydl_opts['cookiefile'] = cookies_file
                        logger.debug(f"Using cookies file for video info: {cookies_file}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return {
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0)
                }
        except Exception as e:
            logger.warning(f"Could not get video info: {str(e)}")
            return {'title': '', 'duration': 0}
