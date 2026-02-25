from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from database import Base


class Session(Base):
    """Top-level session/project container"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    title = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(50), default="processing")  # processing/completed/error

    # Relationships
    transcript = relationship("Transcript", back_populates="session", uselist=False, cascade="all, delete-orphan")
    speakers = relationship("Speakers", back_populates="session", cascade="all, delete-orphan")
    guest = relationship("Guest", back_populates="session", uselist=False, cascade="all, delete-orphan")
    generated_content = relationship("GeneratedContent", back_populates="session", uselist=False, cascade="all, delete-orphan")
    prompt_usage = relationship("PromptUsage", back_populates="session", cascade="all, delete-orphan")
    token_usage = relationship("TokenUsage", back_populates="session", cascade="all, delete-orphan")


class Transcript(Base):
    """Raw and structured transcript data"""
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    raw_text = Column(Text)  # Full plain text transcript
    transcript_json = Column(JSON)  # Structured with timecodes: [{text, start_ms, end_ms, confidence}, ...]
    duration_seconds = Column(Float)
    speaker_labels_enabled = Column(Boolean, default=False)
    speaker_identification_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="transcript")
    utterances = relationship("Utterances", back_populates="transcript", cascade="all, delete-orphan")


class Speakers(Base):
    """Unique speakers identified in the transcript"""
    __tablename__ = "speakers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    speaker_num = Column(String(10))  # Speaker A, Speaker B, Speaker C, etc.
    name = Column(String(255))  # Identified name from AssemblyAI
    role = Column(String(100))  # Optional: Host, Guest, Interviewer, etc.
    confidence = Column(Float, nullable=True)  # Confidence score from speaker identification
    metadata_json = Column(JSON, nullable=True)  # Additional metadata

    # Relationships
    session = relationship("Session", back_populates="speakers")
    utterances = relationship("Utterances", back_populates="speaker", cascade="all, delete-orphan")


class Utterances(Base):
    """Individual spoken segments with speaker attribution"""
    __tablename__ = "utterances"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"), nullable=False, index=True)
    speaker_id = Column(Integer, ForeignKey("speakers.id"), nullable=True)
    text = Column(Text)
    start_time_ms = Column(Integer)  # Start time in milliseconds
    end_time_ms = Column(Integer)  # End time in milliseconds
    confidence = Column(Float, nullable=True)
    words_json = Column(JSON, nullable=True)  # [{word, start_ms, end_ms, confidence}, ...]

    # Relationships
    transcript = relationship("Transcript", back_populates="utterances")
    speaker = relationship("Speakers", back_populates="utterances")


class Guest(Base):
    """Guest/participant information"""
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    title = Column(String(255))
    company = Column(String(255))
    linkedin_url = Column(String(500))
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("Session", back_populates="guest")


class GeneratedContent(Base):
    """All AI-generated content outputs"""
    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    youtube_summary = Column(Text)  # 3 paragraph summary
    blog_post = Column(Text)  # ~2000 word post
    clickbait_titles = Column(JSON)  # Array of 20 titles
    two_line_summary = Column(Text)
    quotes = Column(JSON)  # Array with timestamps: [{text, timestamp}, ...]
    chapter_timestamps = Column(JSON)  # Array of YouTube chapters
    linkedin_post = Column(Text)
    keywords = Column(Text)  # Comma-separated
    hashtags = Column(Text)  # JSON or comma-separated with #
    full_episode_description = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    openai_model_used = Column(String(50))  # e.g., "gpt-4-turbo", "gpt-3.5-turbo"

    # Relationships
    session = relationship("Session", back_populates="generated_content")


class PromptTemplate(Base):
    """Versioned prompt templates"""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)  # e.g., "youtube_summary", "blog_post"
    template = Column(Text)  # Template with {placeholders}
    version = Column(Integer, default=1)  # Track iterations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)  # Soft delete for versioning
    notes = Column(Text, nullable=True)  # Notes about changes

    # Relationships
    prompt_usages = relationship("PromptUsage", back_populates="prompt_template", cascade="all, delete-orphan")
    token_usages = relationship("TokenUsage", back_populates="prompt_template")

    # Composite index on (name, version)
    __table_args__ = (
        Index("idx_template_name_version", "name", "version"),
    )


class PromptUsage(Base):
    """Record of each time a prompt was rendered and used"""
    __tablename__ = "prompt_usage"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=False)
    prompt_text_used = Column(Text)  # The actual rendered prompt with real data inserted
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("Session", back_populates="prompt_usage")
    prompt_template = relationship("PromptTemplate", back_populates="prompt_usages")
    token_usages = relationship("TokenUsage", back_populates="prompt_usage", cascade="all, delete-orphan")


class TokenUsage(Base):
    """Token usage and cost tracking per prompt call"""
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id"), nullable=False, index=True)
    prompt_usage_id = Column(Integer, ForeignKey("prompt_usage.id"), nullable=False)
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=False)
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    model = Column(String(50))  # e.g., "gpt-4-turbo"
    cost_usd = Column(Float)  # Calculated: tokens × model_rate
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    session = relationship("Session", back_populates="token_usage")
    prompt_usage = relationship("PromptUsage", back_populates="token_usages")
    prompt_template = relationship("PromptTemplate", back_populates="token_usages")


class UsageSummary(Base):
    """Aggregated daily usage for trend reports"""
    __tablename__ = "usage_summary"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), unique=True, index=True)  # YYYY-MM-DD format
    total_tokens = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    request_count = Column(Integer, default=0)  # Number of API calls
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
