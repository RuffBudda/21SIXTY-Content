# YouTube Cookies Setup Guide

YouTube requires authentication cookies to download videos due to bot detection. This guide explains how to set up cookies for the 21SIXTY CONTENT GEN application.

## Why Cookies Are Needed

YouTube has implemented bot detection that requires authentication. Without cookies, you'll see errors like:
```
ERROR: [youtube] Sign in to confirm you're not a bot. Use --cookies-from-browser or --cookies for the authentication.
```

## Method 1: Export Cookies from Browser (Recommended)

### Step 1: Install Browser Extension

Install a cookie export extension in your browser:

**For Chrome/Edge:**
- Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) extension

**For Firefox:**
- Install [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/) extension

### Step 2: Export Cookies

1. **Log in to YouTube** in your browser (make sure you're logged in)
2. Navigate to any YouTube video page
3. Click the extension icon
4. Click "Export" to download `cookies.txt`
5. Save the file to your server (e.g., `/path/to/cookies.txt`)

### Step 3: Set Environment Variable

On your server, set the environment variable:

```bash
export YOUTUBE_COOKIES_FILE=/path/to/cookies.txt
```

Or add it to your `.env` file:
```
YOUTUBE_COOKIES_FILE=/path/to/cookies.txt
```

### Step 4: Restart the Application

Restart your application service:
```bash
sudo systemctl restart content-generator
```

## Method 2: Use Browser Cookies Automatically (Local Development Only)

If you're running the application locally and have Chrome installed, you can set:

```bash
export YOUTUBE_COOKIES_BROWSER=chrome
```

Or in `.env`:
```
YOUTUBE_COOKIES_BROWSER=chrome
```

**Note:** This only works if:
- You're running on a machine with Chrome installed
- Chrome has YouTube cookies (you're logged in)
- This won't work on most servers

## Method 3: Using yt-dlp Command Line

You can also test cookie export using yt-dlp directly:

```bash
# Export cookies from Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt https://www.youtube.com/watch?v=VIDEO_ID

# Or use the exported cookies file
yt-dlp --cookies cookies.txt https://www.youtube.com/watch?v=VIDEO_ID
```

## Troubleshooting

### Cookies File Not Found
- Make sure the path in `YOUTUBE_COOKIES_FILE` is absolute and correct
- Check file permissions: `chmod 644 /path/to/cookies.txt`

### Cookies Expired
- YouTube cookies expire after some time
- Re-export cookies if you get authentication errors
- Consider setting up a cron job to refresh cookies periodically

### Still Getting Bot Detection Errors
1. Make sure you're logged into YouTube when exporting cookies
2. Try exporting cookies again (they may have expired)
3. Check that the cookies file is in Netscape format (most extensions export in this format)
4. Verify the file path is correct in your environment variable

## Security Note

**Important:** The cookies file contains your YouTube session credentials. Keep it secure:
- Don't commit it to version control
- Set appropriate file permissions (readable only by the application user)
- Store it in a secure location on your server
- Add `cookies.txt` to your `.gitignore` file

## Automatic Fallback

The application will automatically:
1. Try to use cookies if configured
2. Fall back to downloading without cookies if cookie-based download fails
3. Log which method was used

However, many YouTube videos now require cookies, so setting them up is strongly recommended.

