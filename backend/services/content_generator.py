import logging
from typing import Dict, List
from services.openai_service import OpenAIService
from services.prompts_service import PromptsService

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, openai_service: OpenAIService, prompts_service: PromptsService = None):
        self.openai = openai_service
        self.prompts_service = prompts_service or PromptsService()
    
    async def generate_all_content(
        self,
        transcript: str,
        transcript_with_timecodes: List[dict],
        guest_name: str,
        guest_title: str,
        guest_company: str,
        guest_linkedin: str,
        video_title: str = "",
        video_duration: float = 0
    ) -> Dict:
        """Generate all content types for the podcast episode"""
        logger.info(f"Generating all content for guest: {guest_name}")
        
        # Generate all content in parallel where possible (using asyncio.gather would be ideal)
        # For now, generating sequentially to ensure quality
        
        youtube_summary = await self.generate_youtube_summary(
            transcript, guest_name, guest_title, guest_company
        )
        
        blog_post = await self.generate_blog_post(
            transcript, guest_name, guest_title, guest_company, guest_linkedin
        )
        
        clickbait_titles = await self.generate_clickbait_titles(
            transcript, guest_name, guest_company
        )
        
        two_line_summary = await self.generate_two_line_summary(transcript)
        
        quotes = await self.generate_quotes(transcript_with_timecodes)
        
        chapter_timestamps = await self.generate_chapter_timestamps(
            transcript_with_timecodes, video_duration
        )
        
        linkedin_post = await self.generate_linkedin_post(
            transcript, guest_name, guest_title, guest_company
        )
        
        return {
            'youtube_summary': youtube_summary,
            'blog_post': blog_post,
            'clickbait_titles': clickbait_titles,
            'two_line_summary': two_line_summary,
            'quotes': quotes,
            'chapter_timestamps': chapter_timestamps,
            'linkedin_post': linkedin_post
        }
    
    async def generate_youtube_summary(
        self, transcript: str, guest_name: str, guest_title: str, guest_company: str
    ) -> str:
        """Generate 3-paragraph YouTube summary"""
        prompt = self.prompts_service.format_prompt(
            'youtube_summary',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            transcript=transcript
        )
        
        return await self.openai.generate_text(prompt, max_tokens=600, temperature=0.7)
    
    async def generate_blog_post(
        self, transcript: str, guest_name: str, guest_title: str, 
        guest_company: str, guest_linkedin: str
    ) -> str:
        """Generate 2000-word blog post with LinkedIn hyperlink in first paragraph"""
        prompt = self.prompts_service.format_prompt(
            'blog_post',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            guest_linkedin=guest_linkedin,
            transcript=transcript
        )
        
        return await self.openai.generate_text(prompt, max_tokens=2500, temperature=0.7)
    
    async def generate_clickbait_titles(
        self, transcript: str, guest_name: str, guest_company: str
    ) -> List[str]:
        """Generate 20 clickbait titles under 100 characters, featuring name and company"""
        prompt = self.prompts_service.format_prompt(
            'clickbait_titles',
            guest_name=guest_name,
            guest_company=guest_company,
            transcript=transcript
        )
        
        response = await self.openai.generate_text(prompt, max_tokens=800, temperature=0.8)
        
        # Parse titles from response
        titles = []
        for line in response.split('\n'):
            line = line.strip()
            if line and len(line) > 0:
                # Remove numbering if present
                if line[0].isdigit() and ('.' in line[:3] or ')' in line[:3]):
                    line = line.split('.', 1)[-1].strip()
                    line = line.split(')', 1)[-1].strip()
                if line and len(line) <= 100:
                    titles.append(line)
        
        # Ensure we have exactly 20 titles
        while len(titles) < 20:
            titles.append(f"Insights from {guest_name} at {guest_company}")
        
        return titles[:20]
    
    async def generate_two_line_summary(self, transcript: str) -> str:
        """Generate a two-line summary of the episode"""
        prompt = self.prompts_service.format_prompt(
            'two_line_summary',
            transcript=transcript
        )
        
        return await self.openai.generate_text(prompt, max_tokens=200, temperature=0.7)
    
    async def generate_quotes(self, transcript_with_timecodes: List[dict]) -> List[str]:
        """Generate 20 notable quotes from the episode"""
        prompt = self.prompts_service.format_prompt(
            'quotes',
            transcript_with_timecodes=transcript_with_timecodes
        )
        
        response = await self.openai.generate_text(prompt, max_tokens=1000, temperature=0.6)
        
        # Parse quotes from response
        quotes = []
        for line in response.split('\n'):
            line = line.strip()
            if line and len(line) > 0:
                # Remove numbering if present
                if line[0].isdigit() and ('.' in line[:3] or ')' in line[:3]):
                    line = line.split('.', 1)[-1].strip()
                    line = line.split(')', 1)[-1].strip()
                if line:
                    quotes.append(line)
        
        # Ensure we have exactly 20 quotes
        while len(quotes) < 20:
            quotes.append("Notable insight from the episode")
        
        return quotes[:20]
    
    async def generate_linkedin_post(
        self, transcript: str, guest_name: str, guest_title: str, guest_company: str
    ) -> str:
        """Generate LinkedIn post with guest description, 3 key takeaways, and CTA"""
        prompt = self.prompts_service.format_prompt(
            'linkedin_post',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            transcript=transcript
        )
        
        return await self.openai.generate_text(prompt, max_tokens=800, temperature=0.7)
    
    async def generate_chapter_timestamps(
        self, transcript_with_timecodes: List[dict], video_duration: float
    ) -> List[str]:
        """Generate YouTube-ready chapter timestamps"""
        prompt = self.prompts_service.format_prompt(
            'chapter_timestamps',
            transcript_with_timecodes=transcript_with_timecodes,
            video_duration=video_duration
        )
        
        response = await self.openai.generate_text(prompt, max_tokens=600, temperature=0.7)
        
        # Parse timestamps
        timestamps = []
        for line in response.split('\n'):
            line = line.strip()
            if line and ' - ' in line:
                timestamps.append(line)
        
        # Sort timestamps by time if needed
        timestamps.sort(key=lambda x: self._parse_timestamp(x.split(' - ')[0]))
        
        return timestamps if timestamps else ["00:00:00 - Introduction"]
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _parse_timestamp(self, timestamp_str: str) -> int:
        """Parse HH:MM:SS to total seconds"""
        try:
            parts = timestamp_str.split(':')
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return int(parts[0])
        except:
            return 0
    
    def _format_transcript_for_chapters(self, transcript_with_timecodes: List[dict]) -> str:
        """Format transcript for chapter generation"""
        lines = []
        for tc in transcript_with_timecodes[::10]:  # Sample every 10th entry for efficiency
            timestamp = self._format_timestamp(tc['start'])
            lines.append(f"[{timestamp}] {tc['text']}")
        return "\n".join(lines)

