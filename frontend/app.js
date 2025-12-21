const API_BASE_URL = window.location.origin;

// State
let transcriptData = null;
let videoInfo = null;
let authToken = localStorage.getItem('authToken') || sessionStorage.getItem('authToken') || null;
let rememberMe = localStorage.getItem('rememberMe') === 'true';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    setupEventListeners();
    
    // Set remember me checkbox state from localStorage if available, default to checked
    const rememberMeCheckbox = document.getElementById('rememberMe');
    if (rememberMeCheckbox) {
        const savedRememberMe = localStorage.getItem('rememberMe');
        rememberMeCheckbox.checked = savedRememberMe === 'true' || savedRememberMe === null;
    }
    
    // Load credits status every 30 seconds if authenticated
    // COMMENTED OUT: Cookie status - pytube doesn't support cookies
    if (authToken) {
        setInterval(loadCredits, 30000);
        // setInterval(loadCookiesStatus, 30000);
    }
});

// Authentication
async function checkAuthStatus() {
    if (!authToken) {
        showLoginModal();
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/check`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        const data = await response.json();
        
        if (data.authenticated) {
            showMainApp();
            loadCredits();
            // COMMENTED OUT: Cookie status - pytube doesn't support cookies
            // loadCookiesStatus(); // Check cookie status when authenticated
        } else {
            authToken = null;
            localStorage.removeItem('authToken');
            localStorage.removeItem('rememberMe');
            sessionStorage.removeItem('authToken');
            rememberMe = false;
            showLoginModal();
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        showLoginModal();
    }
}

function showLoginModal() {
    document.getElementById('loginModal').style.display = 'flex';
    document.getElementById('mainContainer').style.display = 'none';
    // Set remember me checkbox - default to checked if no saved preference
    const rememberMeCheckbox = document.getElementById('rememberMe');
    if (rememberMeCheckbox) {
        const savedRememberMe = localStorage.getItem('rememberMe');
        rememberMeCheckbox.checked = savedRememberMe === 'true' || savedRememberMe === null;
    }
}

function showMainApp() {
    document.getElementById('loginModal').style.display = 'none';
    document.getElementById('mainContainer').style.display = 'block';
    // Ensure content tab is shown by default
    switchTab('content');
}

async function login() {
    const password = document.getElementById('passwordInput').value;
    const errorDiv = document.getElementById('loginError');
    const rememberMeCheckbox = document.getElementById('rememberMe');
    const currentRememberMe = rememberMeCheckbox ? rememberMeCheckbox.checked : false;
    
    if (!password) {
        errorDiv.textContent = 'Please enter a password';
        errorDiv.style.display = 'block';
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            authToken = data.token;
            rememberMe = currentRememberMe; // Update global rememberMe state
            if (rememberMe) {
                localStorage.setItem('authToken', authToken);
                localStorage.setItem('rememberMe', 'true');
            } else {
                sessionStorage.setItem('authToken', authToken);
                localStorage.removeItem('authToken'); // Ensure localStorage is clean if not remembering
                localStorage.removeItem('rememberMe');
            }
            showMainApp();
            loadCredits();
            // COMMENTED OUT: Cookie status - pytube doesn't support cookies
            // loadCookiesStatus(); // Check cookie status immediately after login
            errorDiv.style.display = 'none';
            document.getElementById('passwordInput').value = '';
        } else {
            errorDiv.textContent = 'Invalid password';
            errorDiv.style.display = 'block';
        }
    } catch (error) {
        console.error('Login error:', error);
        errorDiv.textContent = 'Login failed. Please try again.';
        errorDiv.style.display = 'block';
    }
}

async function logout() {
    if (authToken) {
        try {
            await fetch(`${API_BASE_URL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
    }
    
    authToken = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('rememberMe');
    sessionStorage.removeItem('authToken');
    rememberMe = false; // Reset rememberMe state
    showLoginModal();
}

function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
    };
}

