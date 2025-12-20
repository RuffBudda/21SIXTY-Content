# YouTube Bot Detection Fixes Log

This document tracks fixes and improvements made to resolve YouTube bot detection errors.

## Problem
YouTube bot detection errors occur when trying to download videos:
```
ERROR: [youtube] ItMq4MttBIA: Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies for the authentication.
```

## Root Causes Identified

1. **Cookie File Not Found**: Cookie file path resolution issues
2. **Invalid/Expired Cookies**: Cookie files may be empty, invalid format, or expired
3. **Missing Cookie Validation**: No validation to ensure cookie files are properly formatted
4. **Insufficient Logging**: Difficult to diagnose why cookies aren't working

## Fixes Applied

### Fix 1: Cookie File Validation (2024-12-XX)
**Problem**: Cookie files could be empty or in invalid format, causing silent failures.

**Solution**:
- Added `_validate_cookie_file()` method to validate cookie file existence, size, and format
- Checks for Netscape cookie format indicators (header or tab-separated entries)
- Logs detailed error messages when validation fails
- Only uses cookie files that pass validation

**Code Changes**:
- `backend/services/youtube_service.py`: Added `_validate_cookie_file()` method
- `backend/services/youtube_service.py`: Modified `_get_cookies_file_path()` to call validation

**Impact**: Prevents silent failures and provides clear feedback when cookie files are invalid.

---

### Fix 2: Enhanced Logging (2024-12-XX)
**Problem**: Insufficient logging made it difficult to diagnose cookie issues.

**Solution**:
- Added detailed logging at each step of cookie file detection
- Log cookie file path, size, and validation status
- Log which cookie strategy is being used (file vs browser)
- Enhanced error messages to clearly indicate when cookies are missing/invalid
- Added visual indicators (✓, ✗, ⚠️) in logs for easier scanning

**Code Changes**:
- `backend/services/youtube_service.py`: Enhanced logging throughout `_build_ydl_opts()`
- `backend/services/youtube_service.py`: Enhanced logging in `download_audio()`

**Impact**: Easier diagnosis of cookie-related issues from server logs.

---

### Fix 3: Cookie File Path Resolution (Previously Fixed)
**Problem**: Cookie file paths might not resolve correctly in all environments.

**Solution**:
- Use absolute paths for all cookie file operations
- Ensure cookies directory is created on service initialization
- Priority order: uploaded file > env var file > browser cookies

**Code Changes**:
- `backend/services/youtube_service.py`: Uses `os.path.abspath()` for all paths
- `backend/services/youtube_service.py`: Creates cookies directory in `__init__`

**Impact**: Reliable cookie file path resolution across different deployment environments.

---

## Current Cookie Strategy

1. **Priority 1**: Uploaded cookies file (`backend/cookies/cookies.txt`)
   - User uploads via web interface
   - Validated before use
   - Highest priority

2. **Priority 2**: Environment variable (`YOUTUBE_COOKIES_FILE`)
   - Backward compatibility
   - Path specified in `.env` file
   - Validated before use

3. **Priority 3**: Browser cookies (`YOUTUBE_COOKIES_BROWSER`)
   - Extracted directly from browser
   - Requires browser name(s) in env var (e.g., `chrome,firefox`)

## User Instructions

1. **Export Cookies**:
   - Install browser extension (Chrome: "Get cookies.txt LOCALLY", Firefox: "cookies.txt")
   - Log in to YouTube in browser
   - Export cookies to `cookies.txt` file

2. **Upload Cookies**:
   - Use "Upload Cookies" button in web interface
   - File is automatically saved as `cookies.txt`
   - Status indicator shows if cookies are active/expired/missing

3. **Check Cookie Status**:
   - View "Cookies" status indicator in header
   - Green "Active" = cookies are valid and recent (< 7 days old)
   - Orange "Warning" = cookies are old (> 7 days) - may need refresh
   - Gray "Missing" = no cookies file found
   - Red "Error" = cookie file exists but is invalid/empty

## Troubleshooting

### Error: "Sign in to confirm you're not a bot"
**Possible Causes**:
1. No cookie file uploaded → Upload fresh cookies via web interface
2. Cookie file expired → Re-export and upload fresh cookies
3. Cookie file invalid format → Ensure exported in Netscape format
4. Cookie file empty → Check file size, re-export if needed

**Solution**:
1. Check cookie status indicator in web interface
2. If missing/invalid, export fresh cookies from browser
3. Upload new cookies.txt file
4. Check server logs for detailed cookie validation messages

### Error: Cookie file validation failed
**Check**:
- File exists at `backend/cookies/cookies.txt`
- File size > 0 bytes
- File contains Netscape format (tab-separated or has header)
- File permissions allow read access

**Solution**:
- Re-export cookies from browser
- Ensure browser extension exports in Netscape format
- Upload fresh file via web interface

## Testing

After each fix, test with:
1. Upload valid cookies.txt file
2. Attempt to download a YouTube video
3. Check server logs for cookie validation messages
4. Verify video downloads successfully

## Future Improvements

- [ ] Automatic cookie refresh reminder when cookies are > 7 days old
- [ ] Cookie format conversion (if browser exports in wrong format)
- [ ] Multiple cookie file support (fallback chain)
- [ ] Cookie expiration date parsing and warnings
- [ ] Integration with browser cookie sync services

