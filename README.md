# CONTENT GEN

A web-based tool for processing podcast audio files and generating comprehensive content including summaries, blog posts, titles, quotes, chapter timestamps, and LinkedIn posts using OpenAI APIs.

## Features

- **Audio File Upload**: Upload audio files (MP3, WAV, M4A, OGG, FLAC) for processing
- **LocalStorage Caching**: Intelligent caching system that stores processed data and audio files locally to avoid reprocessing
- **Projects Gallery**: Browse and manage all your processed projects stored in local storage. Open any project to access its transcript and generated content
- **AI-Powered Content Generation**:
  - Complete transcript with formatted timecodes
  - 3-paragraph episode summary
  - 2000-word blog post with LinkedIn hyperlinks
  - 20 clickbait titles (under 100 characters)
  - 1-line episode summary
  - 20 clickbait quotes summarizing key areas of the episode
  - Chapter timestamps (ready-to-use episode markers)
  - LinkedIn post with guest description, 3 key takeaways, and CTA (with placeholder links for YouTube and Newsletter)
  - Keywords (comma-separated, max 500 characters, includes thedollardiaries, tdd, dubai, guest name, company, role)
  - Hashtags (same keywords with # prefix)
- **Download & Copy Features**: Download any deliverable as TXT file or copy to clipboard with SVG icons
- **Processing Animations**: Real-time visual feedback during processing with step-by-step status updates
- **Dark Mode UI**: Beautiful dark theme matching the 21SIXTY brand
- **OpenAI Credit Tracking**: Monitor API usage in real-time with pill-style display matching version badge
- **Usage Dashboard**: Track and visualize monthly usage costs for both OpenAI and AssemblyAI with interactive charts and billing links
- **Prompt Editor**: Modern grid-based prompt editor with card layout (no nested scrolling). Authentication required to access and edit prompts. Includes variables reference with copy functionality
- **Unified Header Pills**: Version and OpenAI credits displayed as matching pills on the same line
- **Automatic File Cleanup**: Periodic cleanup runs every 2 weeks to automatically remove old MP3 files and prevent disk space issues

## Tech Stack

- **Backend**: Python 3.12+ with FastAPI (tested with Python 3.12.3)
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **AI Generation**: OpenAI API (GPT-4)
- **Speech-to-Text**: AssemblyAI (cloud-based, no model downloads)
- **Deployment**: Nginx reverse proxy

## Quick Start

### Prerequisites

- Python 3.12+ (Python 3.12.3 recommended)
- OpenAI API key (for content generation)
- AssemblyAI API key (for transcription) - [Get one here](https://www.assemblyai.com/)
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

# Add your AssemblyAI API key (for transcription):
ASSEMBLYAI_API_KEY=your-assemblyai-api-key-here
```

You can get your API keys from:
- OpenAI API key: https://platform.openai.com/api-keys
- AssemblyAI API key: https://www.assemblyai.com/ (free tier available)

4. Run the application:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

5. Open your browser to `http://localhost:8001`

## Usage

1. **Upload Audio File**: Select an audio file (MP3, WAV, M4A, OGG, or FLAC) using the file selector
2. **Process Audio**: Click "Process Audio" - the system will:
   - Check localStorage for cached data (if same file was processed before, uses cache)
   - Upload and save the audio file
   - Generate transcript automatically using AssemblyAI (cloud-based, no model downloads)
   - Display processing animations with real-time status
3. **Enter Guest Information**: Fill in the guest's name, title, company, and LinkedIn profile
4. **Generate Content**: Click "Generate Content" to create all 10 content types using AI
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

**Note:** The endpoint accepts form data with file upload. Transcripts are automatically generated using AssemblyAI (cloud-based speech-to-text).

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
  "youtube_summary": "3 paragraph episode summary...",
  "blog_post": "2000 word blog post...",
  "clickbait_titles": ["Title 1", "Title 2", ...],
  "two_line_summary": "Line 1\nLine 2",
  "quotes": ["Quote 1", "Quote 2", ...],
  "chapter_timestamps": ["00:00:00 - Chapter 1", ...],
  "linkedin_post": "LinkedIn post content...",
  "keywords": "thedollardiaries, tdd, dubai, guest name, company, role, ...",
  "hashtags": "#thedollardiaries, #tdd, #dubai, #guestname, ..."
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
│   │   ├── openai_service.py   # OpenAI integration
│   │   ├── content_generator.py # Content generation
│   │   └── prompts_service.py  # Prompt management
│   ├── utils/
│   │   └── file_handler.py     # File cleanup utilities (periodic cleanup every 2 weeks)
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

- `OPENAI_API_KEY`: Your OpenAI API key (required for content generation) - [Get one here](https://platform.openai.com/api-keys)
- `OPENAI_MODEL`: Model to use (default: gpt-4o-mini)
- `ASSEMBLYAI_API_KEY`: Your AssemblyAI API key (required for transcription) - [Get one here](https://www.assemblyai.com/)
- `UPLOAD_DIR`: Directory for temporary files (default: ./uploads)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins for CORS

**Important:** The OpenAI API requires the `openai` Python package version 1.40.0 or higher (specified in `requirements.txt`).

## AI Prompts

The application uses customizable prompts for generating different content types. All prompts can be edited through the Prompts Editor in the web interface. Below are the default prompts:

### YouTube Summary Prompt
```
You are writing a summary for a YouTube video description for The Dollar Diaries podcast.

Guest Information:
- Name: {guest_name}
- Title: {guest_title}
- Company: {guest_company}

Transcript:
{transcript}

Please create a compelling 3-paragraph summary for YouTube that:
1. Introduces the guest and their background in the first paragraph
2. Highlights the key topics and insights discussed in the second paragraph
3. Teases what viewers will learn or take away in the third paragraph

Make it engaging, professional, and suitable for a YouTube video description.
```

### Blog Post Prompt
```
You are writing a comprehensive 2000-word blog post based on a podcast episode transcript from The Dollar Diaries podcast.

Guest Information:
- Name: {guest_name}
- Title: {guest_title}
- Company: {guest_company}
- LinkedIn: {guest_linkedin}

Transcript:
{transcript}

Instructions:
1. Write a comprehensive 2000-word blog post based on this episode
2. In the FIRST PARAGRAPH, hyperlink the guest's name to their LinkedIn profile using markdown format: [Name](LinkedIn_URL)
3. Structure the blog post with engaging subheadings
4. Include key insights, quotes, and takeaways from the episode
5. Make it valuable and readable for the audience
6. End with a strong conclusion

Format the LinkedIn hyperlink in the first paragraph like this:
In this episode of The Dollar Diaries, we speak with [{guest_name}]({guest_linkedin}), {guest_title} at {guest_company}, about...

Write the full blog post now:
```

### Clickbait Titles Prompt
```
Generate 20 clickbait-style titles for a podcast episode, each under 100 characters.

Guest: {guest_name} from {guest_company}

Transcript excerpt:
{transcript}

Requirements:
- Each title must be under 100 characters
- Include the guest's name ({guest_name}) and/or company ({guest_company})
- Make them compelling and click-worthy
- Based on the actual content of the episode
- Number each title from 1 to 20
- Return only the titles, one per line, without any other text

Format:
1. Title here
2. Title here
...
```

### Two Line Summary Prompt
```
Create a concise two-line summary of this podcast episode.

Transcript:
{transcript}

Write exactly two lines that capture the essence of the episode. Make it engaging and informative.

Format:
Line 1
Line 2
```

### Quotes Prompt
```
Extract 20 of the most notable, insightful, or quotable statements from this podcast transcript.

Transcript with timestamps:
{transcript_with_timecodes}

Requirements:
- Select the 20 most impactful quotes
- They should be complete thoughts or statements
- Include the timestamp in format [HH:MM:SS] before each quote
- Number each quote from 1 to 20
- Return only the quotes, one per line

Format:
1. [HH:MM:SS] Quote text here
2. [HH:MM:SS] Quote text here
...
```

### Chapter Timestamps Prompt
```
Analyze this podcast transcript and create YouTube chapter timestamps.

Transcript with timecodes:
{transcript_with_timecodes}

Video duration: {video_duration} seconds

Create YouTube-ready chapter timestamps that:
1. Identify natural topic breaks in the conversation
2. Use format: 00:00:00 - Chapter Title
3. Create 8-12 meaningful chapters
4. Each chapter title should be descriptive and engaging
5. Timestamps should align with topic transitions

Return only the timestamps in this exact format:
00:00:00 - Chapter Title 1
00:05:30 - Chapter Title 2
...
```

### LinkedIn Post Prompt
```
You are creating a professional LinkedIn post for The Dollar Diaries podcast episode.

Guest Information:
- Name: {guest_name}
- Title: {guest_title}
- Company: {guest_company}
- LinkedIn: {guest_linkedin}

Transcript:
{transcript}

Instructions:
1. **Opening Hook**: Start with an engaging hook that introduces the guest and episode topic. Mention the guest's name and link to their LinkedIn profile using markdown format: [{guest_name}]({guest_linkedin})

2. **Guest Description**: Write 2-3 sentences describing the guest's background, expertise, achievements, and why they're an interesting guest. Make it compelling and highlight their credibility.

3. **Three Key Takeaways**: Present exactly three key takeaways from the episode. Format them as:
   • Takeaway 1: [Clear, actionable insight]
   • Takeaway 2: [Clear, actionable insight]
   • Takeaway 3: [Clear, actionable insight]
   
   Each takeaway should be:
   - Specific and actionable
   - Based on actual content from the transcript
   - Valuable to the LinkedIn audience
   - 1-2 sentences each

4. **Call-to-Action (CTA)**: End with a clear CTA that includes:
   - Placeholder link to watch the episode: [Watch on YouTube](YOUTUBE_LINK_PLACEHOLDER)
   - Placeholder link to read the newsletter: [Read in Newsletter](NEWSLETTER_LINK_PLACEHOLDER)
   - Make the CTA engaging and encourage engagement (likes, comments, shares)

Formatting Requirements:
- Use line breaks (double line breaks) between sections for readability
- Keep total length between 300-500 words (optimal for LinkedIn engagement)
- Use professional but conversational tone
- Include relevant hashtags if appropriate (2-3 max)
- Make it scannable with clear structure
- Optimize for LinkedIn's algorithm (engagement-focused)

Write the complete LinkedIn post now:
```

### Keywords Prompt
```
Generate a comma-separated list of keywords based on this podcast episode transcript.

Guest Information:
- Name: {guest_name}
- Title: {guest_title}
- Company: {guest_company}

Transcript:
{transcript}

Requirements:
- MUST include these exact keywords: 'thedollardiaries', 'tdd', 'dubai', '{guest_name}', '{guest_company}', '{guest_title}'
- Add additional relevant keywords based on the conversation topics, themes, and content
- All keywords should be lowercase
- Separate keywords with commas and a single space: ', '
- Total character count (including commas and spaces) must NOT exceed 500 characters
- Focus on topics discussed, industries mentioned, key concepts, and relevant terms
- Return ONLY the comma-separated keywords, nothing else

Format:
keyword1, keyword2, keyword3, ...
```

## License

See [LICENSE.md](LICENSE.md) for details.

**Summary**: You can use, modify, and distribute this code freely, but you cannot use the 21SIXTY name, logo, or branding in your version.

## Need Professional Help?

**🚀 Ready to take your content generation to the next level?**

This open-source tool gives you the foundation, but deploying and customizing it for your specific needs can be challenging. Whether you're looking to:

- **Deploy your own production-ready instance** with enterprise-grade security and scalability
- **Customize the AI prompts** to match your brand voice and content strategy
- **Integrate with your existing workflow** and content management systems
- **Scale for high-volume processing** with optimized infrastructure
- **Get expert guidance** on best practices and advanced configurations

**We're here to help you succeed!**

👉 **Visit [21sixty.media](https://21sixty.media)** to explore our full suite of content generation solutions and see how we can transform your podcast content workflow.

📧 **Email [info@21sixty.media](mailto:info@21sixty.media)** for:
- **Free consultation** on deployment strategies tailored to your needs
- **Personalized implementation support** from our technical experts
- **Enterprise solutions** with dedicated support and custom features
- **Quick answers** to your deployment and customization questions

Don't let technical hurdles slow you down. Let our team help you get up and running quickly with a solution that's perfectly tailored to your requirements. **Reach out today and let's build something amazing together!**

## Support

For issues or questions about the open-source codebase, please open an issue on the repository.

For deployment assistance, custom solutions, or professional consultations, contact us at [info@21sixty.media](mailto:info@21sixty.media) or visit [21sixty.media](https://21sixty.media).

