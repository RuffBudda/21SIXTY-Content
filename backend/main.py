from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File, Form
import hashlib
import time
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import tempfile
import assemblyai as aai
import uuid

from models import ProcessVideoRequest, GenerateContentRequest, ProcessVideoResponse, GenerateContentResponse
from services.youtube_service import YouTubeService
from services.openai_service import OpenAIService
from services.content_generator import ContentGenerator
from services.prompts_service import PromptsService
from services.usage_tracker import UsageTracker
from utils.file_handler import FileHandler
from utils.cost_calculator import calculate_token_cost
from database import init_db, AsyncSessionLocal, Base
from database.repository import Repository
from database.seed import init_prompt_templates
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Load environment variables
load_dotenv()

# Master password
MASTER_PASSWORD = os.getenv("MASTER_PASSWORD", "AbubakrIsAGenius")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="21SIXTY CONTENT GEN API", version="2.0.0")

# CORS configuration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,https://contents.2160.media").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
youtube_service = YouTubeService()
openai_service = OpenAIService()
prompts_service = PromptsService()
content_generator = ContentGenerator(openai_service, prompts_service)
usage_tracker = UsageTracker()

# Initialize AssemblyAI
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
if ASSEMBLYAI_API_KEY:
    aai.settings.api_key = ASSEMBLYAI_API_KEY
    logger.info("AssemblyAI API key configured")
else:
    logger.warning("ASSEMBLYAI_API_KEY not set - transcription will fail")

# Database setup
async def get_db():
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        yield session

# Initialize file handler for cleanup (2 weeks = 336 hours)
file_handler = FileHandler(upload_dir=youtube_service.upload_dir, max_age_hours=336)
# Store MP3 file paths by video ID (in production, use Redis or database)
# Format: {video_id: file_path}
mp3_files = {}

# Pre-compute hash of master password for fast verification
MASTER_PASSWORD_HASH = hashlib.sha256(MASTER_PASSWORD.encode()).hexdigest()

# Initialize scheduler for periodic cleanup
scheduler = AsyncIOScheduler()

async def periodic_cleanup():
    """Periodic cleanup task to remove old MP3 files (runs every 2 weeks)"""
    try:
        logger.info("Starting periodic cleanup of old MP3 files...")
        deleted_count = file_handler.cleanup_old_files()
        
        # Always clean up mp3_files dictionary entries for orphaned files
        # (files deleted by cleanup task, manual deletions, or external processes)
        video_ids_to_remove = []
        for video_id, file_path in mp3_files.items():
            if not os.path.exists(file_path):
                video_ids_to_remove.append(video_id)
        
        orphaned_count = len(video_ids_to_remove)
        for video_id in video_ids_to_remove:
            del mp3_files[video_id]
            logger.info(f"Removed orphaned video_id {video_id} from mp3_files dictionary")
        
        logger.info(f"Periodic cleanup completed. Deleted {deleted_count} files, removed {orphaned_count} orphaned dictionary entries.")
    except Exception as e:
        logger.error(f"Error during periodic cleanup: {str(e)}", exc_info=True)

# Schedule periodic cleanup every 2 weeks (14 days = 1209600 seconds)
scheduler.add_job(
    periodic_cleanup,
    trigger=IntervalTrigger(weeks=2),
    id='cleanup_old_files',
    name='Cleanup old MP3 files',
    replace_existing=True
)

# Start scheduler when app starts
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("=" * 50)
        logger.info("Starting Content Generator API")
        logger.info("=" * 50)
        
        # Log authentication setup
        logger.info("🔐 Authentication enabled")
        logger.info("   Master password: [SET]" if MASTER_PASSWORD else "   Master password: [NOT SET - USING DEFAULT]")
        
        # Initialize database
        try:
            logger.info("Initializing database...")
            await init_db()
            logger.info("✓ Database tables created successfully")
        except Exception as db_err:
            logger.error(f"⚠ Database initialization error (app will continue): {str(db_err)}", exc_info=True)
        
        # Initialize prompt templates
        try:
            logger.info("Initializing prompt templates...")
            async with AsyncSessionLocal() as session:
                await init_prompt_templates(session)
            logger.info("✓ Prompt templates initialized")
        except Exception as template_err:
            logger.error(f"⚠ Prompt template initialization error (app will continue): {str(template_err)}", exc_info=True)
        
        # Start scheduler
        try:
            logger.info("Starting background scheduler...")
            scheduler.start()
            logger.info("✓ Scheduler started - periodic cleanup will run every 2 weeks")
            
            # Run initial cleanup check
            await periodic_cleanup()
            logger.info("✓ Initial cleanup check completed")
        except Exception as scheduler_err:
            logger.error(f"⚠ Scheduler error (app will continue): {str(scheduler_err)}", exc_info=True)
        
        logger.info("=" * 50)
        logger.info("✅ Application startup completed successfully")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Unexpected startup error: {str(e)}", exc_info=True)
        logger.warning("App continuing despite startup errors")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    logger.info("Scheduler stopped.")