// Event Listeners
function setupEventListeners() {
    document.getElementById('loginBtn').addEventListener('click', login);
    document.getElementById('passwordInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') login();
    });
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const tabName = e.target.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    
    // Prompts editor
    document.getElementById('savePromptsBtn').addEventListener('click', savePrompts);
    document.getElementById('resetPromptsBtn').addEventListener('click', resetPrompts);
    
    // Gallery refresh button
    const refreshGalleryBtn = document.getElementById('refreshGalleryBtn');
    if (refreshGalleryBtn) {
        refreshGalleryBtn.addEventListener('click', loadGallery);
    }
    
    // Audio file selection button
    const selectAudioBtn = document.getElementById('selectAudioBtn');
    const audioFileInput = document.getElementById('audioFile');
    const audioFileName = document.getElementById('audioFileName');
    
    if (selectAudioBtn && audioFileInput) {
        selectAudioBtn.addEventListener('click', () => {
            audioFileInput.click();
        });
        
        // Update file name display when file is selected
        audioFileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file && audioFileName) {
                audioFileName.textContent = file.name;
            } else if (audioFileName) {
                audioFileName.textContent = 'No file selected';
            }
        });
    }
    
    document.getElementById('processVideoBtn').addEventListener('click', processVideo);
    document.getElementById('generateContentBtn').addEventListener('click', generateContent);
    
    // Copy buttons
    document.querySelectorAll('.btn-copy').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const targetId = e.target.getAttribute('data-target');
            copyToClipboard(targetId);
        });
    });
    
    // Password visibility toggle
    const passwordInput = document.getElementById('passwordInput');
    const passwordToggle = document.getElementById('passwordToggle');
    if (passwordInput && passwordToggle) {
        passwordToggle.addEventListener('click', () => {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            
            // Toggle SVG icons
            const eyeOpen = passwordToggle.querySelector('.eye-open');
            const eyeClosed = passwordToggle.querySelector('.eye-closed');
            if (eyeOpen && eyeClosed) {
                if (isPassword) {
                    eyeOpen.style.display = 'none';
                    eyeClosed.style.display = 'block';
                } else {
                    eyeOpen.style.display = 'block';
                    eyeClosed.style.display = 'none';
                }
            }
        });
    }
    
    // COMMENTED OUT: Cookie file upload - pytube doesn't support cookies
    // const uploadCookiesBtn = document.getElementById('uploadCookiesBtn');
    // const cookieFileInput = document.getElementById('cookieFileInput');
    // if (uploadCookiesBtn && cookieFileInput) {
    //     // When upload button is clicked, trigger file input
    //     uploadCookiesBtn.addEventListener('click', () => {
    //         cookieFileInput.click();
    //     });
    //     
    //     // When file is selected, upload it
    //     cookieFileInput.addEventListener('change', (e) => {
    //         const file = e.target.files[0];
    //         if (file) {
    //             uploadCookiesFile(file);
    //         }
    //     });
    // }
}

