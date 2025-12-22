import json
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PromptsService:
    def __init__(self, prompts_file: str = "prompts.json"):
        """Initialize prompts service with prompts file path"""
        # Get the directory where this service file is located
        service_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to backend directory
        backend_dir = os.path.dirname(service_dir)
        self.prompts_file = os.path.join(backend_dir, prompts_file)
        self.prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load prompts from JSON file"""
        try:
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    prompts = json.load(f)
                    logger.info(f"Loaded prompts from {self.prompts_file}")
                    return prompts
            else:
                logger.warning(f"Prompts file not found: {self.prompts_file}, using defaults")
                return self._get_default_prompts()
        except Exception as e:
            logger.error(f"Error loading prompts: {str(e)}", exc_info=True)
            return self._get_default_prompts()
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """Get default prompts"""
        return {
            "youtube_summary": "You are writing a summary for a YouTube video description for The Dollar Diaries podcast.\n\nGuest Information:\n- Name: {guest_name}\n- Title: {guest_title}\n- Company: {guest_company}\n\nTranscript:\n{transcript}\n\nPlease create a compelling 3-paragraph summary for YouTube that:\n1. Introduces the guest and their background in the first paragraph\n2. Highlights the key topics and insights discussed in the second paragraph\n3. Teases what viewers will learn or take away in the third paragraph\n\nMake it engaging, professional, and suitable for a YouTube video description.",
            "blog_post": "You are writing a comprehensive 2000-word blog post based on a podcast episode transcript from The Dollar Diaries podcast.\n\nGuest Information:\n- Name: {guest_name}\n- Title: {guest_title}\n- Company: {guest_company}\n- LinkedIn: {guest_linkedin}\n\nTranscript:\n{transcript}\n\nInstructions:\n1. Write a comprehensive 2000-word blog post based on this episode\n2. In the FIRST PARAGRAPH, hyperlink the guest's name to their LinkedIn profile using markdown format: [Name](LinkedIn_URL)\n3. Structure the blog post with engaging subheadings\n4. Include key insights, quotes, and takeaways from the episode\n5. Make it valuable and readable for the audience\n6. End with a strong conclusion\n\nFormat the LinkedIn hyperlink in the first paragraph like this:\nIn this episode of The Dollar Diaries, we speak with [{guest_name}]({guest_linkedin}), {guest_title} at {guest_company}, about...\n\nWrite the full blog post now:",
            "clickbait_titles": "Generate 20 clickbait-style titles for a podcast episode, each under 100 characters.\n\nGuest: {guest_name} from {guest_company}\n\nTranscript excerpt:\n{transcript}\n\nRequirements:\n- Each title must be under 100 characters\n- Include the guest's name ({guest_name}) and/or company ({guest_company})\n- Make them compelling and click-worthy\n- Based on the actual content of the episode\n- Number each title from 1 to 20\n- Return only the titles, one per line, without any other text\n\nFormat:\n1. Title here\n2. Title here\n...",
            "two_line_summary": "Create a concise two-line summary of this podcast episode based ONLY on the transcript content provided below.\n\nTranscript:\n{transcript}\n\nIMPORTANT: Your summary MUST be based directly on the actual content from the transcript above. Do not make up information or use generic statements. Extract the key points and insights that are actually discussed in the transcript.\n\nWrite exactly two lines that capture the essence of the episode. Make it engaging and informative.\n\nFormat:\nLine 1\nLine 2",
            "quotes": "Extract 20 of the most notable, insightful, or quotable statements DIRECTLY from this podcast transcript. You MUST use only the actual text from the transcript below - do not paraphrase or create new quotes.\n\nTranscript with timestamps:\n{transcript_with_timecodes}\n\nRequirements:\n- Select the 20 most impactful quotes that are ACTUALLY in the transcript above\n- They should be complete thoughts or statements as they appear in the transcript\n- Include the timestamp in format [HH:MM:SS] before each quote\n- Use the EXACT wording from the transcript - do not rephrase or summarize\n- Number each quote from 1 to 20\n- Return only the quotes, one per line\n\nFormat:\n1. [HH:MM:SS] Quote text here (exact text from transcript)\n2. [HH:MM:SS] Quote text here (exact text from transcript)\n...",
            "chapter_timestamps": "Analyze this podcast transcript and create YouTube chapter timestamps based EXCLUSIVELY on the actual content and topic transitions visible in the transcript below.\n\nCRITICAL REQUIREMENTS:\n- You MUST base chapter timestamps ONLY on the actual transcript provided below\n- Identify REAL topic transitions that occur in the conversation\n- Do not create generic or made-up chapter titles\n- Each chapter title must reflect what was ACTUALLY discussed at that point in the transcript\n- Timestamps must align with ACTUAL topic transitions visible in the transcript\n- Do not guess or infer topics - use only what is explicitly discussed\n\nTranscript with timecodes:\n{transcript_with_timecodes}\n\nVideo duration: {video_duration} seconds\n\nCreate YouTube-ready chapter timestamps that:\n1. Identify natural topic breaks in the ACTUAL conversation from the transcript\n2. Use format: 00:00:00 - Chapter Title\n3. Create 8-12 meaningful chapters based on REAL topic transitions visible in the transcript\n4. Each chapter title must be descriptive and reflect what was ACTUALLY discussed at that timestamp\n5. Timestamps must align with ACTUAL topic transitions in the transcript - look for when speakers change topics\n6. Chapter titles must be based on the actual content discussed, not generic topics\n\nReturn only the timestamps in this exact format:\n00:00:00 - Chapter Title 1\n00:05:30 - Chapter Title 2\n...",
            "linkedin_post": "You are creating a professional LinkedIn post for The Dollar Diaries podcast episode.\n\nGuest Information:\n- Name: {guest_name}\n- Title: {guest_title}\n- Company: {guest_company}\n- LinkedIn: {guest_linkedin}\n\nTranscript:\n{transcript}\n\nInstructions:\n1. **Opening Hook**: Start with an engaging hook that introduces the guest and episode topic. Mention the guest's name and link to their LinkedIn profile using markdown format: [{guest_name}]({guest_linkedin})\n\n2. **Guest Description**: Write 2-3 sentences describing the guest's background, expertise, achievements, and why they're an interesting guest. Make it compelling and highlight their credibility.\n\n3. **Three Key Takeaways**: Present exactly three key takeaways from the episode. Format them as:\n   • Takeaway 1: [Clear, actionable insight]\n   • Takeaway 2: [Clear, actionable insight]\n   • Takeaway 3: [Clear, actionable insight]\n   \n   Each takeaway should be:\n   - Specific and actionable\n   - Based on actual content from the transcript\n   - Valuable to the LinkedIn audience\n   - 1-2 sentences each\n\n4. **Call-to-Action (CTA)**: End with a clear CTA that includes:\n   - Placeholder link to watch the episode: [Watch on YouTube](YOUTUBE_LINK_PLACEHOLDER)\n   - Placeholder link to read the newsletter: [Read in Newsletter](NEWSLETTER_LINK_PLACEHOLDER)\n   - Make the CTA engaging and encourage engagement (likes, comments, shares)\n\nFormatting Requirements:\n- Use line breaks (double line breaks) between sections for readability\n- Keep total length between 300-500 words (optimal for LinkedIn engagement)\n- Use professional but conversational tone\n- Include relevant hashtags if appropriate (2-3 max)\n- Make it scannable with clear structure\n- Optimize for LinkedIn's algorithm (engagement-focused)\n\nWrite the complete LinkedIn post now:",
            "keywords": "Generate a comma-separated list of keywords based on this podcast episode transcript.\n\nGuest Information:\n- Name: {guest_name}\n- Title: {guest_title}\n- Company: {guest_company}\n\nTranscript:\n{transcript}\n\nRequirements:\n- MUST include these exact keywords: 'thedollardiaries', 'tdd', 'dubai', '{guest_name}', '{guest_company}', '{guest_title}'\n- Add additional relevant keywords based on the conversation topics, themes, and content\n- All keywords should be lowercase\n- Separate keywords with commas and a single space: ', '\n- Total character count (including commas and spaces) must NOT exceed 500 characters\n- Focus on topics discussed, industries mentioned, key concepts, and relevant terms\n- Return ONLY the comma-separated keywords, nothing else\n\nFormat:\nkeyword1, keyword2, keyword3, ...",
            "standard_static_content": ""
        }
    
    def get_all_prompts(self) -> Dict[str, str]:
        """Get all prompts"""
        return self.prompts.copy()
    
    def get_prompt(self, prompt_type: str) -> Optional[str]:
        """Get a specific prompt by type"""
        return self.prompts.get(prompt_type)
    
    def update_prompts(self, new_prompts: Dict[str, str]) -> bool:
        """Update prompts and save to file"""
        try:
            # Validate that all required prompt types are present
            required_types = ["youtube_summary", "blog_post", "clickbait_titles", 
                            "two_line_summary", "quotes", "chapter_timestamps", "linkedin_post", "keywords"]
            
            for prompt_type in required_types:
                if prompt_type not in new_prompts:
                    raise ValueError(f"Missing required prompt type: {prompt_type}")
            
            # Update prompts (include standard_static_content if provided, but don't require it)
            self.prompts.update(new_prompts)
            
            # Ensure standard_static_content exists (default to empty string if not provided)
            if "standard_static_content" not in self.prompts:
                self.prompts["standard_static_content"] = ""
            
            # Save to file
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Prompts updated and saved to {self.prompts_file}")
            return True
        except Exception as e:
            logger.error(f"Error updating prompts: {str(e)}", exc_info=True)
            raise
    
    def format_prompt(self, prompt_type: str, **kwargs) -> str:
        """Format a prompt with provided variables"""
        prompt_template = self.get_prompt(prompt_type)
        if not prompt_template:
            raise ValueError(f"Prompt type not found: {prompt_type}")
        
        # Handle special formatting for transcript limits
        if 'transcript' in kwargs:
            transcript = kwargs['transcript']
            # Limit transcript length based on prompt type
            if prompt_type == 'youtube_summary':
                transcript = transcript[:8000]
            elif prompt_type == 'blog_post':
                transcript = transcript[:12000]
            elif prompt_type in ['clickbait_titles', 'two_line_summary']:
                transcript = transcript[:6000]
            kwargs['transcript'] = transcript
        
        # Format transcript_with_timecodes for quotes and chapters
        if 'transcript_with_timecodes' in kwargs and isinstance(kwargs['transcript_with_timecodes'], list):
            if prompt_type == 'quotes':
                # Format for quotes
                formatted = "\n".join([
                    f"[{self._format_timestamp(tc.get('start', 0))}] {tc.get('text', '')}"
                    for tc in kwargs['transcript_with_timecodes'][:200]
                ])
                kwargs['transcript_with_timecodes'] = formatted
            elif prompt_type == 'chapter_timestamps':
                # Format for chapters
                formatted = self._format_transcript_for_chapters(kwargs['transcript_with_timecodes'][:300])
                kwargs['transcript_with_timecodes'] = formatted
        
        # Format video duration
        if 'video_duration' in kwargs and isinstance(kwargs['video_duration'], (int, float)):
            kwargs['video_duration'] = self._format_timestamp(kwargs['video_duration'])
        
        try:
            return prompt_template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable in prompt template: {e}")
            raise ValueError(f"Missing required variable in prompt: {e}")
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _format_transcript_for_chapters(self, transcript_with_timecodes: list) -> str:
        """Format transcript for chapter generation"""
        lines = []
        for tc in transcript_with_timecodes[::10]:  # Sample every 10th entry
            timestamp = self._format_timestamp(tc.get('start', 0))
            lines.append(f"[{timestamp}] {tc.get('text', '')}")
        return "\n".join(lines)
