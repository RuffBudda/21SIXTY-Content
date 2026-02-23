from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from dotenv import load_dotenv
import logging

from models import ProcessVideoRequest, GenerateContentRequest, ProcessVideoResponse, GenerateContentResponse
from services.youtube_service import YouTubeService
from services.openai_service import OpenAIService
from services.content_generator import ContentGenerator

# Load environment variables
load_dotenv()

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
content_generator = ContentGenerator(openai_service)

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
async def process_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """Process YouTube video: download MP3 and extract transcript with timecodes"""
    try:
        logger.info(f"Processing video: {request.youtube_url}")
        
        # Download video and extract MP3
        audio_path = await youtube_service.download_audio(request.youtube_url)
        
        # Get transcript with timecodes
        transcript_data = await youtube_service.get_transcript(request.youtube_url)
        
        # Schedule cleanup of audio file
        if audio_path:
            background_tasks.add_task(cleanup_file, audio_path)
        
        return ProcessVideoResponse(
            success=True,
            transcript=transcript_data["transcript"],
            transcript_with_timecodes=transcript_data["transcript_with_timecodes"],
            video_title=transcript_data.get("title", ""),
            video_duration=transcript_data.get("duration", 0)
        )
    except Exception as e:
        logger.error(f"Error processing video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.post("/api/generate-content", response_model=GenerateContentResponse)
async def generate_content(request: GenerateContentRequest):
    """Generate all content using OpenAI based on transcript and guest info"""
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
    """Get remaining OpenAI API credits/usage"""
    try:
        credits_info = await openai_service.get_credit_info()
        return credits_info
    except Exception as e:
        logger.error(f"Error fetching credits: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching credits: {str(e)}")

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