// API Calls
async function loadCredits() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/openai-credits`);
        const data = await response.json();
        
        const creditsDisplay = document.getElementById('creditsValue');
        if (!creditsDisplay) return; // Early return if element doesn't exist
        
        if (data.success) {
            if (data.status === 'operational') {
                creditsDisplay.textContent = 'Active';
                creditsDisplay.style.color = '#4CAF50';
                creditsDisplay.title = data.credits_note || data.note || 'Check OpenAI dashboard for remaining credits/balance';
            } else {
                creditsDisplay.textContent = 'Active';
                creditsDisplay.style.color = '#4CAF50';
                creditsDisplay.title = data.note || 'Check OpenAI dashboard for usage details';
            }
        } else {
            if (data.status === 'no_credits') {
                creditsDisplay.textContent = 'Inactive';
                creditsDisplay.style.color = '#f44336';
                creditsDisplay.title = 'Please add credits to your OpenAI account';
            } else {
                creditsDisplay.textContent = 'Inactive';
                creditsDisplay.style.color = '#f44336';
                creditsDisplay.title = data.error || 'Error loading status';
            }
        }
    } catch (error) {
        console.error('Error loading credits:', error);
        const creditsDisplay = document.getElementById('creditsValue');
        if (creditsDisplay) {
            creditsDisplay.textContent = 'Inactive';
            creditsDisplay.style.color = '#f44336';
        }
    }
}

// COMMENTED OUT: Cookie Management - pytube doesn't support cookies
// async function loadCookiesStatus() {
//     try {
//         const response = await fetch(`${API_BASE_URL}/api/cookies-status`);
//         const data = await response.json();
//         
//         const cookiesValue = document.getElementById('cookiesValue');
//         const cookiesDot = document.getElementById('cookiesDot');
//         const uploadBtn = document.getElementById('uploadCookiesBtn');
//         
//         if (!cookiesValue) return;
//         
//         if (cookiesDot) {
//             cookiesDot.className = 'status-dot';
//         }
//         
//         switch (data.status) {
//             case 'active':
//                 cookiesValue.textContent = 'Active';
//                 cookiesValue.style.color = '#4CAF50';
//                 cookiesValue.title = data.message || 'Cookies file is configured';
//                 if (cookiesDot) cookiesDot.classList.add('active');
//                 if (uploadBtn) uploadBtn.style.display = 'none'; // Hide upload button when active
//                 break;
//             case 'warning':
//                 cookiesValue.textContent = `Warning (${data.age_days}d)`;
//                 cookiesValue.style.color = '#FFA500';
//                 cookiesValue.title = data.message || 'Cookies file may be expired';
//                 if (cookiesDot) cookiesDot.classList.add('warning');
//                 if (uploadBtn) uploadBtn.style.display = 'inline-block'; // Show upload button
//                 break;
//             case 'missing':
//                 cookiesValue.textContent = 'Missing';
//                 cookiesValue.style.color = '#9E9E9E';
//                 cookiesValue.title = data.message || 'No cookies file found';
//                 if (uploadBtn) uploadBtn.style.display = 'inline-block'; // Show upload button
//                 break;
//             case 'error':
//                 cookiesValue.textContent = 'Error';
//                 cookiesValue.style.color = '#f44336';
//                 cookiesValue.title = data.message || 'Error with cookies file';
//                 if (cookiesDot) cookiesDot.classList.add('error');
//                 if (uploadBtn) uploadBtn.style.display = 'inline-block'; // Show upload button
//                 break;
//             default:
//                 cookiesValue.textContent = 'Unknown';
//                 cookiesValue.style.color = '#9E9E9E';
//                 cookiesValue.title = 'Unknown status';
//                 if (uploadBtn) uploadBtn.style.display = 'inline-block';
//         }
//     } catch (error) {
//         console.error('Error loading cookies status:', error);
//         const cookiesValue = document.getElementById('cookiesValue');
//         const cookiesDot = document.getElementById('cookiesDot');
//         const uploadBtn = document.getElementById('uploadCookiesBtn');
//         if (cookiesValue) {
//             cookiesValue.textContent = 'Error';
//             cookiesValue.style.color = '#f44336';
//         }
//         if (cookiesDot) {
//             cookiesDot.className = 'status-dot error';
//         }
//         if (uploadBtn) uploadBtn.style.display = 'inline-block';
//     }
// }
// 
// async function uploadCookiesFile(file) {
//     const uploadBtn = document.getElementById('uploadCookiesBtn');
//     const cookieFileInput = document.getElementById('cookieFileInput');
//     
//     if (!file) {
//         console.error('No file selected');
//         return;
//     }
//     
//     // Validate file type
//     if (!file.name.endsWith('.txt')) {
//         alert('Please upload a .txt file');
//         return;
//     }
//     
//     // Disable button during upload
//     if (uploadBtn) {
//         uploadBtn.disabled = true;
//         uploadBtn.textContent = 'Uploading...';
//     }
//     
//     try {
//         const formData = new FormData();
//         formData.append('file', file);
//         
//         const response = await fetch(`${API_BASE_URL}/api/upload-cookies`, {
//             method: 'POST',
//             headers: {
//                 'Authorization': `Bearer ${authToken}`
//             },
//             body: formData
//         });
//         
//         if (response.status === 401) {
//             authToken = null;
//             localStorage.removeItem('authToken');
//             localStorage.removeItem('rememberMe');
//             sessionStorage.removeItem('authToken');
//             rememberMe = false;
//             showLoginModal();
//             return;
//         }
//         
//         if (!response.ok) {
//             const error = await response.json();
//             throw new Error(error.detail || 'Failed to upload cookies file');
//         }
//         
//         const data = await response.json();
//         
//         if (data.success) {
//             // Reload cookie status to reflect the new upload
//             await loadCookiesStatus();
//             alert('Cookies file uploaded successfully!');
//         } else {
//             throw new Error(data.message || 'Upload failed');
//         }
//     } catch (error) {
//         console.error('Error uploading cookies file:', error);
//         alert(`Failed to upload cookies file: ${error.message}`);
//     } finally {
//         // Re-enable button
//         if (uploadBtn) {
//             uploadBtn.disabled = false;
//             uploadBtn.textContent = 'Upload Cookies';
//         }
//         // Reset file input
//         if (cookieFileInput) {
//             cookieFileInput.value = '';
//         }
//     }
// }

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
            headers: getAuthHeaders(),
            body: JSON.stringify({ youtube_url: youtubeUrl })
        });
        
        if (response.status === 401) {
            authToken = null;
            localStorage.removeItem('authToken');
            localStorage.removeItem('rememberMe');
            sessionStorage.removeItem('authToken');
            rememberMe = false;
            showLoginModal();
            return;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to process video');
        }
        
        const data = await response.json();
        
        if (data.success) {
            transcriptData = data;
            videoInfo = {
                title: data.video_title,
                duration: data.video_duration,
                video_id: data.video_id
            };
            
            // Cache the processed data (cache key based on file hash only)
            // Ensure cacheKey is set - use file hash or fallback to video_id
            if (!cacheKey && data.video_id) {
                // Fallback: use video_id if hash generation failed
                cacheKey = `processed_${data.video_id}`;
            }
            
            if (cacheKey) {
                try {
                    const cacheData = {
                        transcriptData: data,
                        videoInfo: videoInfo,
                        timestamp: Date.now()
                    };
                    localStorage.setItem(cacheKey, JSON.stringify(cacheData));
                    console.log(`Cached processed data with key: ${cacheKey}`);
                } catch (e) {
                    console.error('Error caching data:', e);
                }
            } else {
                console.warn('Warning: Could not cache processed data - no cache key available');
            }
            
            // Show download button if video_id is available
            if (data.video_id) {
                const downloadContainer = document.getElementById('audioDownloadContainer');
                const downloadBtn = document.getElementById('downloadAudioBtn');
                downloadContainer.style.display = 'block';
                downloadBtn.href = `${API_BASE_URL}/api/download-audio/${data.video_id}`;
                
                // Add auth header for download (using fetch to handle auth)
                downloadBtn.onclick = async (e) => {
                    e.preventDefault();
                    await downloadAudioFile(data.video_id);
                };
            }
            
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
            headers: getAuthHeaders(),
            body: JSON.stringify(requestBody)
        });
        
        if (response.status === 401) {
            authToken = null;
            localStorage.removeItem('authToken');
            localStorage.removeItem('rememberMe');
            sessionStorage.removeItem('authToken');
            rememberMe = false;
            showLoginModal();
            return;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate content');
        }
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
        // Cache generated content to localStorage
        if (videoInfo && videoInfo.video_id) {
            try {
                const contentKey = `content_${videoInfo.video_id}`;
                const contentData = {
                    data: data,
                    video_id: videoInfo.video_id,
                    timestamp: Date.now()
                };
                localStorage.setItem(contentKey, JSON.stringify(contentData));
                console.log(`Cached generated content with key: ${contentKey}`);
            } catch (e) {
                console.error('Error caching generated content:', e);
            }
        } else {
            console.warn('Warning: Could not cache generated content - no video_id available');
        }
        
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
    // Transcript with Timecodes
    if (transcriptData && transcriptData.transcript_with_timecodes) {
        const transcriptElement = document.getElementById('transcript');
        transcriptElement.textContent = formatTranscriptWithTimecodes(transcriptData.transcript_with_timecodes);
    } else if (transcriptData && transcriptData.transcript) {
        // Fallback to plain transcript if timecodes not available
        const transcriptElement = document.getElementById('transcript');
        transcriptElement.textContent = transcriptData.transcript;
    }
    
    // LinkedIn Post (with markdown rendering for links)
    if (data.linkedin_post) {
        const linkedinPostElement = document.getElementById('linkedinPost');
        linkedinPostElement.innerHTML = formatMarkdownLinks(data.linkedin_post);
    }
    
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
    
    // Keywords
    document.getElementById('keywords').textContent = data.keywords || '';
    
    // Hashtags
    document.getElementById('hashtags').textContent = data.hashtags || '';
}

function formatTranscriptWithTimecodes(timecodes) {
    if (!Array.isArray(timecodes) || timecodes.length === 0) {
        return '';
    }
    
    return timecodes.map((item, index) => {
        const timestamp = item.start !== undefined ? formatTimestamp(item.start) : '';
        const text = item.text || '';
        return `${timestamp} ${text}`.trim();
    }).join('\n');
}

function formatTimestamp(seconds) {
    if (typeof seconds !== 'number' || isNaN(seconds)) {
        return '';
    }
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `[${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}]`;
    }
    return `[${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}]`;
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
    // Select the specific copy button for the targetId (not download button)
    const copyBtn = document.querySelector(`[data-action="copy"][data-target="${targetId}"]`);
    
    if (!element) {
        alert('Nothing to copy');
        return;
    }
    
    let textToCopy = '';
    
    if (element) {
        // If it's HTML content (blog post, LinkedIn post), get text content
        textToCopy = element.textContent || element.innerText || '';
    }
    
    if (!textToCopy.trim()) {
        alert('Nothing to copy');
        return;
    }
    
    navigator.clipboard.writeText(textToCopy).then(() => {
        // Visual feedback - only if copy button was found
        if (copyBtn) {
            const originalSVG = copyBtn.innerHTML;
            copyBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
            copyBtn.style.color = '#4CAF50'; // Green color for success
            copyBtn.classList.add('copied');
            
            setTimeout(() => {
                copyBtn.innerHTML = originalSVG;
                copyBtn.style.color = '';
                copyBtn.classList.remove('copied');
            }, 2000);
        }
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

// Tab Management
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    const tabContent = document.getElementById(`${tabName}Tab`);
    if (tabContent) {
        tabContent.style.display = 'block';
    }
    
    // Add active class to selected tab button
    const tabBtn = document.querySelector(`[data-tab="${tabName}"]`);
    if (tabBtn) {
        tabBtn.classList.add('active');
    }
    
    // Load prompts if switching to prompts tab
    if (tabName === 'prompts') {
        loadPrompts();
    }
    
    // Load gallery if switching to gallery tab
    if (tabName === 'gallery') {
        loadGallery();
    }
}

// Gallery Functions
function loadGallery() {
    const galleryContainer = document.getElementById('galleryContainer');
    const galleryEmpty = document.getElementById('galleryEmpty');
    
    if (!galleryContainer) return;
    
    // Scan localStorage for projects
    const projects = [];
    
    // Get all localStorage keys
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        
        // Skip auth-related keys
        if (key === 'authToken' || key === 'rememberMe') continue;
        
        // Check for processed data (transcript + video info)
        if (key.startsWith('processed_')) {
            try {
                const data = JSON.parse(localStorage.getItem(key));
                if (data && data.transcriptData) {
                    const projectId = key.replace('processed_', '');
                    const videoInfo = data.videoInfo || {};
                    const contentKey = `content_${videoInfo.video_id || projectId}`;
                    let generatedContent = null;
                    
                    // Check if there's generated content
                    const contentData = localStorage.getItem(contentKey);
                    if (contentData) {
                        try {
                            generatedContent = JSON.parse(contentData);
                        } catch (e) {
                            console.error('Error parsing content data:', e);
                        }
                    }
                    
                    projects.push({
                        id: projectId,
                        key: key,
                        videoInfo: videoInfo,
                        transcriptData: data.transcriptData,
                        timestamp: data.timestamp || Date.now(),
                        hasContent: !!generatedContent,
                        contentKey: contentKey
                    });
                }
            } catch (e) {
                console.error(`Error parsing project ${key}:`, e);
            }
        }
    }
    
    // Sort by timestamp (newest first)
    projects.sort((a, b) => b.timestamp - a.timestamp);
    
    // Clear gallery
    galleryContainer.innerHTML = '';
    
    if (projects.length === 0) {
        if (galleryEmpty) {
            galleryEmpty.style.display = 'block';
        }
        return;
    }
    
    if (galleryEmpty) {
        galleryEmpty.style.display = 'none';
    }
    
    // Create project cards
    projects.forEach(project => {
        const card = createProjectCard(project);
        galleryContainer.appendChild(card);
    });
}

function createProjectCard(project) {
    const card = document.createElement('div');
    card.className = 'gallery-card';
    
    const date = new Date(project.timestamp);
    const dateStr = date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const title = project.videoInfo?.title || 'Untitled Project';
    const duration = project.videoInfo?.duration || 0;
    const durationStr = formatDuration(duration);
    
    card.innerHTML = `
        <div class="gallery-card-header">
            <h3 class="gallery-card-title">${escapeHtml(title)}</h3>
            <span class="gallery-card-date">${dateStr}</span>
        </div>
        <div class="gallery-card-body">
            <div class="gallery-card-info">
                <span class="gallery-card-info-item">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <polyline points="12 6 12 12 16 14"></polyline>
                    </svg>
                    ${durationStr}
                </span>
                <span class="gallery-card-info-item ${project.hasContent ? 'has-content' : ''}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    ${project.hasContent ? 'Content Generated' : 'Transcript Only'}
                </span>
            </div>
            <div class="gallery-card-actions">
                <button class="btn btn-primary btn-sm" onclick="openProject('${project.id}')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
                        <path d="M5 12h14M12 5l7 7-7 7"></path>
                    </svg>
                    Open Project
                </button>
                <button class="btn btn-secondary btn-sm" onclick="deleteProject('${project.id}', '${project.key}')">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                    Delete
                </button>
            </div>
        </div>
    `;
    
    return card;
}

function openProject(projectId) {
    // Find the project in localStorage
    const cacheKey = `processed_${projectId}`;
    const cachedData = localStorage.getItem(cacheKey);
    
    if (!cachedData) {
        alert('Project not found in local storage.');
        return;
    }
    
    try {
        const parsed = JSON.parse(cachedData);
        transcriptData = parsed.transcriptData;
        videoInfo = parsed.videoInfo;
        
        // Check for generated content
        if (videoInfo && videoInfo.video_id) {
            const contentKey = `content_${videoInfo.video_id}`;
            const contentData = localStorage.getItem(contentKey);
            if (contentData) {
                try {
                    const content = JSON.parse(contentData);
                    displayResults(content.data);
                    document.getElementById('resultsContainer').style.display = 'block';
                } catch (e) {
                    console.error('Error parsing content:', e);
                }
            }
        }
        
        // Switch to content tab
        switchTab('content');
        
        // Show step 2 (guest info) if transcript is loaded
        if (transcriptData) {
            document.getElementById('step2Card').style.display = 'block';
            document.getElementById('step1Card').scrollIntoView({ behavior: 'smooth' });
        }
        
        // Show success message
        const statusDiv = document.getElementById('processingStatus');
        if (statusDiv) {
            showStatus(statusDiv, 'Project loaded successfully!', 'success');
        }
    } catch (e) {
        console.error('Error loading project:', e);
        alert('Error loading project: ' + e.message);
    }
}

function deleteProject(projectId, cacheKey) {
    if (!confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
        return;
    }
    
    try {
        // Delete processed data
        localStorage.removeItem(cacheKey);
        
        // Delete audio file if exists
        localStorage.removeItem(`audio_${projectId}`);
        
        // Delete generated content if exists
        const contentKey = `content_${projectId}`;
        const contentData = localStorage.getItem(contentKey);
        if (contentData) {
            try {
                const content = JSON.parse(contentData);
                if (content.data && content.data.video_id) {
                    localStorage.removeItem(`content_${content.data.video_id}`);
                }
            } catch (e) {
                // Try to delete by projectId
                localStorage.removeItem(contentKey);
            }
        }
        
        // Reload gallery
        loadGallery();
    } catch (e) {
        console.error('Error deleting project:', e);
        alert('Error deleting project: ' + e.message);
    }
}

function formatDuration(seconds) {
    if (!seconds || seconds === 0) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    }
    return `${minutes}:${String(secs).padStart(2, '0')}`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Prompts Management
async function loadPrompts() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/prompts`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.status === 401) {
            authToken = null;
            localStorage.removeItem('authToken');
            localStorage.removeItem('rememberMe');
            sessionStorage.removeItem('authToken');
            rememberMe = false;
            showLoginModal();
            return;
        }
        
        if (!response.ok) {
            throw new Error('Failed to load prompts');
        }
        
        const data = await response.json();
        if (data.success && data.prompts) {
            // Populate textareas with prompts
            document.getElementById('prompt_youtube_summary').value = data.prompts.youtube_summary || '';
            document.getElementById('prompt_blog_post').value = data.prompts.blog_post || '';
            document.getElementById('prompt_clickbait_titles').value = data.prompts.clickbait_titles || '';
            document.getElementById('prompt_two_line_summary').value = data.prompts.two_line_summary || '';
            document.getElementById('prompt_quotes').value = data.prompts.quotes || '';
            document.getElementById('prompt_chapter_timestamps').value = data.prompts.chapter_timestamps || '';
            document.getElementById('prompt_linkedin_post').value = data.prompts.linkedin_post || '';
        }
    } catch (error) {
        console.error('Error loading prompts:', error);
        showStatus(document.getElementById('promptsStatus'), 'Error loading prompts', 'error');
    }
}