# Cookie file directory - COMMENTED OUT: pytube doesn't support cookies
# COOKIES_DIR = os.path.join(os.path.dirname(__file__), "cookies")
# COOKIES_FILE_PATH = os.path.join(COOKIES_DIR, "cookies.txt")
# os.makedirs(COOKIES_DIR, exist_ok=True)

def verify_password(password: str) -> bool:
    """Verify master password"""
    return password == MASTER_PASSWORD

def verify_auth(credentials: Optional[HTTPAuthorizationCredentials]) -> bool:
    """Verify authentication token (compares against hashed environment password)"""
    if not credentials:
        logger.debug("🔓 No credentials provided")
        return False
    token_hash = credentials.credentials
    logger.debug(f"🔓 Token received: {token_hash[:16]}..." if len(token_hash) > 16 else f"🔓 Token received: {token_hash}")
    logger.debug(f"   Expected: {MASTER_PASSWORD_HASH[:16]}...")
    match = token_hash == MASTER_PASSWORD_HASH
    logger.debug(f"   Match: {match}")
    return match

# Frontend path
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
frontend_path = os.path.abspath(frontend_path)

# Serve static files (CSS, JS, images)
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    # Serve CSS and JS files
    @app.get("/styles.css")
    async def serve_css():
        css_path = os.path.join(frontend_path, "styles.css")
        if os.path.exists(css_path):
            return FileResponse(css_path, media_type="text/css")
        raise HTTPException(status_code=404, detail="CSS file not found")
    
    @app.get("/app.js")
    async def serve_js():
        js_path = os.path.join(frontend_path, "app.js")
        if os.path.exists(js_path):
            return FileResponse(js_path, media_type="application/javascript")
        raise HTTPException(status_code=404, detail="JS file not found")

@app.get("/")
async def serve_frontend():
    """Serve the frontend index.html"""
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    return {"message": "Frontend not found"}

