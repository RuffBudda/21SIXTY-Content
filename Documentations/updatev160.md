# Update to v151 - AssemblyAI Migration

This document outlines the steps required to update from v150 to v151, which replaces Faster Whisper with AssemblyAI for cloud-based transcript generation.

## Overview

v151 replaces Faster Whisper (local, requires model downloads) with AssemblyAI (cloud-based), providing:
- **No model downloads** - Simple API-based transcription
- **No system dependencies** - No FFmpeg or build tools required
- **Easy setup** - Just requires API key configuration
- **Reliable** - Cloud-based service with automatic scaling
- **Fast** - Optimized cloud infrastructure

## Ubuntu Server Installation Steps

### 1. Update Python Dependencies

Navigate to your backend directory and update the requirements:

```bash
cd /path/to/your/backend
source venv/bin/activate  # Activate your virtual environment

# Install/update assemblyai
pip install --upgrade assemblyai>=0.48.0

# Or install all requirements fresh
pip install -r requirements.txt
```

**Note:** AssemblyAI is a pure Python package with no system dependencies. No additional system packages are required.

### 2. Get AssemblyAI API Key

1. Sign up for a free account at https://www.assemblyai.com/
2. Navigate to your dashboard and copy your API key
3. The free tier includes 5 hours of transcription per month

### 3. Configure Environment Variables

Add the AssemblyAI API key to your `.env` file:

```bash
# Add AssemblyAI API key (required for transcription)
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here

# OpenAI API key (still required for content generation)
OPENAI_API_KEY=your-openai-api-key-here
```

**Important:** Both API keys are required:
- `ASSEMBLYAI_API_KEY` - For audio transcription
- `OPENAI_API_KEY` - For content generation (summaries, blog posts, etc.)

### 4. Restart the Application

After installing dependencies and configuring the API key, restart your FastAPI application:

```bash
# If using systemd
sudo systemctl restart your-app-service

# Or if running manually
# Stop the current process (Ctrl+C) and restart:
cd /path/to/your/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Verify Installation

After restarting, check the logs to confirm AssemblyAI is configured:

```bash
# Check application logs
tail -f /path/to/your/logs/app.log

# Look for this message on startup:
# "AssemblyAI API key configured"
```

You can also verify the status in the frontend - the AssemblyAI pill in the header should show "Active" (green) when the API key is properly configured.

## What Changed

### Backend Changes
- **Removed Faster Whisper** - No longer requires local model downloads or system dependencies
- **Added AssemblyAI** - Cloud-based transcription using `assemblyai` package
- **No model downloads** - Models run on AssemblyAI's servers
- **Same response format** - API response structure unchanged, so frontend works without modifications
- **Error handling** - Added `error` and `error_details` fields to response for better debugging

### Frontend Changes
- **Added AssemblyAI status pill** - Shows "Active" or "Inactive" next to OpenAI pill
- **Status updates** - AssemblyAI status checks every 30 seconds
- **Better error display** - Shows backend error messages in transcript area if transcription fails

### Removed Dependencies
- **Faster Whisper** - No longer needed
- **FFmpeg** - Not required for AssemblyAI (handled by their service)
- **System build tools** - Not required (pure Python package)

## Troubleshooting

### Issue: "No module named 'assemblyai'"
**Solution:** Make sure you've activated your virtual environment and installed requirements:
```bash
source venv/bin/activate
pip install assemblyai>=0.48.0
```

### Issue: "AssemblyAI API key not configured"
**Solution:** Add `ASSEMBLYAI_API_KEY` to your `.env` file:
```bash
ASSEMBLYAI_API_KEY=your-api-key-here
```

### Issue: "AssemblyAI API key validation failed"
**Solutions:**
1. Verify your API key is correct (copy from AssemblyAI dashboard)
2. Check that your API key hasn't expired
3. Ensure you have credits/quota remaining in your AssemblyAI account
4. Check your internet connection (API calls require network access)

### Issue: Transcription returns empty results
**Solutions:**
1. Check backend logs for error messages
2. Verify API key is valid and has credits
3. Check audio file format is supported (MP3, WAV, M4A, OGG, FLAC)
4. Ensure audio file is not corrupted

### Issue: Slow transcription
**Note:** Transcription speed depends on:
- Audio file length
- AssemblyAI server load
- Your network connection

For faster processing, ensure good network connectivity to AssemblyAI servers.

## Performance Notes

- **No local processing** - All transcription happens on AssemblyAI servers
- **Network dependent** - Requires internet connection
- **Automatic scaling** - AssemblyAI handles load automatically
- **Pay-per-minute** - Charges based on audio length processed

## Migration Notes

- **No data migration required** - Existing cached transcripts remain valid
- **API key required** - ASSEMBLYAI_API_KEY must be configured
- **Backward compatible** - Old API responses work with new implementation
- **No system dependencies** - Can remove FFmpeg and build tools if not used elsewhere

## Cost Considerations

- **Free tier**: 5 hours of transcription per month
- **Paid plans**: Pay-per-minute pricing (check AssemblyAI website for current rates)
- **No model storage costs** - Models run on AssemblyAI infrastructure

## Support

If you encounter issues during the update, check:
1. Application logs for error messages
2. AssemblyAI API key is correctly configured
3. Python virtual environment is activated
4. All dependencies are installed
5. Network connectivity to AssemblyAI servers

For additional help:
- AssemblyAI documentation: https://www.assemblyai.com/docs
- AssemblyAI status page: https://status.assemblyai.com/

