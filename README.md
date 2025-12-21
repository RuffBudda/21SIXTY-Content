# 21SIXTY CONTENT GEN v67

A web-based tool for processing podcast audio files and generating comprehensive content including summaries, blog posts, titles, quotes, chapter timestamps, and LinkedIn posts using OpenAI APIs.

## Features

- **Audio File Upload**: Upload audio files (MP3, WAV, M4A, OGG, FLAC) for processing
- **LocalStorage Caching**: Intelligent caching system that stores processed data and audio files locally to avoid reprocessing
- **Projects Gallery**: Browse and manage all your processed projects stored in local storage. Open any project to access its transcript and generated content
- **AI-Powered Content Generation**:
  - Complete transcript with formatted timecodes
  - 3-paragraph YouTube summary
  - 2000-word blog post with LinkedIn hyperlinks
  - 20 clickbait titles (under 100 characters)
  - 2-line episode summary
  - 20 notable quotes from the episode
  - YouTube-ready chapter timestamps
  - LinkedIn post with guest description, 3 key takeaways, and CTA (with placeholder links for YouTube and Newsletter)
- **Download & Copy Features**: Download any deliverable as TXT file or copy to clipboard with SVG icons
- **Processing Animations**: Real-time visual feedback during processing with step-by-step status updates
- **Dark Mode UI**: Beautiful dark theme matching the 21SIXTY brand
- **OpenAI Credit Tracking**: Monitor API usage in real-time
- **Prompt Editor**: Customize AI prompts for all content types

## Tech Stack

- **Backend**: Python 3.12+ with FastAPI (tested with Python 3.12.3)
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **YouTube Processing**: yt-dlp
- **Transcription**: YouTube Transcript API
- **AI Generation**: OpenAI API (GPT-4)
- **Deployment**: Nginx reverse proxy

## Quick Start

### Prerequisites

- Python 3.12+ (Python 3.12.3 recommended)
- FFmpeg (for audio processing)
- OpenAI API key
- Node.js/npm (optional, for development)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd content-generator
```

2. Set up Python virtual environment:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cd backend
cp .env.example .env
```

**Important:** Edit the `.env` file and add your OpenAI API key:
```bash
# Open .env file in your editor
nano .env  # or use any text editor

# Replace 'your_openai_api_key_here' with your actual OpenAI API key:
OPENAI_API_KEY=sk-your-actual-api-key-here
```

You can get your OpenAI API key from: https://platform.openai.com/api-keys

4. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

5. Open your browser to `http://localhost:8000`

## Usage

1. **Upload Audio File**: Select an audio file (MP3, WAV, M4A, OGG, or FLAC) using the file selector
2. **Process Audio**: Click "Process Audio" - the system will:
   - Check localStorage for cached data (if same file was processed before, uses cache)
   - Upload and save the audio file
   - Display processing animations with real-time status
   - Note: Transcripts must be provided manually or through speech-to-text integration
3. **Enter Guest Information**: Fill in the guest's name, title, company, and LinkedIn profile
4. **Generate Content**: Click "Generate Content" to create all 7 content types using AI
5. **Download or Copy Results**: 
   - Use the download button (📥) to save any deliverable as a TXT file
   - Use the copy button (📋) to copy content to your clipboard
6. **Projects Gallery**: 
   - Navigate to the "Projects Gallery" tab to view all your processed projects
   - Each project card shows the title, date, duration, and whether content has been generated
   - Click "Open Project" to load a project and access its transcript and generated content
   - Delete projects you no longer need directly from the gallery

## API Endpoints

### POST /api/process-video
Process an uploaded audio file.

**Request:** (multipart/form-data)
- `audio_file`: Audio file (MP3, WAV, M4A, OGG, FLAC) - **Required**

**Note:** The endpoint accepts form data with file upload. Transcripts must be provided manually or through speech-to-text integration.

**Response:**
```json
{
  "success": true,
  "transcript": "Full transcript text...",
  "transcript_with_timecodes": [...],
  "video_title": "Video Title",
  "video_duration": 3600.0
}
```

### POST /api/generate-content
Generate all content types based on transcript and guest info.

**Request:**
```json
{
  "transcript": "Full transcript text...",
  "transcript_with_timecodes": [...],
  "guest_name": "John Doe",
  "guest_title": "CEO",
  "guest_company": "Company Name",
  "guest_linkedin": "https://www.linkedin.com/in/johndoe",
  "video_title": "Video Title",
  "video_duration": 3600.0
}
```

**Response:**
```json
{
  "youtube_summary": "3 paragraph summary...",
  "blog_post": "2000 word blog post...",
  "clickbait_titles": ["Title 1", "Title 2", ...],
  "two_line_summary": "Line 1\nLine 2",
  "quotes": ["Quote 1", "Quote 2", ...],
  "chapter_timestamps": ["00:00:00 - Chapter 1", ...]
}
```

### GET /api/openai-credits
Get OpenAI API credit/usage information.

### GET /api/health
Health check endpoint.

## Project Structure

```
content-generator/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic models
│   ├── services/
│   │   ├── youtube_service.py  # YouTube processing
│   │   ├── openai_service.py   # OpenAI integration
│   │   └── content_generator.py # Content generation
│   ├── utils/
│   │   └── file_handler.py     # File cleanup
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── nginx/                      # Nginx configuration
└── systemd/                    # Systemd service file
```

## Environment Variables

Configure these in the `.env` file in the `backend/` directory:

- `OPENAI_API_KEY`: Your OpenAI API key (required) - [Get one here](https://platform.openai.com/api-keys)
- `OPENAI_MODEL`: Model to use (default: gpt-4)
- `UPLOAD_DIR`: Directory for temporary files (default: ./uploads)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins for CORS

**Important:** The OpenAI API requires the `openai` Python package version 1.40.0 or higher (specified in `requirements.txt`).

## License

[Add your license here]

## Support

For issues or questions, please open an issue on the repository.

