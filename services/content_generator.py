import logging
from typing import Dict, List
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, openai_service: OpenAIService):
        self.openai = openai_service
    
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
        
        return {
            'youtube_summary': youtube_summary,
            'blog_post': blog_post,
            'clickbait_titles': clickbait_titles,
            'two_line_summary': two_line_summary,
            'quotes': quotes,
            'chapter_timestamps': chapter_timestamps
        }
    
    async def generate_youtube_summary(
        self, transcript: str, guest_name: str, guest_title: str, guest_company: str
    ) -> str:
        """Generate 3-paragraph YouTube summary"""
        prompt = f"""You are writing a summary for a YouTube video description for The Dollar Diaries podcast.

Guest Information:
- Name: {guest_name}
- Title: {guest_title}
- Company: {guest_company}

Transcript:
{transcript[:8000]}  # Limit transcript length for token efficiency

Please create a compelling 3-paragraph summary for YouTube that:
1. Introduces the guest and their background in the first paragraph
2. Highlights the key topics and insights discussed in the second paragraph
3. Teases what viewers will learn or take away in the third paragraph

Make it engaging, professional, and suitable for a YouTube video description."""
        
        return await self.openai.generate_text(prompt, max_tokens=600, temperature=0.7)
    
    async def generate_blog_post(
        self, transcript: str, guest_name: str, guest_title: str, 
        guest_company: str, guest_linkedin: str
    ) -> str:
        """Generate 2000-word blog post with LinkedIn hyperlink in first paragraph"""
        prompt = f"""You are writing a comprehensive 2000-word blog post based on a podcast episode transcript from The Dollar Diaries podcast.

Guest Information:
- Name: {guest_name}
- Title: {guest_title}
- Company: {guest_company}
- LinkedIn: {guest_linkedin}

Transcript:
{transcript[:12000]}  # Use more of transcript for longer blog post

Instructions:
1. Write a comprehensive 2000-word blog post based on this episode
2. In the FIRST PARAGRAPH, hyperlink the guest's name to their LinkedIn profile using markdown format: [Name](LinkedIn_URL)
3. Structure the blog post with engaging subheadings
4. Include key insights, quotes, and takeaways from the episode
5. Make it valuable and readable for the audience
6. End with a strong conclusion

Format the LinkedIn hyperlink in the first paragraph like this:
In this episode of The Dollar Diaries, we speak with [{guest_name}]({guest_linkedin}), {guest_title} at {guest_company}, about...

Write the full blog post now:"""
        
        return await self.openai.generate_text(prompt, max_tokens=2500, temperature=0.7)
    
    async def generate_clickbait_titles(
        self, transcript: str, guest_name: str, guest_company: str
    ) -> List[str]:
        """Generate 20 clickbait titles under 100 characters, featuring name and company"""
        prompt = f"""Generate 20 clickbait-style titles for a podcast episode, each under 100 characters.

Guest: {guest_name} from {guest_company}

Transcript excerpt:
{transcript[:6000]}

Requirements:
- Each title must be under 100 characters
- Include the guest's name ({guest_name}) and/or company ({guest_company})
- Make them compelling and click-worthy
- Based on the actual content of the episode
- Number each title from 1 to 20
- Return only the titles, one per line, without any other text

Format:
1. Title here
2. Title here
..."""
        
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
        prompt = f"""Create a concise two-line summary of this podcast episode.

Transcript:
{transcript[:6000]}

Write exactly two lines that capture the essence of the episode. Make it engaging and informative.

Format:
Line 1
Line 2"""
        
        return await self.openai.generate_text(prompt, max_tokens=200, temperature=0.7)
    
    async def generate_quotes(self, transcript_with_timecodes: List[dict]) -> List[str]:
        """Generate 20 notable quotes from the episode"""
        # Create a readable format from transcript with timecodes
        transcript_text = "\n".join([
            f"[{self._format_timestamp(tc['start'])}] {tc['text']}"
            for tc in transcript_with_timecodes[:200]  # Limit for efficiency
        ])
        
        prompt = f"""Extract 20 of the most notable, insightful, or quotable statements from this podcast transcript.

Transcript with timestamps:
{transcript_text}

Requirements:
- Select the 20 most impactful quotes
- They should be complete thoughts or statements
- Include the timestamp in format [HH:MM:SS] before each quote
- Number each quote from 1 to 20
- Return only the quotes, one per line

Format:
1. [HH:MM:SS] Quote text here
2. [HH:MM:SS] Quote text here
..."""
        
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
    
    async def generate_chapter_timestamps(
        self, transcript_with_timecodes: List[dict], video_duration: float
    ) -> List[str]:
        """Generate YouTube-ready chapter timestamps"""
        # Analyze transcript to identify natural breaks/topics
        # For now, we'll create timestamps at regular intervals with AI-generated chapter titles
        
        prompt = f"""Analyze this podcast transcript and create YouTube chapter timestamps.

Transcript with timecodes (showing first 300 entries):
{self._format_transcript_for_chapters(transcript_with_timecodes[:300])}

Video duration: {self._format_timestamp(video_duration)} seconds

Create YouTube-ready chapter timestamps that:
1. Identify natural topic breaks in the conversation
2. Use format: 00:00:00 - Chapter Title
3. Create 8-12 meaningful chapters
4. Each chapter title should be descriptive and engaging
5. Timestamps should align with topic transitions

Return only the timestamps in this exact format:
00:00:00 - Chapter Title 1
00:05:30 - Chapter Title 2
..."""
        
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