async function savePrompts() {
    const statusDiv = document.getElementById('promptsStatus');
    const saveBtn = document.getElementById('savePromptsBtn');
    
    saveBtn.disabled = true;
    showStatus(statusDiv, 'Saving prompts...', 'info');
    
    try {
        const prompts = {
            youtube_summary: document.getElementById('prompt_youtube_summary').value,
            blog_post: document.getElementById('prompt_blog_post').value,
            clickbait_titles: document.getElementById('prompt_clickbait_titles').value,
            two_line_summary: document.getElementById('prompt_two_line_summary').value,
            quotes: document.getElementById('prompt_quotes').value,
            chapter_timestamps: document.getElementById('prompt_chapter_timestamps').value,
            linkedin_post: document.getElementById('prompt_linkedin_post').value
        };
        
        const response = await fetch(`${API_BASE_URL}/api/prompts`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify({ prompts })
        });
        
        if (response.status === 401) {
            authToken = null;
            localStorage.removeItem('authToken');
            localStorage.removeItem('rememberMe');
            sessionStorage.removeItem('authToken');
            rememberMe = false;
            showLoginModal();
            return;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to save prompts');
        }
        
        const data = await response.json();
        if (data.success) {
            showStatus(statusDiv, 'Prompts saved successfully!', 'success');
        }
    } catch (error) {
        console.error('Error saving prompts:', error);
        showStatus(statusDiv, error.message || 'Error saving prompts', 'error');
    } finally {
        saveBtn.disabled = false;
    }
}

async function resetPrompts() {
    if (!confirm('Are you sure you want to reset all prompts to default? This cannot be undone.')) {
        return;
    }
    
    try {
        // Reload prompts from server (which will use defaults if file doesn't exist)
        await loadPrompts();
        showStatus(document.getElementById('promptsStatus'), 'Prompts reset to defaults. Click Save to apply.', 'info');
    } catch (error) {
        console.error('Error resetting prompts:', error);
        showStatus(document.getElementById('promptsStatus'), 'Error resetting prompts', 'error');
    }
}

// Audio Download
async function downloadAudioFile(videoId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/download-audio/${videoId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.status === 401) {
            authToken = null;
            localStorage.removeItem('authToken');
            localStorage.removeItem('rememberMe');
            sessionStorage.removeItem('authToken');
            rememberMe = false;
            showLoginModal();
            return;
        }
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to download audio');
        }
        
        // Get the blob and create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from Content-Disposition header or use video_id
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = `${videoId}.mp3`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+?)"?$/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Error downloading audio:', error);
        alert(`Failed to download audio: ${error.message}`);
    }
}