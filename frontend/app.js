const API_BASE_URL = window.location.origin;

// State
let transcriptData = null;
let videoInfo = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCredits();
    setupEventListeners();
    
    // Load credits every 30 seconds
    setInterval(loadCredits, 30000);
});

// Event Listeners
function setupEventListeners() {
    document.getElementById('processVideoBtn').addEventListener('click', processVideo);
    document.getElementById('generateContentBtn').addEventListener('click', generateContent);
    
    // Copy buttons
    document.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = e.target.getAttribute('data-target');
            copyToClipboard(targetId);
        });
    });
}

// API Calls
async function loadCredits() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/openai-credits`);
        const data = await response.json();
        
        const creditsDisplay = document.getElementById('creditsValue');
        if (data.success) {
            creditsDisplay.textContent = data.message || 'API Key Configured';
            creditsDisplay.style.color = '#4CAF50';
            creditsDisplay.title = data.note || 'Check OpenAI dashboard for usage details';
        } else {
            creditsDisplay.textContent = data.message || 'Error loading credits';
            creditsDisplay.style.color = '#f44336';
        }
    } catch (error) {
        console.error('Error loading credits:', error);
        document.getElementById('creditsValue').textContent = 'Unable to load';
        document.getElementById('creditsValue').style.color = '#f44336';
    }
}

async function processVideo() {
    const youtubeUrl = document.getElementById('youtubeUrl').value.trim();
    const statusDiv = document.getElementById('processingStatus');
    const processBtn = document.getElementById('processVideoBtn');
    
    if (!youtubeUrl) {
        showStatus(statusDiv, 'Please enter a YouTube URL', 'error');
        return;
    }
    
    // Validate YouTube URL
    if (!isValidYouTubeUrl(youtubeUrl)) {
        showStatus(statusDiv, 'Please enter a valid YouTube URL', 'error');
        return;
    }
    
    processBtn.disabled = true;
    showLoading('Downloading video and extracting transcript...');
    showStatus(statusDiv, 'Processing video...', 'info');
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/process-video`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ youtube_url: youtubeUrl })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process video');
        }
        
        const data = await response.json();
        
        if (data.success) {
            transcriptData = data;
            videoInfo = {
                title: data.video_title,
                duration: data.video_duration
            };
            
            showStatus(statusDiv, 'Video processed successfully! Please fill in guest information.', 'success');
            document.getElementById('step2Card').style.display = 'block';
            document.getElementById('step1Card').scrollIntoView({ behavior: 'smooth' });
        } else {
            throw new Error('Processing failed');
        }
    } catch (error) {
        console.error('Error processing video:', error);
        showStatus(statusDiv, `Error: ${error.message}`, 'error');
    } finally {
        processBtn.disabled = false;
        hideLoading();
    }
}

async function generateContent() {
    const guestName = document.getElementById('guestName').value.trim();
    const guestTitle = document.getElementById('guestTitle').value.trim();
    const guestCompany = document.getElementById('guestCompany').value.trim();
    const guestLinkedIn = document.getElementById('guestLinkedIn').value.trim();
    const statusDiv = document.getElementById('generatingStatus');
    const generateBtn = document.getElementById('generateContentBtn');
    
    // Validate inputs
    if (!guestName || !guestTitle || !guestCompany || !guestLinkedIn) {
        showStatus(statusDiv, 'Please fill in all guest information fields', 'error');
        return;
    }
    
    if (!transcriptData) {
        showStatus(statusDiv, 'Please process a video first', 'error');
        return;
    }
    
    // Validate LinkedIn URL
    if (!isValidUrl(guestLinkedIn)) {
        showStatus(statusDiv, 'Please enter a valid LinkedIn URL', 'error');
        return;
    }
    
    generateBtn.disabled = true;
    showLoading('Generating content with AI... This may take a few minutes.');
    showStatus(statusDiv, 'Generating content...', 'info');
    
    try {
        const requestBody = {
            transcript: transcriptData.transcript,
            transcript_with_timecodes: transcriptData.transcript_with_timecodes,
            guest_name: guestName,
            guest_title: guestTitle,
            guest_company: guestCompany,
            guest_linkedin: guestLinkedIn,
            video_title: videoInfo?.title || '',
            video_duration: videoInfo?.duration || 0
        };
        
        const response = await fetch(`${API_BASE_URL}/api/generate-content`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate content');
        }
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
        showStatus(statusDiv, 'Content generated successfully!', 'success');
        document.getElementById('resultsContainer').style.display = 'block';
        document.getElementById('resultsContainer').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
        console.error('Error generating content:', error);
        showStatus(statusDiv, `Error: ${error.message}`, 'error');
    } finally {
        generateBtn.disabled = false;
        hideLoading();
    }
}

// Display Results
function displayResults(data) {
    // YouTube Summary
    document.getElementById('youtubeSummary').textContent = data.youtube_summary;
    
    // Blog Post (with markdown rendering for links)
    const blogPostElement = document.getElementById('blogPost');
    blogPostElement.innerHTML = formatMarkdownLinks(data.blog_post);
    
    // Two Line Summary
    document.getElementById('twoLineSummary').textContent = data.two_line_summary;
    
    // Clickbait Titles
    const titlesElement = document.getElementById('clickbaitTitles');
    titlesElement.innerHTML = formatList(data.clickbait_titles);
    
    // Quotes
    const quotesElement = document.getElementById('quotes');
    quotesElement.innerHTML = formatList(data.quotes);
    
    // Chapter Timestamps
    const timestampsElement = document.getElementById('chapterTimestamps');
    timestampsElement.textContent = data.chapter_timestamps.join('\n');
}

function formatList(items) {
    return items.map((item, index) => `${index + 1}. ${item}`).join('\n');
}

function formatMarkdownLinks(text) {
    // Convert markdown links to HTML
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    return text.replace(linkRegex, '<a href="$2" target="_blank" style="color: #1E90FF; text-decoration: underline;">$1</a>');
}

// Utility Functions
function copyToClipboard(targetId) {
    const element = document.getElementById(targetId);
    const copyBtn = document.querySelector(`[data-target="${targetId}"]`);
    
    let textToCopy = '';
    
    if (element) {
        // If it's HTML content (blog post), get text content
        textToCopy = element.textContent || element.innerText || '';
    }
    
    if (!textToCopy.trim()) {
        alert('Nothing to copy');
        return;
    }
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        // Visual feedback
        const originalText = copyBtn.textContent;
        copyBtn.textContent = 'Copied!';
        copyBtn.classList.add('copied');
        
        setTimeout(() => {
            copyBtn.textContent = originalText;
            copyBtn.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
}

function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
}

function showLoading(text = 'Processing...') {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingOverlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loadingOverlay').style.display = 'none';
}

function isValidYouTubeUrl(url) {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    return youtubeRegex.test(url);
}

function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

