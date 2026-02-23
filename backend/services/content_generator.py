import logging
from typing import Dict, List, Tuple, Optional, Any
from services.openai_service import OpenAIService
from services.prompts_service import PromptsService
from utils.cost_calculator import calculate_token_cost
from database.repository import Repository
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class ContentGenerator:
    def __init__(self, openai_service: OpenAIService, prompts_service: PromptsService = None, 
                 repository: Optional[Repository] = None, db_session: Optional[AsyncSession] = None):
        self.openai = openai_service
        self.prompts_service = prompts_service or PromptsService()
        self.repository = repository
        self.db_session = db_session
    
    # Database-integrated generation methods
    async def generate_all_content_with_db(
        self,
        session_id: str,
        transcript: str,
        transcript_with_timecodes: List[dict],
        guest_name: str,
        guest_title: str,
        guest_company: str,
        guest_linkedin: str,
        video_title: str = "",
        video_duration: float = 0
    ) -> Tuple[Dict, Dict]:
        """Generate all content with database persistence of prompts and tokens"""
        if not self.repository:
            logger.warning("Repository not initialized - falling back to generate_all_content")
            return await self.generate_all_content(
                transcript, transcript_with_timecodes, guest_name, guest_title,
                guest_company, guest_linkedin, video_title, video_duration
            )
        
        logger.info(f"Generating all content for session {session_id}, guest: {guest_name}")
        
        content_dict = {}
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost = 0.0
        model_used = self.openai.model
        
        content_types = [
            ('youtube_summary', self._generate_youtube_summary_with_db_impl, 
             {'transcript': transcript, 'guest_name': guest_name, 'guest_title': guest_title, 'guest_company': guest_company}),
            ('blog_post', self._generate_blog_post_with_db_impl,
             {'transcript': transcript, 'guest_name': guest_name, 'guest_title': guest_title, 'guest_company': guest_company, 'guest_linkedin': guest_linkedin}),
            ('clickbait_titles', self._generate_clickbait_titles_with_db_impl,
             {'transcript': transcript, 'guest_name': guest_name, 'guest_company': guest_company}),
            ('two_line_summary', self._generate_two_line_summary_with_db_impl,
             {'transcript': transcript}),
            ('quotes', self._generate_quotes_with_db_impl,
             {'transcript_with_timecodes': transcript_with_timecodes}),
            ('chapter_timestamps', self._generate_chapter_timestamps_with_db_impl,
             {'transcript_with_timecodes': transcript_with_timecodes, 'video_duration': video_duration}),
            ('linkedin_post', self._generate_linkedin_post_with_db_impl,
             {'transcript': transcript, 'guest_name': guest_name, 'guest_title': guest_title, 'guest_company': guest_company, 'guest_linkedin': guest_linkedin}),
            ('keywords', self._generate_keywords_with_db_impl,
             {'transcript': transcript, 'guest_name': guest_name, 'guest_title': guest_title, 'guest_company': guest_company}),
        ]
        
        for content_type, generator_func, params in content_types:
            try:
                result = await generator_func(session_id, **params)
                content_dict[content_type] = result['content']
                total_prompt_tokens += result['prompt_tokens']
                total_completion_tokens += result['completion_tokens']
                total_cost += result['cost_usd']
            except Exception as e:
                logger.error(f"Error generating {content_type}: {str(e)}", exc_info=True)
                raise
        
        # Generate hashtags from keywords
        content_dict['hashtags'] = self.generate_hashtags_from_keywords(content_dict.get('keywords', ''))
        
        # Save generated content to database
        await self.repository.save_generated_content(session_id, content_dict, model_used)
        
        token_usage = {
            'prompt_tokens': total_prompt_tokens,
            'completion_tokens': total_completion_tokens,
            'total_tokens': total_prompt_tokens + total_completion_tokens,
            'model': model_used,
            'cost_usd': round(total_cost, 4)
        }
        
        return content_dict, token_usage
    
    async def _generate_youtube_summary_with_db_impl(self, session_id: str, transcript: str, 
                                                      guest_name: str, guest_title: str, guest_company: str) -> Dict:
        """Generate YouTube summary with DB persistence"""
        return await self._generate_content_with_db('youtube_summary', session_id, 
                                                    transcript=transcript, max_tokens=600, temperature=0.7,
                                                    guest_name=guest_name, guest_title=guest_title, guest_company=guest_company)
    
    async def _generate_blog_post_with_db_impl(self, session_id: str, transcript: str, 
                                                guest_name: str, guest_title: str, guest_company: str, 
                                                guest_linkedin: str) -> Dict:
        """Generate blog post with DB persistence"""
        return await self._generate_content_with_db('blog_post', session_id,
                                                    transcript=transcript, max_tokens=2500, temperature=0.7,
                                                    guest_name=guest_name, guest_title=guest_title, 
                                                    guest_company=guest_company, guest_linkedin=guest_linkedin)
    
    async def _generate_clickbait_titles_with_db_impl(self, session_id: str, transcript: str,
                                                       guest_name: str, guest_company: str) -> Dict:
        """Generate clickbait titles with DB persistence"""
        result = await self._generate_content_with_db('clickbait_titles', session_id,
                                                      transcript=transcript, max_tokens=800, temperature=0.8,
                                                      guest_name=guest_name, guest_company=guest_company,
                                                      parse_list=True, default_items=20,
                                                      default_item=f"Insights from {guest_name} at {guest_company}")
        # Ensure titles don't exceed 100 chars
        result['content'] = [t[:100] for t in result['content']]
        return result
    
    async def _generate_two_line_summary_with_db_impl(self, session_id: str, transcript: str) -> Dict:
        """Generate two-line summary with DB persistence"""
        return await self._generate_content_with_db('two_line_summary', session_id,
                                                    transcript=transcript, max_tokens=200, temperature=0.7)
    
    async def _generate_quotes_with_db_impl(self, session_id: str, transcript_with_timecodes: List[dict]) -> Dict:
        """Generate quotes with DB persistence"""
        result = await self._generate_content_with_db('quotes', session_id,
                                                      transcript_with_timecodes=transcript_with_timecodes,
                                                      max_tokens=1000, temperature=0.6,
                                                      parse_list=True, default_items=20,
                                                      default_item="Notable insight from the episode")
        return result
    
    async def _generate_chapter_timestamps_with_db_impl(self, session_id: str, 
                                                         transcript_with_timecodes: List[dict],
                                                         video_duration: float) -> Dict:
        """Generate chapter timestamps with DB persistence"""
        result = await self._generate_content_with_db('chapter_timestamps', session_id,
                                                      transcript_with_timecodes=transcript_with_timecodes,
                                                      video_duration=video_duration,
                                                      max_tokens=600, temperature=0.7,
                                                      parse_timestamps=True)
        return result
    
    async def _generate_linkedin_post_with_db_impl(self, session_id: str, transcript: str,
                                                    guest_name: str, guest_title: str, guest_company: str,
                                                    guest_linkedin: str) -> Dict:
        """Generate LinkedIn post with DB persistence"""
        return await self._generate_content_with_db('linkedin_post', session_id,
                                                    transcript=transcript, max_tokens=800, temperature=0.7,
                                                    guest_name=guest_name, guest_title=guest_title,
                                                    guest_company=guest_company, guest_linkedin=guest_linkedin)
    
    async def _generate_keywords_with_db_impl(self, session_id: str, transcript: str,
                                               guest_name: str, guest_title: str, guest_company: str) -> Dict:
        """Generate keywords with DB persistence"""
        result = await self._generate_content_with_db('keywords', session_id,
                                                      transcript=transcript, max_tokens=200, temperature=0.5,
                                                      guest_name=guest_name, guest_title=guest_title,
                                                      guest_company=guest_company)
        # Truncate to 500 chars max
        keywords = result['content'].strip().rstrip('...')
        if len(keywords) > 500:
            truncated = keywords[:500]
            last_comma = truncated.rfind(',')
            if last_comma > 400:
                keywords = truncated[:last_comma]
            else:
                keywords = truncated
        result['content'] = keywords.strip()
        return result
    
    async def _generate_content_with_db(self, prompt_name: str, session_id: str,
                                        transcript: Optional[str] = None,
                                        transcript_with_timecodes: Optional[List[dict]] = None,
                                        video_duration: Optional[float] = None,
                                        max_tokens: int = 500, temperature: float = 0.7,
                                        parse_list: bool = False, parse_timestamps: bool = False,
                                        default_items: int = 0, default_item: str = "",
                                        **format_kwargs) -> Dict:
        """Generic method to generate content with DB persistence"""
        # Get prompt template
        template = await self.repository.get_prompt_template(prompt_name)
        if not template:
            logger.warning(f"Prompt template not found: {prompt_name}, using fallback")
            prompt_text = f"Generate {prompt_name}"
            template_id = 0
        else:
            # Build format kwargs
            fmt_kwargs = format_kwargs.copy()
            if transcript:
                fmt_kwargs['transcript'] = transcript
            if transcript_with_timecodes:
                fmt_kwargs['transcript_with_timecodes'] = transcript_with_timecodes
            if video_duration is not None:
                fmt_kwargs['video_duration'] = video_duration
            
            # Render prompt
            try:
                prompt_text = template.template.format(**fmt_kwargs)
            except KeyError as e:
                logger.warning(f"Could not format prompt template {prompt_name}: {e}")
                prompt_text = template.template
            
            template_id = template.id
        
        # Save prompt usage BEFORE calling OpenAI
        prompt_usage = await self.repository.save_prompt_usage(session_id, template_id, prompt_text)
        
        # Call OpenAI
        result = await self.openai.generate_text_with_tokens(prompt_text, max_tokens=max_tokens, temperature=temperature)
        
        response_text = result['content']
        prompt_tokens = result.get('prompt_tokens', 0)
        completion_tokens = result.get('completion_tokens', 0)
        total_tokens = result.get('total_tokens', 0)
        
        # Calculate cost
        cost_usd = calculate_token_cost(prompt_tokens, completion_tokens, self.openai.model)
        
        # Save token usage AFTER OpenAI call
        await self.repository.save_token_usage(
            session_id=session_id,
            prompt_usage_id=prompt_usage.id,
            template_id=template_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            model=self.openai.model,
            cost_usd=cost_usd
        )
        
        # Parse response if needed
        if parse_list:
            items = self._parse_list_response(response_text, default_items, default_item)
            content = items
        elif parse_timestamps:
            timestamps = self._parse_timestamps_response(response_text)
            content = timestamps
        else:
            content = response_text
        
        return {
            'content': content,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'cost_usd': cost_usd,
            'model': self.openai.model
        }
    
    def _parse_list_response(self, response: str, target_count: int = 20, default_item: str = "") -> List[str]:
        """Parse numbered/bulleted list from response"""
        items = []
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove numbering
            if line and line[0].isdigit() and ('.' in line[:3] or ')' in line[:3]):
                line = line.split('.', 1)[-1].strip() if '.' in line[:3] else line.split(')', 1)[-1].strip()
            # Remove bullet points
            if line.startswith('-') or line.startswith('•'):
                line = line[1:].strip()
            if line:
                items.append(line)
        
        # Pad to target count
        while len(items) < target_count and default_item:
            items.append(default_item)
        
        return items[:target_count]
    
    def _parse_timestamps_response(self, response: str) -> List[str]:
        """Parse timestamps from response"""
        timestamps = []
        for line in response.split('\n'):
            line = line.strip()
            if line and ' - ' in line:
                timestamps.append(line)
        
        # Sort by time
        timestamps.sort(key=lambda x: self._parse_timestamp(x.split(' - ')[0]))
        
        return timestamps if timestamps else ["00:00:00 - Introduction"]
    
    # Original methods preserved for backward compatibility
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
    ) -> Tuple[Dict, Dict]:
        """Generate all content types for the podcast episode. Returns (content_dict, token_usage_dict)"""
        logger.info(f"Generating all content for guest: {guest_name}")
        
        # Track total token usage across all generations
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_tokens = 0
        model_used = self.openai.model
        
        # Generate all content sequentially and track tokens
        youtube_summary, tokens1 = await self._generate_youtube_summary_with_tokens(
            transcript, guest_name, guest_title, guest_company
        )
        total_prompt_tokens += tokens1.get("prompt_tokens", 0)
        total_completion_tokens += tokens1.get("completion_tokens", 0)
        total_tokens += tokens1.get("total_tokens", 0)
        
        blog_post, tokens2 = await self._generate_blog_post_with_tokens(
            transcript, guest_name, guest_title, guest_company, guest_linkedin
        )
        total_prompt_tokens += tokens2.get("prompt_tokens", 0)
        total_completion_tokens += tokens2.get("completion_tokens", 0)
        total_tokens += tokens2.get("total_tokens", 0)
        
        clickbait_titles, tokens3 = await self._generate_clickbait_titles_with_tokens(
            transcript, guest_name, guest_company
        )
        total_prompt_tokens += tokens3.get("prompt_tokens", 0)
        total_completion_tokens += tokens3.get("completion_tokens", 0)
        total_tokens += tokens3.get("total_tokens", 0)
        
        two_line_summary, tokens4 = await self._generate_two_line_summary_with_tokens(transcript)
        total_prompt_tokens += tokens4.get("prompt_tokens", 0)
        total_completion_tokens += tokens4.get("completion_tokens", 0)
        total_tokens += tokens4.get("total_tokens", 0)
        
        quotes, tokens5 = await self._generate_quotes_with_tokens(transcript_with_timecodes)
        total_prompt_tokens += tokens5.get("prompt_tokens", 0)
        total_completion_tokens += tokens5.get("completion_tokens", 0)
        total_tokens += tokens5.get("total_tokens", 0)
        
        chapter_timestamps, tokens6 = await self._generate_chapter_timestamps_with_tokens(
            transcript_with_timecodes, video_duration
        )
        total_prompt_tokens += tokens6.get("prompt_tokens", 0)
        total_completion_tokens += tokens6.get("completion_tokens", 0)
        total_tokens += tokens6.get("total_tokens", 0)
        
        linkedin_post, tokens7 = await self._generate_linkedin_post_with_tokens(
            transcript, guest_name, guest_title, guest_company, guest_linkedin
        )
        total_prompt_tokens += tokens7.get("prompt_tokens", 0)
        total_completion_tokens += tokens7.get("completion_tokens", 0)
        total_tokens += tokens7.get("total_tokens", 0)
        
        keywords, tokens8 = await self._generate_keywords_with_tokens(
            transcript, guest_name, guest_title, guest_company
        )
        total_prompt_tokens += tokens8.get("prompt_tokens", 0)
        total_completion_tokens += tokens8.get("completion_tokens", 0)
        total_tokens += tokens8.get("total_tokens", 0)
        
        # Generate hashtags from keywords (add # prefix to each keyword)
        hashtags = self.generate_hashtags_from_keywords(keywords)
        
        content = {
            'youtube_summary': youtube_summary,
            'blog_post': blog_post,
            'clickbait_titles': clickbait_titles,
            'two_line_summary': two_line_summary,
            'quotes': quotes,
            'chapter_timestamps': chapter_timestamps,
            'linkedin_post': linkedin_post,
            'keywords': keywords,
            'hashtags': hashtags
        }
        
        token_usage = {
            'prompt_tokens': total_prompt_tokens,
            'completion_tokens': total_completion_tokens,
            'total_tokens': total_tokens,
            'model': model_used
        }
        
        return content, token_usage
    
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
        """Generate 20 clickbait quotes summarizing key areas of the episode"""
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
        self, transcript: str, guest_name: str, guest_title: str, guest_company: str, guest_linkedin: str
    ) -> str:
        """Generate LinkedIn post with guest description, 3 key takeaways, and CTA"""
        prompt = self.prompts_service.format_prompt(
            'linkedin_post',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            guest_linkedin=guest_linkedin,
            transcript=transcript
        )
        
        return await self.openai.generate_text(prompt, max_tokens=800, temperature=0.7)
    
    async def generate_keywords(
        self, transcript: str, guest_name: str, guest_title: str, guest_company: str
    ) -> str:
        """Generate comma-separated keywords based on transcript, max 500 characters"""
        prompt = self.prompts_service.format_prompt(
            'keywords',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            transcript=transcript
        )
        keywords = await self.openai.generate_text(prompt, max_tokens=200, temperature=0.5)
        # Ensure it doesn't exceed 500 characters (remove trailing ... if present)
        keywords = keywords.strip().rstrip('...')
        if len(keywords) > 500:
            # Truncate at last comma before 500 chars to avoid breaking keywords
            truncated = keywords[:500]
            last_comma = truncated.rfind(',')
            if last_comma > 400:  # Only truncate at comma if it's reasonable
                keywords = truncated[:last_comma]
            else:
                keywords = truncated
        return keywords.strip()
    
    def generate_hashtags_from_keywords(self, keywords: str) -> str:
        """Convert keywords to hashtags by adding # prefix to each keyword, remove spaces per hashtag"""
        if not keywords:
            return ''
        # Split by comma, trim whitespace, remove all spaces within each keyword, add # prefix
        keyword_list = [kw.strip().replace(' ', '') for kw in keywords.split(',') if kw.strip()]
        # Remove trailing ... if present from each keyword
        keyword_list = [kw.rstrip('...') for kw in keyword_list]
        hashtags = ', '.join([f'#{kw}' for kw in keyword_list])
        # Ensure total doesn't exceed 500 characters
        if len(hashtags) > 500:
            # Truncate at last comma before 500 chars
            truncated = hashtags[:500]
            last_comma = truncated.rfind(',')
            if last_comma > 400:
                hashtags = truncated[:last_comma]
            else:
                hashtags = truncated
        return hashtags
    
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
    
    # Helper methods with token tracking
    async def _generate_youtube_summary_with_tokens(self, transcript: str, guest_name: str, guest_title: str, guest_company: str):
        """Generate YouTube summary with token tracking"""
        prompt = self.prompts_service.format_prompt(
            'youtube_summary',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            transcript=transcript
        )
        result = await self.openai.generate_text_with_tokens(prompt, max_tokens=600, temperature=0.7)
        return result['content'], result
    
    async def _generate_blog_post_with_tokens(self, transcript: str, guest_name: str, guest_title: str, guest_company: str, guest_linkedin: str):
        """Generate blog post with token tracking"""
        prompt = self.prompts_service.format_prompt(
            'blog_post',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            guest_linkedin=guest_linkedin,
            transcript=transcript
        )
        result = await self.openai.generate_text_with_tokens(prompt, max_tokens=2500, temperature=0.7)
        return result['content'], result
    
    async def _generate_clickbait_titles_with_tokens(self, transcript: str, guest_name: str, guest_company: str):
        """Generate clickbait titles with token tracking"""
        prompt = self.prompts_service.format_prompt(
            'clickbait_titles',
            guest_name=guest_name,
            guest_company=guest_company,
            transcript=transcript
        )
        result = await self.openai.generate_text_with_tokens(prompt, max_tokens=800, temperature=0.8)
        response = result['content']
        
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
        
        return titles[:20], result
    
    async def _generate_two_line_summary_with_tokens(self, transcript: str):
        """Generate two-line summary with token tracking"""
        prompt = self.prompts_service.format_prompt(
            'two_line_summary',
            transcript=transcript
        )
        result = await self.openai.generate_text_with_tokens(prompt, max_tokens=200, temperature=0.7)
        return result['content'], result
    
    async def _generate_quotes_with_tokens(self, transcript_with_timecodes: List[dict]):
        """Generate clickbait quotes with token tracking"""
        prompt = self.prompts_service.format_prompt(
            'quotes',
            transcript_with_timecodes=transcript_with_timecodes
        )
        result = await self.openai.generate_text_with_tokens(prompt, max_tokens=1000, temperature=0.6)
        response = result['content']
        
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
        
        return quotes[:20], result
    
    async def _generate_chapter_timestamps_with_tokens(self, transcript_with_timecodes: List[dict], video_duration: float):
        """Generate chapter timestamps with token tracking"""
        prompt = self.prompts_service.format_prompt(
            'chapter_timestamps',
            transcript_with_timecodes=transcript_with_timecodes,
            video_duration=video_duration
        )
        result = await self.openai.generate_text_with_tokens(prompt, max_tokens=600, temperature=0.7)
        response = result['content']
        
        # Parse timestamps
        timestamps = []
        for line in response.split('\n'):
            line = line.strip()
            if line and ' - ' in line:
                timestamps.append(line)
        
        # Sort timestamps by time if needed
        timestamps.sort(key=lambda x: self._parse_timestamp(x.split(' - ')[0]))
        
        return timestamps if timestamps else ["00:00:00 - Introduction"], result
    
    async def _generate_linkedin_post_with_tokens(self, transcript: str, guest_name: str, guest_title: str, guest_company: str, guest_linkedin: str):
        """Generate LinkedIn post with token tracking"""
        prompt = self.prompts_service.format_prompt(
            'linkedin_post',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            guest_linkedin=guest_linkedin,
            transcript=transcript
        )
        result = await self.openai.generate_text_with_tokens(prompt, max_tokens=800, temperature=0.7)
        return result['content'], result
    
    async def _generate_keywords_with_tokens(self, transcript: str, guest_name: str, guest_title: str, guest_company: str):
        """Generate keywords with token tracking"""
        prompt = self.prompts_service.format_prompt(
            'keywords',
            guest_name=guest_name,
            guest_title=guest_title,
            guest_company=guest_company,
            transcript=transcript
        )
        result = await self.openai.generate_text_with_tokens(prompt, max_tokens=200, temperature=0.5)
        keywords = result['content'].strip().rstrip('...')
        if len(keywords) > 500:
            # Truncate at last comma before 500 chars to avoid breaking keywords
            truncated = keywords[:500]
            last_comma = truncated.rfind(',')
            if last_comma > 400:  # Only truncate at comma if it's reasonable
                keywords = truncated[:last_comma]
            else:
                keywords = truncated
        return keywords.strip(), result