@app.get("/api/health")
async def health_check():
    """Health check endpoint - simple status without dependencies"""
    try:
        return {
            "status": "healthy",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check error: {str(e)}", exc_info=True)
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/api/process-video", response_model=ProcessVideoResponse)
async def process_video(
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Process uploaded audio file"""
    
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Validate file type BEFORE reading file content
    if not audio_file.filename:
        raise HTTPException(status_code=400, detail="No filename provided. Please ensure your file has a valid name.")
    
    file_extension = audio_file.filename.lower()
    if not file_extension.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.flac')):
        raise HTTPException(status_code=400, detail="Invalid audio file format. Supported formats: MP3, WAV, M4A, OGG, FLAC")
    
    try:
        # Generate unique ID from audio file (use filename hash or timestamp)
        file_content = await audio_file.read()
        
        # Validate file size (optional: prevent extremely large files)
        max_file_size = 500 * 1024 * 1024  # 500MB
        if len(file_content) > max_file_size:
            raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {max_file_size / (1024*1024):.0f}MB")
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty. Please upload a valid audio file.")
        
        file_hash = hashlib.md5(file_content).hexdigest()[:11]
        video_id = f"audio_{file_hash}_{int(time.time())}"
        
        logger.info(f"Processing audio file: {audio_file.filename} (size: {len(file_content)} bytes)")
        
        # Save uploaded audio file
        audio_path = os.path.join(youtube_service.upload_dir, f"{video_id}.mp3")
        os.makedirs(youtube_service.upload_dir, exist_ok=True)
        
        # Save uploaded file
        with open(audio_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Saved uploaded audio file to: {audio_path}")
        
        # Generate transcript using AssemblyAI
        transcript_data = {
            "transcript": "",
            "transcript_with_timecodes": [],
            "title": audio_file.filename or "Audio File",
            "duration": 0
        }
        
        try:
            if not ASSEMBLYAI_API_KEY:
                raise ValueError("ASSEMBLYAI_API_KEY not set. Please configure AssemblyAI API key in environment variables.")
            
            logger.info(f"Generating transcript using AssemblyAI for file: {audio_file.filename}")
            
            # Reset file pointer and read content
            audio_file.file.seek(0)
            audio_content = file_content
            
            # Create temporary file for AssemblyAI
            file_ext = os.path.splitext(audio_file.filename)[1] or '.mp3'
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
                tmp_file.write(audio_content)
                tmp_file_path = tmp_file.name
            
            try:
                # Initialize AssemblyAI transcriber
                transcriber = aai.Transcriber()
                
                # Configure transcription to include word timestamps (for timecodes)
                # Using speaker_labels=True enables utterances with timecodes
                config = aai.TranscriptionConfig(speaker_labels=True)
                
                # Transcribe audio file
                logger.info(f"Transcribing audio file with AssemblyAI: {tmp_file_path} (size: {os.path.getsize(tmp_file_path)} bytes)")
                transcript = transcriber.transcribe(tmp_file_path, config)
                
                # Wait for transcription to complete
                logger.info("Waiting for AssemblyAI transcription to complete...")
                while transcript.status == aai.TranscriptStatus.processing:
                    time.sleep(1)
                    transcript = transcriber.get_transcript(transcript.id)
                
                if transcript.status == aai.TranscriptStatus.error:
                    error_msg = transcript.error if hasattr(transcript, 'error') else "Unknown error"
                    raise Exception(f"AssemblyAI transcription failed: {error_msg}")
                
                logger.info(f"AssemblyAI transcription completed. Status: {transcript.status}")
                
                # Extract transcript text
                transcript_text = transcript.text if transcript.text else ""
                
                # Extract segments with timestamps
                transcript_with_timecodes = []
                if hasattr(transcript, 'utterances') and transcript.utterances:
                    # Use utterances if available (more accurate timestamps)
                    logger.info(f"Found {len(transcript.utterances)} utterances in transcript")
                    for utterance in transcript.utterances:
                        if utterance.text and utterance.text.strip():
                            transcript_with_timecodes.append({
                                "start": utterance.start / 1000.0,  # Convert ms to seconds
                                "end": utterance.end / 1000.0,
                                "text": utterance.text.strip()
                            })
                    logger.info(f"Extracted {len(transcript_with_timecodes)} segments with timecodes from utterances")
                elif hasattr(transcript, 'words') and transcript.words:
                    # Fallback: group words into segments (every 10 words or sentence break)
                    logger.info(f"Using word-level timestamps, found {len(transcript.words)} words")
                    segment_words = []
                    segment_start = None
                    for word in transcript.words:
                        if segment_start is None:
                            segment_start = word.start / 1000.0
                        segment_words.append(word.text)
                        # Create segment every 10 words or at punctuation
                        if len(segment_words) >= 10 or word.text.endswith(('.', '!', '?')):
                            if segment_words:
                                segment_text = ' '.join(segment_words).strip()
                                if segment_text:
                                    transcript_with_timecodes.append({
                                        "start": segment_start,
                                        "end": word.end / 1000.0,
                                        "text": segment_text
                                    })
                                segment_words = []
                                segment_start = None
                    # Add remaining words as final segment
                    if segment_words:
                        segment_text = ' '.join(segment_words).strip()
                        if segment_text:
                            transcript_with_timecodes.append({
                                "start": segment_start,
                                "end": transcript.words[-1].end / 1000.0,
                                "text": segment_text
                            })
                    logger.info(f"Extracted {len(transcript_with_timecodes)} segments from word timestamps")
                elif hasattr(transcript, 'words') and transcript.words:
                    # Fallback to words if utterances not available
                    current_segment = {"start": None, "end": None, "text": ""}
                    for word in transcript.words:
                        word_start = word.start / 1000.0  # Convert ms to seconds
                        word_end = word.end / 1000.0
                        word_text = word.text
                        
                        if current_segment["start"] is None:
                            current_segment["start"] = word_start
                        
                        current_segment["end"] = word_end
                        current_segment["text"] += word_text + " "
                    
                    if current_segment["text"]:
                        current_segment["text"] = current_segment["text"].strip()
                        transcript_with_timecodes.append(current_segment)
                
                # If no segments but we have text, create a single segment
                if not transcript_with_timecodes and transcript_text:
                    duration = transcript.audio_duration / 1000.0 if hasattr(transcript, 'audio_duration') else 0
                    transcript_with_timecodes = [{
                        "start": 0,
                        "end": duration,
                        "text": transcript_text
                    }]
                
                # Get duration
                duration = transcript.audio_duration / 1000.0 if hasattr(transcript, 'audio_duration') and transcript.audio_duration else 0
                if not duration and transcript_with_timecodes:
                    duration = transcript_with_timecodes[-1]["end"]
                
                # Ensure we have valid transcript data
                if not transcript_text and not transcript_with_timecodes:
                    logger.error("AssemblyAI returned empty transcript")
                    raise ValueError("AssemblyAI returned empty transcript")
                
                transcript_data = {
                    "transcript": transcript_text,
                    "transcript_with_timecodes": transcript_with_timecodes,
                    "title": audio_file.filename or "Audio File",
                    "duration": duration
                }
                
                logger.info(f"Successfully generated transcript with {len(transcript_with_timecodes)} segments, duration: {duration}s, text length: {len(transcript_text)} chars")
                
                # Track AssemblyAI usage
                if duration > 0:
                    usage_tracker.track_assemblyai_usage(duration)
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            import traceback
            full_traceback = traceback.format_exc()
            
            logger.error(f"Error generating transcript with AssemblyAI: {error_type}: {error_message}", exc_info=True)
            logger.error(f"Full error details - Type: {error_type}, Message: {error_message}")
            logger.error(f"Traceback: {full_traceback}")
            
            # Continue with empty transcript - don't fail the request
            logger.warning("Continuing with empty transcript due to AssemblyAI error")
            
            # Set error message in transcript_data for frontend debugging
            transcript_data = {
                "transcript": "",
                "transcript_with_timecodes": [],
                "title": audio_file.filename or "Audio File",
                "duration": 0,
                "error": f"AssemblyAI error: {error_type}: {error_message}",
                "error_details": full_traceback[:500] if len(full_traceback) > 500 else full_traceback
            }
        
        # Store MP3 file path for download (don't cleanup immediately)
        if audio_path and os.path.exists(audio_path):
            mp3_files[video_id] = audio_path
            logger.info(f"Stored MP3 file path for video_id: {video_id}")
        
        return ProcessVideoResponse(
            success=True,
            transcript=transcript_data.get("transcript", ""),
            transcript_with_timecodes=transcript_data.get("transcript_with_timecodes", []),
            video_title=transcript_data.get("title", audio_file.filename or "Audio File"),
            video_duration=transcript_data.get("duration", 0),
            video_id=video_id,
            error=transcript_data.get("error"),
            error_details=transcript_data.get("error_details")
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.post("/api/generate-content", response_model=GenerateContentResponse)
async def generate_content(request: GenerateContentRequest,
                          credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
                          db: AsyncSession = Depends(get_db)):
    """Generate all content using OpenAI based on transcript and guest info"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        # Create or use existing session
        session_id = request.session_id or str(uuid.uuid4())
        logger.info(f"Generating content for session: {session_id}, guest: {request.guest_name}")
        
        # Create repository
        repository = Repository(db)
        
        # Create session record
        await repository.create_session(session_id, title=request.video_title or f"Content for {request.guest_name}")
        
        # Update content generator with database support
        db_content_generator = ContentGenerator(openai_service, prompts_service, repository, db)
        
        # Generate all content with database persistence
        content, token_usage = await db_content_generator.generate_all_content_with_db(
            session_id=session_id,
            transcript=request.transcript,
            transcript_with_timecodes=request.transcript_with_timecodes,
            guest_name=request.guest_name,
            guest_title=request.guest_title,
            guest_company=request.guest_company,
            guest_linkedin=request.guest_linkedin,
            video_title=request.video_title or "",
            video_duration=request.video_duration or 0
        )
        
        # Save guest info
        await repository.save_guest(
            session_id=session_id,
            name=request.guest_name,
            title=request.guest_title,
            company=request.guest_company,
            linkedin_url=request.guest_linkedin
        )
        
        # Update session status to completed
        await repository.update_session_status(session_id, "completed")
        await repository.commit()
        
        # Track OpenAI usage (keep existing tracking for backward compatibility)
        if token_usage:
            usage_tracker.track_openai_usage(
                prompt_tokens=token_usage.get("prompt_tokens", 0),
                completion_tokens=token_usage.get("completion_tokens", 0),
                total_tokens=token_usage.get("total_tokens", 0),
                model=token_usage.get("model", "gpt-4o-mini")
            )
        
        # Return response with session info
        response = GenerateContentResponse(
            **content,
            session_id=session_id,
            total_tokens=token_usage.get("total_tokens", 0),
            total_cost_usd=token_usage.get("cost_usd", 0.0)
        )
        
        return response
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")

@app.post("/api/generate-content/{content_type}")
async def generate_single_content(
    content_type: str,
    request: GenerateContentRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Generate a single content type using OpenAI"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    valid_types = {
        'youtube_summary': 'generate_youtube_summary',
        'blog_post': 'generate_blog_post',
        'clickbait_titles': 'generate_clickbait_titles',
        'two_line_summary': 'generate_two_line_summary',
        'quotes': 'generate_quotes',
        'chapter_timestamps': 'generate_chapter_timestamps',
        'linkedin_post': 'generate_linkedin_post',
        'keywords': 'generate_keywords',
        'hashtags': 'generate_hashtags'
    }
    
    if content_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid content type. Valid types: {', '.join(valid_types.keys())}")
    
    try:
        method_name = valid_types[content_type]
        method = getattr(content_generator, method_name)
        
        if content_type == 'youtube_summary':
            result = await method(request.transcript, request.guest_name, request.guest_title, request.guest_company)
        elif content_type == 'blog_post':
            result = await method(request.transcript, request.guest_name, request.guest_title, request.guest_company, request.guest_linkedin)
        elif content_type == 'clickbait_titles':
            result = await method(request.transcript, request.guest_name, request.guest_company)
        elif content_type == 'two_line_summary':
            result = await method(request.transcript)
        elif content_type == 'quotes':
            result = await method(request.transcript_with_timecodes)
        elif content_type == 'chapter_timestamps':
            result = await method(request.transcript_with_timecodes, request.video_duration or 0)
        elif content_type == 'linkedin_post':
            result = await method(request.transcript, request.guest_name, request.guest_title, request.guest_company, request.guest_linkedin)
        elif content_type == 'keywords':
            result = await method(request.transcript, request.guest_name, request.guest_title, request.guest_company)
        elif content_type == 'hashtags':
            keywords = await content_generator.generate_keywords(request.transcript, request.guest_name, request.guest_title, request.guest_company)
            result = content_generator.generate_hashtags_from_keywords(keywords)
        
        return {content_type: result}
    except Exception as e:
        logger.error(f"Error generating {content_type}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating {content_type}: {str(e)}")

@app.get("/api/openai-credits")
async def get_openai_credits():
    """Get remaining OpenAI API credits/usage (no auth required for display)"""
    try:
        credits_info = await openai_service.get_credit_info()
        return credits_info
    except Exception as e:
        logger.error(f"Error fetching credits: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching credits: {str(e)}")

@app.get("/api/usage-stats")
async def get_usage_stats(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get usage statistics for OpenAI and AssemblyAI (requires authentication)"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        stats = usage_tracker.get_usage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching usage stats: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching usage stats: {str(e)}")

@app.get("/api/assemblyai-status")
async def get_assemblyai_status():
    """Check AssemblyAI API key status"""
    try:
        if not ASSEMBLYAI_API_KEY:
            return {
                "success": False,
                "status": "inactive",
                "message": "AssemblyAI API key not configured",
                "error": "missing_api_key"
            }
        
        # Test API key by attempting to create a transcriber
        try:
            transcriber = aai.Transcriber()
            # If we can create a transcriber, the API key is valid
            return {
                "success": True,
                "status": "active",
                "message": "AssemblyAI API key is configured and valid"
            }
        except Exception as api_error:
            error_msg = str(api_error)
            return {
                "success": False,
                "status": "inactive",
                "message": f"AssemblyAI API key validation failed: {error_msg}",
                "error": "invalid_api_key"
            }
    except Exception as e:
        logger.error(f"Error checking AssemblyAI status: {str(e)}", exc_info=True)
        return {
            "success": False,
            "status": "inactive",
            "message": f"Error checking AssemblyAI status: {str(e)}",
            "error": "check_failed"
        }

# COMMENTED OUT: Cookie upload endpoint - pytube doesn't support cookies
# @app.post("/api/upload-cookies")
# async def upload_cookies(
#     file: UploadFile = File(...),
#     credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
# ):
#     """Upload cookies.txt file (requires authentication)"""
#     if not verify_auth(credentials):
#         raise HTTPException(status_code=401, detail="Authentication required")
#     
#     try:
#         # Validate file size (max 100KB)
#         content = await file.read()
#         if len(content) > 100 * 1024:  # 100KB
#             raise HTTPException(status_code=400, detail="File too large. Maximum size is 100KB")
#         
#         # Basic validation: check if it looks like a cookies file
#         # Netscape format cookies start with # Netscape HTTP Cookie File or have domain entries
#         content_str = content.decode('utf-8', errors='ignore')
#         if not content_str.strip():
#             raise HTTPException(status_code=400, detail="Empty file")
#         
#         # Save file as cookies.txt (normalize filename)
#         # Always save as cookies.txt regardless of uploaded filename
#         with open(COOKIES_FILE_PATH, 'wb') as f:
#             f.write(content)
#         
#         logger.info(f"Cookies file uploaded successfully: {COOKIES_FILE_PATH}")
#         return {"success": True, "message": "Cookies file uploaded successfully"}
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error uploading cookies: {str(e)}", exc_info=True)
#         raise HTTPException(status_code=500, detail=f"Error uploading cookies: {str(e)}")

# COMMENTED OUT: Cookie status endpoint - pytube doesn't support cookies
# @app.get("/api/cookies-status")
# async def get_cookies_status():
#     """Get cookie file status (no auth required for display)"""
#     try:
#         if not os.path.exists(COOKIES_FILE_PATH):
#             return {
#                 "status": "missing",
#                 "message": "No cookies file found",
#                 "file_path": COOKIES_FILE_PATH
#             }
#         
#         # Check file size (should not be empty)
#         file_size = os.path.getsize(COOKIES_FILE_PATH)
#         if file_size == 0:
#             return {
#                 "status": "error",
#                 "message": "Cookies file is empty",
#                 "file_path": COOKIES_FILE_PATH
#             }
#         
#         # Check file age (warn if older than 7 days)
#         file_mtime = os.path.getmtime(COOKIES_FILE_PATH)
#         file_age = datetime.now() - datetime.fromtimestamp(file_mtime)
#         
#         if file_age > timedelta(days=7):
#             return {
#                 "status": "warning",
#                 "message": f"Cookies file is {file_age.days} days old (may be expired)",
#                 "file_path": COOKIES_FILE_PATH,
#                 "age_days": file_age.days
#             }
#         
#         return {
#             "status": "active",
#             "message": "Cookies file is configured and recent",
#             "file_path": COOKIES_FILE_PATH,
#             "age_days": file_age.days
#         }
#     except Exception as e:
#         logger.error(f"Error checking cookies status: {str(e)}", exc_info=True)
#         return {
#             "status": "error",
#             "message": f"Error checking cookies: {str(e)}",
#             "file_path": COOKIES_FILE_PATH
#         }

@app.post("/api/auth/login")
async def login(password_data: Dict[str, str]):
    """Login endpoint to authenticate with master password"""
    try:
        password = password_data.get("password", "")
        logger.debug(f"🔓 Login attempt with password: {password[:8]}..." if len(password) > 8 else f"🔓 Login attempt")
        logger.debug(f"   Expected password: {MASTER_PASSWORD[:8]}..." if len(MASTER_PASSWORD) > 8 else f"   Expected password length: {len(MASTER_PASSWORD)}")
        logger.debug(f"   Passwords match: {password == MASTER_PASSWORD}")
        
        if verify_password(password):
            # Return hashed password as token (derived from environment password)
            token = MASTER_PASSWORD_HASH
            logger.info(f"✓ Login successful for password")
            logger.debug(f"   Returning token: {token[:16]}...")
            return {"success": True, "message": "Login successful", "token": token}
        else:
            logger.warning(f"✗ Login failed - invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/logout")
async def logout(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Logout endpoint (stateless - just validates token)"""
    try:
        if verify_auth(credentials):
            return {"success": True, "message": "Logged out successfully"}
        else:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Logout failed")

@app.get("/api/auth/check")
async def check_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Check if user is authenticated"""
    if verify_auth(credentials):
        return {"authenticated": True}
    return {"authenticated": False}

@app.get("/api/prompts")
async def get_prompts(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Get all prompts (requires authentication)"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        prompts = prompts_service.get_all_prompts()
        return {"success": True, "prompts": prompts}
    except Exception as e:
        logger.error(f"Error fetching prompts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching prompts: {str(e)}")

@app.post("/api/prompts")
async def update_prompts(
    prompts_data: dict,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Update prompts (requires authentication)"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        prompts = prompts_data.get("prompts", {})
        prompts_service.update_prompts(prompts)
        return {"success": True, "message": "Prompts updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating prompts: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating prompts: {str(e)}")

@app.get("/api/download-audio/{video_id}")
async def download_audio(
    video_id: str,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Download the MP3 audio file for a processed video"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Check if we have the file path stored
        if video_id not in mp3_files:
            raise HTTPException(status_code=404, detail="Audio file not found. Please process the video first.")
        
        file_path = mp3_files[video_id]
        
        # Check if file still exists on disk
        if not os.path.exists(file_path):
            # Remove from storage if file is missing
            del mp3_files[video_id]
            raise HTTPException(status_code=404, detail="Audio file no longer exists on server")
        
        # Get video title for filename
        video_title = "audio"
        try:
            # Try to get from stored data or use video_id
            video_title = video_id
        except:
            pass
        
        # Sanitize filename
        safe_filename = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        if not safe_filename:
            safe_filename = video_id
        
        filename = f"{safe_filename}.mp3"
        
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            filename=filename,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error serving audio file: {str(e)}")

def cleanup_file(file_path: str):
    """Cleanup temporary file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")

# ==================== Database-backed endpoints ====================

@app.get("/api/sessions/{session_id}/content")
async def get_session_content(session_id: str,
                             credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
                             db: AsyncSession = Depends(get_db)):
    """Retrieve all stored content for a session from database"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        repository = Repository(db)
        
        # Get session
        session = await repository.get_session(session_id, load_relations=True)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        
        # Get all related data
        transcript = await repository.get_transcript(session_id)
        guest = await repository.get_guest(session_id)
        generated_content = await repository.get_generated_content(session_id)
        speakers = await repository.get_speakers(session_id)
        
        # Format speakers data
        speakers_data = [
            {
                "speaker_num": s.speaker_num,
                "name": s.name,
                "role": s.role,
                "confidence": s.confidence
            }
            for s in speakers
        ]
        
        return {
            "session_id": session_id,
            "created_at": session.created_at,
            "status": session.status,
            "transcript": {
                "raw_text": transcript.raw_text if transcript else "",
                "duration_seconds": transcript.duration_seconds if transcript else 0,
                "speaker_labels_enabled": transcript.speaker_labels_enabled if transcript else False,
                "speaker_identification_enabled": transcript.speaker_identification_enabled if transcript else False,
            } if transcript else None,
            "speakers": speakers_data,
            "guest": {
                "name": guest.name,
                "title": guest.title,
                "company": guest.company,
                "linkedin_url": guest.linkedin_url
            } if guest else None,
            "generated_content": {
                "youtube_summary": generated_content.youtube_summary,
                "blog_post": generated_content.blog_post,
                "clickbait_titles": generated_content.clickbait_titles,
                "two_line_summary": generated_content.two_line_summary,
                "quotes": generated_content.quotes,
                "chapter_timestamps": generated_content.chapter_timestamps,
                "linkedin_post": generated_content.linkedin_post,
                "keywords": generated_content.keywords,
                "hashtags": generated_content.hashtags,
                "full_episode_description": generated_content.full_episode_description,
                "model_used": generated_content.openai_model_used,
                "generated_at": generated_content.generated_at
            } if generated_content else None
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session content: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving session content: {str(e)}")

@app.get("/api/sessions/{session_id}/usage")
async def get_session_usage(session_id: str,
                           credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
                           db: AsyncSession = Depends(get_db)):
    """Get token usage and costs for a session"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        repository = Repository(db)
        usage_summary = await repository.get_usage_summary_for_session(session_id)
        return usage_summary
    except Exception as e:
        logger.error(f"Error retrieving session usage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving session usage: {str(e)}")

@app.get("/api/usage/summary")
async def get_usage_summary(days: int = 30,
                           credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
                           db: AsyncSession = Depends(get_db)):
    """Get aggregate usage statistics"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        repository = Repository(db)
        summary = await repository.get_usage_summary(days=days)
        return summary
    except Exception as e:
        logger.error(f"Error retrieving usage summary: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving usage summary: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

