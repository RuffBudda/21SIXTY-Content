# 21SIXTY Content Generator - Feature Documentation

**Version:** v138  
**Last Updated:** 2024-12-21

This document provides a comprehensive overview of all features, architecture, and implementation details for AI agents working on this codebase.

## Table of Contents

1. [Feature List](#feature-list)
2. [Architecture Overview](#architecture-overview)
3. [Core Features Deep Dive](#core-features-deep-dive)
4. [Data Flow](#data-flow)
5. [Storage & Caching](#storage--caching)
6. [API Endpoints](#api-endpoints)
7. [Frontend Components](#frontend-components)
8. [Adding New Features](#adding-new-features)

---

## Feature List

### 1. Audio File Upload & Processing
- **Location**: `frontend/app.js` - `processVideo()`, `backend/main.py` - `/api/process-video`
- **Description**: Users upload audio files (MP3, WAV, M4A, OGG, FLAC) instead of downloading from YouTube
- **Implementation**:
  - File input with validation for supported formats
  - FormData submission to backend
  - File saved to `backend/uploads/` directory
  - File hash (SHA-256) generated for caching

### 2. Audio File Processing with Whisper API
- **Location**: `backend/main.py` - `process_video()`
- **Description**: Processes uploaded audio files, generates transcripts using Whisper API, and saves them for content generation
- **Implementation**:
  - Accepts audio file upload via multipart/form-data
  - Validates file format (MP3, WAV, M4A, OGG, FLAC)
  - Generates unique video_id from file hash and timestamp
  - Saves file to `backend/uploads/` directory
  - Calls OpenAI Whisper API to generate transcript with timecodes
  - Returns transcript structure with segments containing start, end, and text
  - Falls back to empty transcript if Whisper API fails (doesn't break the request)

### 3. LocalStorage Caching System
- **Location**: `frontend/app.js` - `processVideo()`, `getFileHash()`, `fileToBase64()`
- **Description**: Intelligent caching to avoid reprocessing same files
- **Implementation**:
  - Generates SHA-256 hash of uploaded audio file
  - Cache key format: `processed_{fileHash}` (YouTube URL removed from cache key)
  - Stores: transcript data, video info, timestamp
  - Audio file cached as base64: `audio_{fileHash}`
  - Generated content cached: `content_{videoId}`
  - Checks cache before processing, uses cached data if available

### 4. Processing Animations
- **Location**: `frontend/index.html` - `#processingAnimation`, `frontend/app.js` - `processVideo()`
- **Description**: Real-time visual feedback during processing
- **Implementation**:
  - Spinner animation with CSS keyframes
  - Step-by-step status text updates:
    - "Uploading audio file..."
    - "Extracting transcript from YouTube..."
    - "Processing data..."
    - "Almost done..."
  - Updates every 2 seconds

### 5. AI Content Generation
- **Location**: `backend/services/content_generator.py`
- **Description**: Generates 10 types of content using OpenAI GPT-4
- **Content Types**:
  1. **Transcript with Timecodes** - Formatted transcript display
  2. **3 Paragraph YouTube Summary** - SEO-optimized summary
  3. **2000 Word Blog Post** - Full blog post with LinkedIn hyperlinks
  4. **20 Clickbait Titles** - Titles under 100 characters
  5. **2 Line Summary** - Concise episode summary
  6. **20 Quotes** - Notable quotes from episode
  7. **YouTube Chapter Timestamps** - Ready-to-use chapter markers
  8. **LinkedIn Post** - Post with guest description, 3 key takeaways, and CTA (includes placeholder links for YouTube and Newsletter)
  9. **Keywords** - Comma-separated keywords based on transcript (max 500 characters, includes thedollardiaries, tdd, dubai, guest name, company, role). No trailing "..." ellipsis.
  10. **Hashtags** - Same keywords as above but with # prefix for each keyword. Spaces removed from each hashtag. Max 500 characters total.

### 6. Unified Header Pills
- **Location**: `frontend/index.html` - `.header-pills`, `frontend/styles.css` - `.version`, `.openai-pill`
- **Description**: Version and OpenAI credits displayed as matching pills on the same line
- **Implementation**:
  - Version pill: Shows current version (v94) with code-like font (Courier New)
  - OpenAI pill: Shows "OpenAI:" label and credit value with matching styling
  - Both pills have same dimensions: padding 2px 8px, border-radius 12px
  - Same styling: background-color (var(--bg-card)), border (1px solid var(--border-color)), font-size (0.75rem)
  - Displayed in flex container (`.header-pills`) with 8px gap
  - OpenAI value uses monospace font and accent-blue color

### 7. Download & Copy Functionality
- **Location**: `frontend/app.js` - `downloadAsTxt()`, `copyToClipboard()`
- **Description**: Download any deliverable as TXT or copy to clipboard
- **Implementation**:
  - Download: Creates Blob, triggers browser download with appropriate filename
  - Copy: Uses Clipboard API, shows visual feedback (checkmark icon)
  - SVG icons for both actions
  - Filename mapping for each deliverable type

### 7. Prompt Editor (Modern Grid Layout with Variables Reference)
- **Location**: `frontend/index.html` - Prompts tab, `frontend/styles.css` - Grid styles, `backend/services/prompts_service.py`
- **Description**: Modern grid-based prompt editor with card layout. Authentication required to access and edit prompts
- **Implementation**:
  - **Authentication Enforcement**: 
    - Frontend checks authentication when switching to prompts tab (`switchTab()` function)
    - If not authenticated, shows login modal and switches back to content tab
    - Backend requires authentication for GET/POST `/api/prompts` endpoints
  - **Modern UI/UX Design**:
    - Responsive CSS Grid layout (2 columns on desktop, 1 on mobile)
    - Each prompt in its own card with hover effects and category badges
    - Fixed height containers prevent scroll-within-scroll issue
    - Custom scrollbar styling for grid container
    - Header with action buttons (Save All, Reset) at the top
    - Category badges for each prompt type (Summary, Long Form, Titles, etc.)
  - **Variables Reference Section**:
    - Displays all available prompt variables with descriptions
    - Variables shown: `{guest_name}`, `{guest_title}`, `{guest_company}`, `{guest_linkedin}`, `{transcript}`, `{transcript_with_timecodes}`, `{video_title}`, `{video_duration}`
    - Each variable has a copy button and can be clicked to copy
    - Visual feedback when variable is copied (checkmark icon)
    - Responsive grid layout for variables
  - **Technical Details**:
    - Stores prompts in `backend/prompts.json`
    - Editable textareas for each prompt type (8 prompts total)
    - Save/Reset functionality
    - Prompts use placeholders: `{guest_name}`, `{transcript}`, `{guest_title}`, `{guest_company}`, `{guest_linkedin}`, `{transcript_with_timecodes}`, `{video_title}`, `{video_duration}`
    - Grid uses `display: grid` with `grid-template-columns: repeat(auto-fit, minmax(400px, 1fr))`
    - Max height on grid container: `calc(100vh - 300px)` with overflow-y: auto
    - Variables copy function uses Clipboard API with visual feedback

### 8. Projects Gallery
- **Location**: `frontend/index.html` - Gallery tab, `frontend/app.js` - Gallery functions, `frontend/styles.css` - Gallery styles
- **Description**: Browse and manage all processed projects stored in localStorage
- **Implementation**:
  - Scans localStorage for all projects (keys starting with `processed_`)
  - Displays projects in a responsive grid layout
  - Each project card shows:
    - Video title
    - Processing date and time
    - Duration
    - Status indicator (Transcript Only / Content Generated)
  - **Open Project**: Loads transcript data, video info, and generated content (if available)
  - **Delete Project**: Removes project from localStorage (including associated audio and content)
  - Auto-refreshes when switching to gallery tab
  - Empty state message when no projects exist

### 9. Authentication System
- **Location**: `backend/main.py` - Auth endpoints, `frontend/app.js` - Auth functions
- **Description**: Master password authentication with session management
- **Implementation**:
  - HTTPBearer token-based auth
  - Password hashed with SHA-256
  - Remember me functionality (localStorage vs sessionStorage)
  - Auto-logout on 401 responses

### 9. OpenAI Credit Tracking
- **Location**: `backend/services/openai_service.py` - `get_credit_info()`
- **Description**: Monitor OpenAI API usage and credits
- **Implementation**:
  - Calls OpenAI API to check account status
  - Displays status in header (Active/Inactive)
  - Updates every 30 seconds when authenticated

### 10. Periodic File Cleanup
- **Location**: `backend/main.py` - `periodic_cleanup()`, `backend/utils/file_handler.py`
- **Description**: Automatically removes old MP3 files every 2 weeks to prevent disk space issues
- **Implementation**:
  - Uses APScheduler to run cleanup task every 2 weeks (14 days)
  - Removes files older than 336 hours (2 weeks) from `backend/uploads/` directory
  - Cleans up `mp3_files` dictionary entries for deleted files
  - Logs cleanup activity including number of files deleted and total size freed
  - Runs automatically on server startup and then every 2 weeks
  - Default cleanup period: 336 hours (configurable in FileHandler)

---

## Architecture Overview

### Backend Structure
```
backend/
├── main.py                    # FastAPI app, routes, auth, periodic cleanup scheduler
├── models.py                  # Pydantic models for requests/responses
├── services/
│   ├── openai_service.py     # OpenAI API integration
│   ├── content_generator.py   # Content generation orchestration
│   └── prompts_service.py    # Prompt management
└── utils/
    └── file_handler.py        # File cleanup utilities (periodic cleanup every 2 weeks)
```

### Frontend Structure
```
frontend/
├── index.html                # Main HTML structure
├── app.js                    # All JavaScript logic
└── styles.css                # All styling
```

### Key Technologies
- **Backend**: FastAPI (Python 3.12+)
- **Frontend**: Vanilla JavaScript (no frameworks)
- **AI**: OpenAI GPT-4 API
- **Storage**: Browser localStorage, File system (uploads)

---

## Core Features Deep Dive

### Audio Upload Flow

1. **User selects file** → `audioFileInput` change event
2. **File name displayed** → Updates `#audioFileName` element
3. **User clicks "Process Audio"** → `processVideo()` function
4. **File validation** → Checks file extension
5. **Hash generation** → `getFileHash()` creates SHA-256 hash
6. **Cache check** → Looks for `processed_{hash}` in localStorage
7. **If cached**: Returns cached data immediately
8. **If not cached**:
   - Creates FormData with file
   - POST to `/api/process-video`
   - Backend generates unique video_id from file hash + timestamp
   - Backend saves file to `uploads/` directory
   - Backend returns empty transcript structure
   - Response includes empty transcript data (user must provide transcript manually)
   - Frontend caches result in localStorage

### Content Generation Flow

1. **User fills guest info** → Name, title, company, LinkedIn
2. **User clicks "Generate Content"** → `generateContent()` function
3. **Check cache** → Looks for `content_{videoId}` in localStorage
4. **If cached**: Displays cached content
5. **If not cached**:
   - POST to `/api/generate-content` with transcript and guest info
   - Backend calls `ContentGenerator.generate_all_content()`
   - Each content type generated sequentially using OpenAI
   - Prompts loaded from `prompts.json` or defaults
   - Results returned and displayed
   - Results cached in localStorage

### Caching Strategy

**Cache Keys:**
- `processed_{fileHash}` - Processed transcript data (cache key based on file hash only, no YouTube URL component)
- `audio_{fileHash}` - Audio file as base64
- `content_{videoId}` - Generated content

**Note:** Cache key uses only file hash to ensure same audio file always uses same cache entry, regardless of processing context.

**Cache Structure:**
```javascript
{
  transcriptData: {...},  // or data: {...} for content
  videoInfo: {...},      // or timestamp for content
  timestamp: 1234567890  // Unix timestamp
}
```

**Cache Invalidation:**
- Manual: User can clear browser localStorage
- Automatic: None (cache persists until cleared)
- Note: Cache is based on file hash only (YouTube URL no longer affects cache key)

---

## Data Flow

### Processing Pipeline

```
User Uploads Audio File
    ↓
Generate File Hash (SHA-256)
    ↓
Check localStorage Cache
    ↓
[Cache Hit] → Return Cached Data
    ↓
[Cache Miss] → Upload to Backend
    ↓
Backend Saves File
    ↓
Return Transcript Data (transcripts must be provided manually or via speech-to-text)
    ↓
Cache in localStorage
    ↓
Display Transcript
    ↓
User Enters Guest Info
    ↓
Generate Content (Check Cache)
    ↓
[Cache Hit] → Display Cached Content
    ↓
[Cache Miss] → Call OpenAI API
    ↓
Generate All 7 Content Types
    ↓
Cache Results
    ↓
Display All Deliverables
```

---

## Storage & Caching

### localStorage Structure

```javascript
{
  // Authentication
  "authToken": "hashed_token",
  "rememberMe": "true",
  
  // Processed data (by file hash only)
  "processed_abc123...": {
    transcriptData: {...},
    videoInfo: {...},
    timestamp: 1234567890
  },
  
  // Audio file (by file hash)
  "audio_abc123...": "data:audio/mp3;base64,...",
  
  // Generated content (by video ID)
  "content_videoId123": {
    data: {...},
    timestamp: 1234567890
  }
}
```

### File System Storage

- **Location**: `backend/uploads/`
- **Naming**: `{videoId}.mp3`
- **Cleanup**: Files stored temporarily, can be downloaded via `/api/download-audio/{videoId}`
- **Automatic Cleanup**: Periodic cleanup runs every 2 weeks (336 hours) to remove old MP3 files
  - Implemented using APScheduler
  - Removes files older than 2 weeks
  - Also cleans up `mp3_files` dictionary entries for deleted files
  - Logs cleanup activity including number of files deleted and total size freed

---

## API Endpoints

### POST /api/process-video
**Purpose**: Process uploaded audio file and optionally extract transcript

**Request Format**: `multipart/form-data`
- `audio_file`: File (MP3, WAV, M4A, OGG, FLAC) - **Required**

**Note**: Transcripts must be provided manually or through speech-to-text integration. The endpoint only accepts audio file uploads.

**Response**:
```json
{
  "success": true,
  "transcript": "Full transcript text...",
  "transcript_with_timecodes": [
    {
      "text": "Hello world",
      "start": 0.0,
      "duration": 2.5,
      "end": 2.5
    }
  ],
  "video_title": "Video Title",
  "video_duration": 3600.0,
  "video_id": "abc123"
}
```

**Implementation**: `backend/main.py` - `process_video()`

### POST /api/generate-content
**Purpose**: Generate all content types using AI

**Request**:
```json
{
  "transcript": "Full transcript...",
  "transcript_with_timecodes": [...],
  "guest_name": "John Doe",
  "guest_title": "CEO",
  "guest_company": "Company Name",
  "guest_linkedin": "https://linkedin.com/in/johndoe",
  "video_title": "Video Title",
  "video_duration": 3600.0
}
```

**Response**:
```json
{
  "youtube_summary": "3 paragraph summary...",
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

**Implementation**: `backend/main.py` - `generate_content()`

### GET /api/download-audio/{video_id}
**Purpose**: Download processed audio file

**Implementation**: `backend/main.py` - `download_audio()`

### GET /api/openai-credits
**Purpose**: Get OpenAI API credit status

**Implementation**: `backend/main.py` - `get_openai_credits()`

### POST /api/prompts
**Purpose**: Update AI prompts

**Implementation**: `backend/main.py` - `update_prompts()`

### GET /api/prompts
**Purpose**: Get current AI prompts

**Implementation**: `backend/main.py` - `get_prompts()`

---

## Frontend Components

### Step 1: Audio Upload
- **File Input**: Hidden, triggered by "Select Audio File" button
- **File Name Display**: Shows selected file name
- **Process Button**: Triggers `processVideo()` (labeled "Process Audio")
- **Processing Animation**: Shows during processing
- **Note**: Transcripts must be provided manually or through speech-to-text integration

### Step 2: Guest Information
- **Form Fields**: Name, Title, Company, LinkedIn
- **Generate Button**: Triggers `generateContent()`
- **Validation**: All fields required, LinkedIn must be valid URL

### Results Section
- **7 Deliverable Cards**: Each with download/copy buttons
- **Transcript Display**: Formatted with timecodes
- **Copy Feedback**: Visual confirmation (checkmark icon)
- **Download**: Automatic filename based on deliverable type

---

## Adding New Features

### Adding a New Content Type

1. **Backend**:
   - Add method in `ContentGenerator` class
   - Add to `generate_all_content()` return dict
   - Update `GenerateContentResponse` model in `models.py`

2. **Frontend**:
   - Add result card in `index.html`
   - Add display logic in `displayResults()` function
   - Add download/copy button handlers (already handled by event delegation)

3. **Prompts**:
   - Add prompt field in `prompts.json`
   - Add textarea in Prompts Editor tab
   - Update `PromptsService` if needed

### Adding a New Cache Type

1. **Generate unique cache key** (e.g., `newFeature_{identifier}`)
2. **Check cache before operation**:
   ```javascript
   const cacheKey = `newFeature_${identifier}`;
   const cached = localStorage.getItem(cacheKey);
   if (cached) {
     return JSON.parse(cached);
   }
   ```
3. **Store after operation**:
   ```javascript
   localStorage.setItem(cacheKey, JSON.stringify(data));
   ```

### Modifying Processing Flow

1. **Update `processVideo()` in `frontend/app.js`**
2. **Update `/api/process-video` in `backend/main.py`**
3. **Update `YouTubeService` methods if needed**
4. **Test cache invalidation** (may need to clear old cache keys)

### Adding New File Format Support

1. **Frontend**: Update `accept` attribute in file input
2. **Backend**: Update validation in `process_video()` endpoint
3. **Documentation**: Update README and this file

---

## Important Notes for AI Agents

### Version Management
- **Current Version**: v138
- **Version Location**: `frontend/index.html` (title and header)
- **Update**: Change in both places when incrementing version

### Cache Considerations
- localStorage has size limits (~5-10MB)
- Base64 audio files can be large
- Consider implementing cache size limits or cleanup
- Cache keys should be unique and descriptive

### Error Handling
- All API calls should handle 401 (unauthorized) → redirect to login
- Network errors should show user-friendly messages
- Validation errors should be clear and actionable

### Security
- Authentication required for all processing endpoints
- File uploads validated for type and size
- YouTube URLs validated before processing
- No sensitive data in localStorage (only processed content)

### Performance
- Content generation is sequential (could be parallelized)
- Large audio files may take time to hash
- Consider adding progress indicators for long operations
- Cache reduces API calls significantly

### Testing Checklist
When adding features, test:
1. Cache hit scenario (same file, same URL)
2. Cache miss scenario (new file/URL)
3. File format validation
4. Error handling (network, validation, API errors)
5. UI feedback (animations, status messages)
6. Download/copy functionality
7. Authentication flow

---

## File Locations Reference

### Backend
- Main app: `backend/main.py`
- OpenAI service: `backend/services/openai_service.py`
- Content generator: `backend/services/content_generator.py`
- Prompts service: `backend/services/prompts_service.py`
- Models: `backend/models.py`
- Prompts data: `backend/prompts.json`

### Frontend
- HTML: `frontend/index.html`
- JavaScript: `frontend/app.js`
- Styles: `frontend/styles.css`

### Documentation
- This file: `Documentations/ContGen.md`
- Deployment: `Documentations/DEPLOYMENT.md`
- YouTube fixes: `Documentations/yt_fix.md`
- Quick start: `Documentations/QUICKSTART.md`

---

## Common Patterns

### File Hash Generation
```javascript
async function getFileHash(file) {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
```

### Cache Check Pattern
```javascript
const cacheKey = `feature_${identifier}`;
const cached = localStorage.getItem(cacheKey);
if (cached) {
  try {
    const data = JSON.parse(cached);
    // Use cached data
    return data;
  } catch (e) {
    // Invalid cache, continue with fresh data
  }
}
// Process and cache
const result = await processData();
localStorage.setItem(cacheKey, JSON.stringify(result));
```

### FormData Upload Pattern
```javascript
const formData = new FormData();
formData.append('audio_file', audioFile);
// Only audio_file is appended, no YouTube URL

const response = await fetch('/api/process-video', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${authToken}`
  },
  body: formData
});
```

---

**End of Documentation**

For questions or updates, refer to the codebase or update this document accordingly.

