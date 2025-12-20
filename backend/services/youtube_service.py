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
            # Cookie support - try multiple methods
            cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', None)
            cookies_browser = os.getenv('YOUTUBE_COOKIES_BROWSER', None)
            
            # Try cookies from browser first (most reliable)
            if cookies_browser:
                ydl_opts['cookiesfrombrowser'] = cookies_browser.split(',')
                logger.info(f"Using cookies from browser: {cookies_browser}")
            elif cookies_file and os.path.exists(cookies_file):
                ydl_opts['cookiefile'] = cookies_file
                logger.info(f"Using cookies file: {cookies_file}")
            else:
                # Try to automatically use Chrome cookies (most common)
                try:
                    ydl_opts['cookiesfrombrowser'] = ['chrome']
                    logger.info("Attempting to use Chrome cookies automatically")
                except Exception as e:
                    logger.warning(f"Could not use Chrome cookies: {e}")
        
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
            
            # Cookie support - try multiple methods
            cookies_file = os.getenv('YOUTUBE_COOKIES_FILE', None)
            cookies_browser = os.getenv('YOUTUBE_COOKIES_BROWSER', None)
            
            if cookies_browser:
                ydl_opts['cookiesfrombrowser'] = cookies_browser.split(',')
            elif cookies_file and os.path.exists(cookies_file):
                ydl_opts['cookiefile'] = cookies_file
            else:
                # Try to automatically use Chrome cookies
                try:
                    ydl_opts['cookiesfrombrowser'] = ['chrome']
                except Exception:
                    pass  # Continue without cookies if not available
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                return {
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0)
                }
        except Exception as e:
            logger.warning(f"Could not get video info: {str(e)}")
            return {'title': '', 'duration': 0}

