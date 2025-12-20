# Quick Start Guide

## Local Development Setup

1. **Install Dependencies**

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure Environment**

```bash
cp .env.example .env
```

**Add your OpenAI API key:**

Edit the `.env` file in the `backend/` directory and replace `your_openai_api_key_here` with your actual OpenAI API key:

```bash
# Open .env file
nano .env  # or use any text editor (VS Code, Notepad, etc.)

# Update this line:
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Get your OpenAI API key:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key and paste it in the `.env` file

**File location:** `backend/.env`

3. **Install FFmpeg** (required for audio processing)

- **Linux**: `sudo apt install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from https://ffmpeg.org/download.html

4. **Run the Application**

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

5. **Access the Application**

Open your browser to `http://localhost:8000`

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions on DigitalOcean.

## Troubleshooting

### FFmpeg not found
Make sure FFmpeg is installed and in your system PATH.

### OpenAI API errors
- Verify your API key is correct in `.env`
- Check your OpenAI account has sufficient credits
- Ensure the model (default: gpt-4) is available to your account

### YouTube transcript not available
- Some videos don't have transcripts
- Try a different video or manually add a transcript to YouTube

