# 21SIXTY CONTENT GEN

A web-based tool for processing YouTube podcast episodes and generating comprehensive content including summaries, blog posts, titles, quotes, and chapter timestamps using OpenAI APIs.

## Features

- **YouTube Video Processing**: Downloads videos as MP3 and extracts transcripts with timecodes
- **AI-Powered Content Generation**:
  - 3-paragraph YouTube summary
  - 2000-word blog post with LinkedIn hyperlinks
  - 20 clickbait titles (under 100 characters)
  - 2-line episode summary
  - 20 notable quotes from the episode
  - YouTube-ready chapter timestamps
- **Dark Mode UI**: Beautiful dark theme matching the 21SIXTY brand
- **Copy-to-Clipboard**: Easy copying of all generated content
- **OpenAI Credit Tracking**: Monitor API usage in real-time

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

1. **Enter YouTube URL**: Paste a YouTube video URL and click "Process Video"
2. **Wait for Processing**: The system will download the video and extract the transcript
3. **Enter Guest Information**: Fill in the guest's name, title, company, and LinkedIn profile
4. **Generate Content**: Click "Generate Content" to create all content types
5. **Copy Results**: Use the copy buttons to copy any generated content to your clipboard

## API Endpoints

### POST /api/process-video
Process a YouTube video and extract transcript.

**Request:**
```json
{
  "youtube_url": "https://www.youtube.com/watch?v=..."
}
```

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
├── systemd/                    # Systemd service file
└── DEPLOYMENT.md              # Deployment guide
```

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for a complete deployment guide including:
- Server setup and dependencies
- Application installation and configuration
- Systemd service setup
- Nginx reverse proxy configuration
- SSL/HTTPS setup with Let's Encrypt
- Troubleshooting and maintenance

The deployment guide is comprehensive and includes all steps needed to deploy on DigitalOcean with SSL support.

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

