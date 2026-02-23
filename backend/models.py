from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional

class ProcessVideoRequest(BaseModel):
    youtube_url: str = Field(..., description="YouTube video URL")

class ProcessVideoResponse(BaseModel):
    success: bool
    transcript: str = Field(..., description="Full transcript text")
    transcript_with_timecodes: List[dict] = Field(..., description="Transcript with timecodes")
    video_title: Optional[str] = Field(None, description="Video title")
    video_duration: Optional[float] = Field(None, description="Video duration in seconds")
    video_id: Optional[str] = Field(None, description="YouTube video ID for downloading MP3")
    error: Optional[str] = Field(None, description="Error message if transcription failed")
    error_details: Optional[str] = Field(None, description="Detailed error information")

class GuestInfo(BaseModel):
    name: str = Field(..., description="Guest name")
    title: str = Field(..., description="Guest title/position")
    company: str = Field(..., description="Guest company")
    linkedin: str = Field(..., description="LinkedIn profile URL")

class GenerateContentRequest(BaseModel):
    transcript: str = Field(..., description="Full transcript text")
    transcript_with_timecodes: List[dict] = Field(..., description="Transcript with timecodes")
    guest_name: str = Field(..., description="Guest name")
    guest_title: str = Field(..., description="Guest title/position")
    guest_company: str = Field(..., description="Guest company")
    guest_linkedin: str = Field(..., description="LinkedIn profile URL")
    video_title: Optional[str] = Field(None, description="Video title")
    video_duration: Optional[float] = Field(None, description="Video duration in seconds")
    session_id: Optional[str] = Field(None, description="Session ID for database persistence (optional, will be created if not provided)")

class GenerateContentResponse(BaseModel):
    youtube_summary: str = Field(..., description="3 paragraph YouTube summary")
    blog_post: str = Field(..., description="2000 word blog post")
    clickbait_titles: List[str] = Field(..., description="20 clickbait titles under 100 characters")
    two_line_summary: str = Field(..., description="One line summary of episode")
    quotes: List[str] = Field(..., description="20 clickbait quotes summarizing key areas of episode")
    chapter_timestamps: List[str] = Field(..., description="YouTube-ready timestamps for chapters")
    linkedin_post: str = Field(..., description="LinkedIn post with guest description, 3 key takeaways, and CTA")
    keywords: str = Field(..., description="Comma-separated keywords based on transcript, max 500 characters")
    hashtags: str = Field(..., description="Hashtags with # prefix, same keywords as keywords field")
    session_id: Optional[str] = Field(None, description="Session ID for retrieving content later")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")
    total_cost_usd: Optional[float] = Field(None, description="Total cost in USD")

