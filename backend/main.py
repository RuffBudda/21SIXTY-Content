from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from dotenv import load_dotenv
import logging
from typing import Optional
import hashlib

from models import ProcessVideoRequest, GenerateContentRequest, ProcessVideoResponse, GenerateContentResponse
from services.youtube_service import YouTubeService
from services.openai_service import OpenAIService
from services.content_generator import ContentGenerator
from services.prompts_service import PromptsService

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

app = FastAPI(title="21SIXTY CONTENT GEN API", version="1.0.0")

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

# Session storage (in production, use Redis or similar)
authenticated_sessions = set()

# Store MP3 file paths by video ID (in production, use Redis or database)
# Format: {video_id: file_path}
mp3_files = {}

def verify_password(password: str) -> bool:
    """Verify master password"""
    return password == MASTER_PASSWORD

def get_password_hash(password: str) -> str:
    """Hash password for session token"""
    return hashlib.sha256(password.encode()).hexdigest()

async def verify_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> bool:
    """Verify authentication token"""
    if not credentials:
        return False
    token_hash = credentials.credentials
    return token_hash in authenticated_sessions

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
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/api/process-video", response_model=ProcessVideoResponse)
async def process_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks, 
                       credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Process YouTube video: download MP3 and extract transcript with timecodes"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        logger.info(f"Processing video: {request.youtube_url}")
        
        # Extract video ID for storing and downloading
        video_id = youtube_service._extract_video_id(request.youtube_url)
        
        # Download video and extract MP3
        audio_path = await youtube_service.download_audio(request.youtube_url)
        
        # Get transcript with timecodes
        transcript_data = await youtube_service.get_transcript(request.youtube_url)
        
        # Store MP3 file path for download (don't cleanup immediately)
        if audio_path and os.path.exists(audio_path):
            mp3_files[video_id] = audio_path
            logger.info(f"Stored MP3 file path for video_id: {video_id}")
        
        return ProcessVideoResponse(
            success=True,
            transcript=transcript_data["transcript"],
            transcript_with_timecodes=transcript_data["transcript_with_timecodes"],
            video_title=transcript_data.get("title", ""),
            video_duration=transcript_data.get("duration", 0),
            video_id=video_id
        )
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.post("/api/generate-content", response_model=GenerateContentResponse)
async def generate_content(request: GenerateContentRequest,
                          credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Generate all content using OpenAI based on transcript and guest info"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        logger.info(f"Generating content for guest: {request.guest_name}")
        
        # Generate all content
        content = await content_generator.generate_all_content(
            transcript=request.transcript,
            transcript_with_timecodes=request.transcript_with_timecodes,
            guest_name=request.guest_name,
            guest_title=request.guest_title,
            guest_company=request.guest_company,
            guest_linkedin=request.guest_linkedin,
            video_title=request.video_title or "",
            video_duration=request.video_duration or 0
        )
        
        return GenerateContentResponse(**content)
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")

@app.get("/api/openai-credits")
async def get_openai_credits():
    """Get remaining OpenAI API credits/usage (no auth required for display)"""
    try:
        credits_info = await openai_service.get_credit_info()
        return credits_info
    except Exception as e:
        logger.error(f"Error fetching credits: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching credits: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

