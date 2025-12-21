from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header, UploadFile, File, Form
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
import hashlib
from datetime import datetime, timedelta
import shutil

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

# Cookie file directory - COMMENTED OUT: pytube doesn't support cookies
# COOKIES_DIR = os.path.join(os.path.dirname(__file__), "cookies")
# COOKIES_FILE_PATH = os.path.join(COOKIES_DIR, "cookies.txt")
# os.makedirs(COOKIES_DIR, exist_ok=True)

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
async def process_video(
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Process uploaded audio file"""
    if not verify_auth(credentials):
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        # Generate unique ID from audio file (use filename hash or timestamp)
        file_content = await audio_file.read()
        file_hash = hashlib.md5(file_content).hexdigest()[:11]
        video_id = f"audio_{file_hash}_{int(time.time())}"
        
        # Reset file pointer for saving
        await audio_file.seek(0)
        
        logger.info(f"Processing audio file: {audio_file.filename}")
        
        # Save uploaded audio file
        audio_path = os.path.join(youtube_service.upload_dir, f"{video_id}.mp3")
        os.makedirs(youtube_service.upload_dir, exist_ok=True)
        
        # Validate file type
        if not audio_file.filename or not audio_file.filename.lower().endswith(('.mp3', '.wav', '.m4a', '.ogg', '.flac')):
            raise HTTPException(status_code=400, detail="Invalid audio file format. Supported formats: MP3, WAV, M4A, OGG, FLAC")
        
        # Save uploaded file
        with open(audio_path, 'wb') as f:
            f.write(file_content)
        
        logger.info(f"Saved uploaded audio file to: {audio_path} (size: {len(file_content)} bytes)")
        
        # Return empty transcript - user will need to provide transcript manually or use speech-to-text
        transcript_data = {
            "transcript": "",
            "transcript_with_timecodes": [],
            "title": audio_file.filename or "Audio File",
            "duration": 0
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
        if verify_password(password):
            token = get_password_hash(password)
            authenticated_sessions.add(token)
            return {"success": True, "message": "Login successful", "token": token}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/auth/logout")
async def logout(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Logout endpoint to invalidate session"""
    try:
        if credentials:
            token_hash = credentials.credentials
            if token_hash in authenticated_sessions:
                authenticated_sessions.remove(token_hash)
                return {"success": True, "message": "Logged out successfully"}
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

