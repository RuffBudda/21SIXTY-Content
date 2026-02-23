import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import PromptTemplate

logger = logging.getLogger(__name__)

# Default prompt templates
DEFAULT_PROMPTS = {
    'youtube_summary': '''You are a podcast summary expert. Based on the following transcript from a podcast episode featuring {guest_name}, {guest_title} at {guest_company}, generate a compelling 3-paragraph YouTube description summary.

Transcript:
{transcript}

Create a summary that:
1. Hooks viewers in the first paragraph with the main topic
2. Highlights key takeaways in the second paragraph
3. Ends with a call-to-action in the third paragraph

Generate only the 3-paragraph summary, no numbering or extra formatting.''',

    'blog_post': '''You are an expert blog writer. Write a comprehensive 2000-word blog post based on this podcast transcript featuring {guest_name}, {guest_title} at {guest_company}.

Guest LinkedIn: {guest_linkedin}

Transcript:
{transcript}

The blog post should:
1. Have an engaging introduction that hooks the reader
2. Include the guest's LinkedIn URL as a hyperlink in the first paragraph
3. Break content into multiple sections with headers
4. Include 3-4 key takeaways highlighted
5. End with a strong conclusion and CTA

Write the complete blog post.''',

    'clickbait_titles': '''Generate exactly 20 clickbait-style YouTube video titles for a podcast episode featuring {guest_name} from {guest_company}.

Transcript excerpt:
{transcript}

Requirements:
- Each title must be under 100 characters
- Must mention {guest_name} or {guest_company}
- Use power words and curiosity gaps
- Number each title

Generate the 20 titles now.''',

    'two_line_summary': '''Summarize this podcast transcript in exactly 2 lines (2 sentences max):

{transcript}

Make it punchy and interesting for social media.''',

    'quotes': '''Extract exactly 20 of the most quotable moments from this podcast transcript that would work well as quote graphics on social media.

{transcript_with_timecodes}

Format each quote as a standalone statement. Number them 1-20.''',

    'chapter_timestamps': '''Create YouTube chapter timestamps for this podcast based on the transcript and {video_duration} second duration.

Transcript segments:
{transcript_with_timecodes}

Format each line as: HH:MM:SS - Chapter Title

Generate logical chapter breaks that improve viewer navigation.''',

    'linkedin_post': '''Write a professional LinkedIn post for {guest_name}, {guest_title} at {guest_company}.

Guest LinkedIn: {guest_linkedin}
Podcast transcript:
{transcript}

The post should:
1. Start with an engaging hook
2. Include 3 key takeaways as bullet points
3. Include the guest's LinkedIn URL as a hyperlink
4. End with a call-to-action (like/comment/share)

Keep it to 1-2 paragraphs plus bullets.''',

    'keywords': '''Extract 10-15 SEO-friendly keywords from this podcast featuring {guest_name}, {guest_title} at {guest_company}.

Transcript:
{transcript}

Return only comma-separated keywords, max 500 characters total. Focus on searchable topics discussed.''',
}


async def init_prompt_templates(db_session: AsyncSession):
    """Initialize default prompt templates if they don't exist"""
    try:
        for name, template_text in DEFAULT_PROMPTS.items():
            # Check if template already exists
            query = select(PromptTemplate).where(PromptTemplate.name == name)
            result = await db_session.execute(query)
            existing = result.scalar_one_or_none()
            
            if not existing:
                prompt = PromptTemplate(
                    name=name,
                    template=template_text,
                    version=1,
                    is_active=True,
                    notes="Default template"
                )
                db_session.add(prompt)
                logger.info(f"Created prompt template: {name} v1")
            else:
                logger.debug(f"Prompt template already exists: {name}")
        
        await db_session.commit()
        logger.info("Prompt templates initialization complete")
        
    except Exception as e:
        logger.error(f"Error initializing prompt templates: {str(e)}", exc_info=True)
        await db_session.rollback()
        raise
