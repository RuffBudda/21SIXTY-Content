# 21SIXTY Content Generator - Feature Documentation

**Version:** v150  
**Last Updated:** 2024-12-22

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

### 2. Audio File Processing with Faster Whisper
- **Location**: `backend/main.py` - `process_video()`
- **Description**: Processes uploaded audio files, generates transcripts using Faster Whisper (local), and saves them for content generation
- **Implementation**:
  - Accepts audio file upload via multipart/form-data
  - Validates file format (MP3, WAV, M4A, OGG, FLAC)
  - Generates unique video_id from file hash and timestamp
  - Saves file to `backend/uploads/` directory
  - Uses Faster Whisper (local) to generate transcript with timecodes
  - Returns transcript structure with segments containing start, end, and text
  - Falls back to empty transcript if Faster Whisper fails (doesn't break the request)
  - Lazy model loading - model loads on first use for faster startup
  - Configurable via environment variables (model size, device, compute type)

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
  11. **Full Episode Description** - Concatenation of 3 Paragraph Summary + Standard Static Content + Chapter Timestamps (v142+)

### 6. Unified Header Pills
- **Location**: `frontend/index.html` - `.header-pills`, `frontend/styles.css` - `.version`, `.openai-pill`
- **Description**: Version and OpenAI credits displayed as matching pills on the same line
- **Implementation**:
  - Version pill: Shows current version (v150) with code-like font (Courier New)
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

### 8. Projects Gallery
- **Location**: `frontend/app.js` - `loadGallery()`, `openProject()`, `deleteProject()`
- **Description**: Browse and manage all processed projects stored in localStorage
- **Implementation**:
  - Reads all `processed_*` keys from localStorage
  - Displays project cards with title, date, duration, and content status
  - Click "Open Project" to load project data and switch to Content tab
  - Delete button removes project and all related cache entries
  - Shows empty state when no projects exist

### 9. Prompt Editor
- **Location**: `frontend/index.html` - Prompts Editor tab, `frontend/app.js` - `loadPrompts()`, `savePrompts()`
- **Description**: Modern grid-based prompt editor with card layout
- **Implementation**:
  - Grid layout with prompt tiles (no nested scrolling)
  - Each tile shows preview and expandable content
  - Edit requires password authentication
  - Variables reference section with copy functionality
  - Save all prompts button
  - Reset to defaults button

### 10. OpenAI Credit Tracking
- **Location**: `frontend/app.js` - `loadCredits()`, `backend/main.py` - `/api/openai-credits`
- **Description**: Monitor API usage in real-time
- **Implementation**:
  - Fetches credits from OpenAI API
  - Updates every 30 seconds if authenticated
  - Displays in header pill matching version badge style
  - Shows "Fetching..." while loading

### 11. Processing Spinner & Blackout (v140)
- **Location**: `frontend/app.js` - `showLoading()`, `hideLoading()`, `processVideo()`
- **Description**: Loading overlay with spinner during file processing
- **Implementation**:
  - Global loading overlay with spinner animation
  - Blackout background similar to content generation spinner
  - Shows during audio file processing
  - Hides when processing completes

### 12. Guest Information Pre-population Fix (v140)
- **Location**: `frontend/app.js` - `openProject()`
- **Description**: Guest information fields cleared when opening projects
- **Implementation**:
  - Clears guestName, guestTitle, guestCompany, guestLinkedIn input fields
  - Ensures clean state for new entries

### 13. Transcript Display Improvements (v140)
- **Location**: `frontend/app.js` - `displayTranscript()`, `formatTranscriptWithTimecodes()`
- **Description**: Improved transcript display with better format handling
- **Implementation**:
  - Prioritizes `transcript_with_timecodes` array when available
  - Handles multiple data format variations (`{start, text}`, `{start, end, text}`, `{start_time, transcript}`)
  - Filters empty lines from formatted output
  - Graceful fallback to plain transcript if timecodes unavailable
  - See `Documentations/transcript_timecode_fixes.md` for detailed fix history

### 14. Content Generation from Transcript (v141)
- **Location**: `backend/services/prompts_service.py` - prompt templates
- **Description**: Enhanced prompts to ensure content is generated from actual transcript content
- **Implementation**:
  - Two line summary prompt emphasizes using ONLY transcript content
  - Quotes prompt requires EXACT wording from transcript (no paraphrasing)
  - Chapter timestamps prompt requires identifying actual topic transitions in transcript
  - All prompts explicitly state to use actual transcript content, not generic statements

### 15. Project Deletion Cache Clearing (v141)
- **Location**: `frontend/app.js` - `deleteProject()` function
- **Description**: Comprehensive cache clearing when projects are deleted
- **Implementation**:
  - Clears all `content_` keys related to the deleted video_id
  - Clears all `processed_` keys that reference the deleted video_id
  - Ensures complete cleanup of all cached data related to the project
  - Prevents orphaned cache entries

### 16. Tab Button Click Handler Fix (v141)
- **Location**: `frontend/app.js` - `setupEventListeners()` function
- **Description**: Fixed tab switching when clicking SVG icons within tab buttons
- **Implementation**:
  - Changed from `e.target` to `e.currentTarget` to handle clicks on child elements
  - Ensures tab switching works when clicking anywhere on the button, including SVG icons
  - Prevents `tabName` from being null when clicking child elements

### 17. API Tab Button and Tile Improvements (v141)
- **Location**: `frontend/index.html` - API tab button and tile, `frontend/app.js` - event listeners
- **Description**: Removed SVG from API tab button, made API tile square, fixed click handler
- **Implementation**:
  - Removed SVG icon from API tab button (now shows only "API" text)
  - Made API tile square using `aspect-ratio: 1` with flexbox centering
  - Fixed click handler using event delegation for reliable click detection
  - Ensures API tile is clickable and properly styled

### 18. Standard Static Content Tile Format (v143)
- **Location**: `frontend/index.html` - Prompts Editor tab, `frontend/app.js` - expand/edit handlers
- **Description**: Converted Standard Static Content to prompt-tile format with expand/edit functionality
- **Implementation**:
  - Uses same prompt-tile structure as other prompts
  - Expand button toggles visibility of content
  - Edit button enables editing without password (saves to server via prompts API)
  - Preview shows truncated content
  - Auto-saves when prompts are saved (v145: now saves to server instead of localStorage)
  - Updates Full Episode Description when content changes
  - Server-side storage: Content persisted in `backend/prompts.json` (v145)

### 19. N8N Setup Instructions and Bearer Token Display (v143)
- **Location**: `frontend/index.html` - API tab, `frontend/app.js` - bearer token functions
- **Description**: Added N8N setup instructions and bearer token display with visibility toggle
- **Implementation**:
  - Step-by-step N8N setup instructions in API documentation
  - Bearer token display with visibility toggle (eye icon)
  - Copy button for bearer token
  - Token hidden by default (shows dots)
  - Token updates automatically when user logs in or switches to API tab
  - Webhook URL and copy button aligned on same line using flexbox

### 20. Full Episode Description Deliverable (v142)
- **Location**: `frontend/index.html` - Content tab, `frontend/app.js` - `updateFullEpisodeDescription()`
- **Description**: New deliverable that concatenates 3 Paragraph Summary + Standard Static Content + Chapter Timestamps
- **Implementation**:
  - Displayed as a result card in the Content tab
  - Automatically updates when any of its components change
  - Includes regenerate, download, and copy buttons
  - Concatenation logic: `youtubeSummary + standardStaticContent + chapterTimestamps`
  - Updates after content generation and when Standard Static Content is saved

### 21. Standard Static Content Server-Side Storage (v145)
- **Location**: `backend/prompts.json`, `backend/services/prompts_service.py`, `frontend/app.js`
- **Description**: Standard Static Content migrated from localStorage to server-side storage in prompts.json
- **Implementation**:
  - Added `standard_static_content` field to `backend/prompts.json` (default empty string)
  - Updated `PromptsService.update_prompts()` to handle `standard_static_content` as optional field
  - Frontend `loadPrompts()` loads `standard_static_content` from server
  - Frontend `performSavePrompts()` saves `standard_static_content` to server
  - `updateFullEpisodeDescription()` called after saving prompts to keep display in sync
  - Removed localStorage dependency - content now persisted on server
  - Migration support: localStorage value loaded initially, then overwritten by server data

### 22. Transcript Display in Step 2 and Enhanced Display Function (v147)
- **Location**: `frontend/index.html` - Step 2 card, `frontend/app.js` - `displayTranscript()`
- **Description**: Show transcript in Step 2 before generating deliverables, enhanced display function considering all previous fixes
- **Implementation**:
  - Added transcript preview section in Step 2 (Guest Information)
  - Enhanced `displayTranscript()` to accept optional target element ID
  - Comprehensive handling of all data formats (array, string, object)
  - Displays transcript in both Step 2 preview and main transcript area
  - User workflow: Process Audio → Review Transcript → Enter Guest Info → Generate Content
  - Removed Regenerate button from Step 2 (only in results section)
  - See `Documentations/transcript_timecode_fixes.md` for detailed fix history

### 23. Strengthened Prompts for Quotes and Chapter Timestamps (v147)
- **Location**: `backend/prompts.json`, `backend/services/prompts_service.py`
- **Description**: Enhanced prompts to ensure quotes and chapter timestamps are accurate to transcript
- **Implementation**:
  - Quotes prompt: Added CRITICAL REQUIREMENTS emphasizing exact wording, no paraphrasing
  - Chapter timestamps prompt: Added CRITICAL REQUIREMENTS emphasizing actual content and real topic transitions
  - Both prompts explicitly state to use only what is in the transcript
  - Prevents AI from creating generic or made-up content

### 24. Enhanced Whisper API Transcript Processing (v148)
- **Location**: `backend/main.py` - `process_video()` function, `frontend/app.js` - `displayTranscript()` and `formatTranscriptWithTimecodes()`
- **Description**: Enhanced Whisper API response handling with comprehensive logging and better error handling
- **Implementation**:
  - Added detailed logging at each step of transcript processing in backend
  - Better handling of dict vs object responses from Whisper API
  - Improved error handling for segment processing with try-catch per segment
  - Enhanced frontend display function with comprehensive console logging
  - Better error handling in formatTranscriptWithTimecodes function with per-segment try-catch
  - Changed Step 2 title to "Review Transcript & Enter Guest Information" (removed "Step 2:")
  - See `Documentations/transcript_timecode_fixes.md` Fix Attempt #6 for details

### 25. Faster Whisper Migration (v150)
- **Location**: `backend/main.py` - `process_video()` function, `backend/requirements.txt`
- **Description**: Replaced OpenAI Whisper API with Faster Whisper for local, free transcription
- **Implementation**:
  - Replaced OpenAI Whisper API calls with Faster Whisper (local Python library)
  - Lazy model loading - model loads on first use to speed up startup
  - Configurable via environment variables: `WHISPER_MODEL_SIZE`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`
  - No API costs - runs entirely on server
  - Same accuracy as Whisper API but faster
  - Automatic model download on first use (~500MB for base model)
  - Backward compatible - API response format unchanged
  - See `updatev150.md` for Ubuntu server installation steps
  - See `Documentations/transcript_timecode_fixes.md` Fix Attempt #7 for details

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
- **Storage**: Browser localStorage, File system (uploads), Server-side prompts.json

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
- `audio_{fileHash}` - Base64-encoded audio file
- `content_{videoId}` - Generated content for a specific video

**Cache Invalidation:**
- Project deletion clears all related cache entries
- Manual cache clearing via browser dev tools

---

## Data Flow

### Processing Flow
```
User Upload → File Hash → Cache Check → Backend Processing → Transcript Generation → Cache Storage → Display
```

### Content Generation Flow
```
Guest Info + Transcript → Cache Check → API Call → OpenAI Generation → Cache Storage → Display
```

---

## Storage & Caching

### localStorage Structure
- `processed_{fileHash}` - Processed video data
- `audio_{fileHash}` - Base64 audio files
- `content_{videoId}` - Generated content
- `authToken` - Authentication token (if remember me checked)
- `rememberMe` - Remember me preference

### Server-Side Storage
- `backend/prompts.json` - All prompts including Standard Static Content (v145+)
- `backend/uploads/` - Uploaded audio files (periodic cleanup every 2 weeks)

---

## API Endpoints

### POST /api/process-video
Process uploaded audio file and generate transcript.

### POST /api/generate-content
Generate all content types based on transcript and guest info.

### GET /api/prompts
Get all prompts (requires authentication).

### POST /api/prompts
Update prompts (requires authentication).

### GET /api/openai-credits
Get OpenAI API credit information.

### GET /api/health
Health check endpoint.

---

## Frontend Components

### Tabs
- **Content**: Main content generation interface
- **Projects Gallery**: Browse and manage projects
- **Prompts Editor**: Edit AI prompts (requires authentication)
- **API**: API documentation and setup instructions

### Modals
- **Login Modal**: Authentication
- **Edit Password Modal**: Password verification for prompt editing
- **Save Warnings Modal**: Confirmation before saving prompts

---

## Adding New Features

### Adding a New Content Type
1. Add prompt template to `backend/prompts.json`
2. Add generation method to `ContentGenerator`
3. Add display section to `frontend/index.html`
4. Add display logic to `frontend/app.js`
5. Update cache structure if needed

### Adding a New Prompt Variable
1. Add variable to prompt template in `prompts.json`
2. Add variable reference in Prompts Editor
3. Update `format_prompt()` if special handling needed

---

## Important Notes for AI Agents

### Version Management
- **Current Version**: v150
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
