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

function getAuthHeaders(includeContentType = true) {
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/b207b689-8405-4a20-bd10-ddb3167454cd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:154',message:'getAuthHeaders called',data:{includeContentType,authToken:authToken?'present':'missing'},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
    // #endregion
    const headers = {
        'Authorization': `Bearer ${authToken}`
    };
    // Only include Content-Type for JSON requests, not for FormData (file uploads)
    if (includeContentType) {
        headers['Content-Type'] = 'application/json';
    }
    // #region agent log
    fetch('http://127.0.0.1:7243/ingest/b207b689-8405-4a20-bd10-ddb3167454cd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:162',message:'getAuthHeaders returning',data:{headers,hasContentType:!!headers['Content-Type']},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
    // #endregion
    return headers;
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
            // Use currentTarget instead of target to handle clicks on child elements (e.g., SVG icons)
            const tabName = e.currentTarget.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
    
    // Prompts editor
    document.getElementById('savePromptsBtn').addEventListener('click', savePrompts);
    document.getElementById('resetPromptsBtn').addEventListener('click', resetPrompts);
    
    // Variable copy buttons
    document.querySelectorAll('.variable-copy-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const variableItem = btn.closest('.variable-item');
            const variable = variableItem.getAttribute('data-variable');
            copyVariable(variable, btn);
        });
    });
    
    // Also allow clicking the variable item itself to copy
    document.querySelectorAll('.variable-item').forEach(item => {
        item.addEventListener('click', (e) => {
            // Only copy if not clicking the copy button
            if (!e.target.closest('.variable-copy-btn')) {
                const variable = item.getAttribute('data-variable');
                const copyBtn = item.querySelector('.variable-copy-btn');
                copyVariable(variable, copyBtn);
            }
        });
    });
    
    // Prompt tile expand/collapse buttons
    document.querySelectorAll('.btn-expand').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const targetId = btn.getAttribute('data-target');
            togglePromptExpand(targetId, btn);
        });
    });
    
    // Prompt tile edit buttons
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const targetId = btn.getAttribute('data-target');
            showEditPasswordModal(targetId);
        });
    });
    
    // Edit password modal submit
    const confirmEditBtn = document.getElementById('confirmEditBtn');
    if (confirmEditBtn) {
        confirmEditBtn.addEventListener('click', verifyEditPassword);
    }
    
    // Edit password modal cancel
    const cancelEditBtn = document.getElementById('cancelEditBtn');
    if (cancelEditBtn) {
        cancelEditBtn.addEventListener('click', () => {
            document.getElementById('editPasswordModal').style.display = 'none';
            document.getElementById('editPasswordInput').value = '';
        });
    }
    
    // Save warnings modal confirm
    const confirmSaveBtn = document.getElementById('confirmSaveBtn');
    if (confirmSaveBtn) {
        confirmSaveBtn.addEventListener('click', () => {
            document.getElementById('saveWarningsModal').style.display = 'none';
            // Proceed with actual save
            performSavePrompts();
        });
    }
    
    // Save warnings modal cancel
    const cancelSaveBtn = document.getElementById('cancelSaveBtn');
    if (cancelSaveBtn) {
        cancelSaveBtn.addEventListener('click', () => {
            document.getElementById('saveWarningsModal').style.display = 'none';
        });
    }
    
    // Allow Enter key in edit password input
    const editPasswordInput = document.getElementById('editPasswordInput');
    if (editPasswordInput) {
        editPasswordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                verifyEditPassword();
            }
        });
    }
    
    // Gallery refresh button
    const refreshGalleryBtn = document.getElementById('refreshGalleryBtn');
    if (refreshGalleryBtn) {
        refreshGalleryBtn.addEventListener('click', loadGallery);
    }
    
    // API tile click handler - use event delegation to ensure it works even if element is created later
    document.addEventListener('click', (e) => {
        const apiTile = e.target.closest('#apiTile');
        if (apiTile) {
            showApiDetails();
        }
    });
    
    // Hide API details button
    const hideApiDetailsBtn = document.getElementById('hideApiDetailsBtn');
    if (hideApiDetailsBtn) {
        hideApiDetailsBtn.addEventListener('click', () => {
            hideApiDetails();
        });
    }
    
    // Copy webhook URL button
    const copyWebhookUrlBtn = document.getElementById('copyWebhookUrlBtn');
    if (copyWebhookUrlBtn) {
        copyWebhookUrlBtn.addEventListener('click', () => {
            copyWebhookUrl();
        });
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
    document.getElementById('generateContentBtn').addEventListener('click', () => generateContent(false));
    const regenerateBtn = document.getElementById('regenerateContentBtn');
    if (regenerateBtn) {
        regenerateBtn.addEventListener('click', () => generateContent(true));
    }
    
    // Event delegation for result action buttons (copy and download)
    document.addEventListener('click', (e) => {
        const button = e.target.closest('[data-action]');
        if (!button) return;
        
        const action = button.getAttribute('data-action');
        const targetId = button.getAttribute('data-target');
        
        if (!targetId) return;
        
        if (action === 'copy') {
            copyToClipboard(targetId);
        } else if (action === 'download') {
            downloadAsTxt(targetId);
        } else if (action === 'regenerate') {
            const contentType = button.getAttribute('data-type');
            if (contentType) {
                regenerateContent(contentType, targetId);
            }
        }
    });
    
    // Legacy copy buttons (for backward compatibility)
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

// Utility function to generate SHA-256 hash
async function getFileHash(file) {
    const arrayBuffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Utility function to convert file to base64
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

async function processVideo() {
    const audioFileInput = document.getElementById('audioFile');
    const statusDiv = document.getElementById('processingStatus');
    const processBtn = document.getElementById('processVideoBtn');
    
    if (!audioFileInput) {
        console.error('Audio file input not found');
        return;
    }
    
    const audioFile = audioFileInput.files[0];
    
    if (!audioFile) {
        if (statusDiv) {
            showStatus(statusDiv, 'Please select an audio file', 'error');
        }
        return;
    }
    
    // Validate file type
    const validExtensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac'];
    const fileExtension = '.' + audioFile.name.split('.').pop().toLowerCase();
    if (!validExtensions.includes(fileExtension)) {
        if (statusDiv) {
            showStatus(statusDiv, 'Invalid file format. Supported formats: MP3, WAV, M4A, OGG, FLAC', 'error');
        }
        return;
    }
    
    if (!processBtn) {
        console.error('Process button not found');
        return;
    }
    
    // Disable all buttons and show spinner with blackout
    processBtn.disabled = true;
    const selectAudioBtn = document.getElementById('selectAudioBtn');
    if (selectAudioBtn) selectAudioBtn.disabled = true;
    
    // Show loading overlay (spinner + blackout background)
    showLoading('Processing audio and generating transcript with Whisper API...');
    
    // Generate file hash for caching
    let fileHash = null;
    let cacheKey = null;
    
    try {
        fileHash = await getFileHash(audioFile);
        cacheKey = `processed_${fileHash}`;
        
        // Check cache
        try {
            const cachedData = localStorage.getItem(cacheKey);
            if (cachedData) {
                try {
                    const parsed = JSON.parse(cachedData);
                    transcriptData = parsed.transcriptData;
                    videoInfo = parsed.videoInfo;
                    
                    // Hide spinner and re-enable buttons
                    hideLoading();
                    showStatus(statusDiv, 'Using cached data!', 'success');
                    const step2Card = document.getElementById('step2Card');
                    if (step2Card) {
                        step2Card.style.display = 'block';
                    }
                    processBtn.disabled = false;
                    const selectAudioBtn = document.getElementById('selectAudioBtn');
                    if (selectAudioBtn) selectAudioBtn.disabled = false;
                    return;
                } catch (e) {
                    console.error('Error parsing cached data:', e);
                }
            }
        } catch (e) {
            console.warn('Error accessing localStorage for cache check:', e);
            // Continue without cache if localStorage fails
        }
        
        // Try to cache audio file as base64 (optional, skip if quota exceeded)
        try {
            const audioBase64 = await fileToBase64(audioFile);
            localStorage.setItem(`audio_${fileHash}`, audioBase64);
        } catch (e) {
            if (e.name === 'QuotaExceededError' || e.message.includes('quota')) {
                // Silently clear old cache without warning
                try {
                    clearOldCache();
                    // Try again after clearing
                    try {
                        const audioBase64 = await fileToBase64(audioFile);
                        localStorage.setItem(`audio_${fileHash}`, audioBase64);
                    } catch (retryError) {
                        // Skip audio caching if still fails after clearing
                        console.debug('Skipping audio file cache after quota exceeded');
                    }
                } catch (clearError) {
                    console.debug('Error clearing old cache:', clearError);
                }
            } else {
                console.debug('Error caching audio file:', e);
            }
        }
        
    } catch (e) {
        console.error('Error generating file hash:', e);
        // Continue processing even if hash generation fails
    }
    
    if (statusDiv) {
        showStatus(statusDiv, 'Processing audio file...', 'info');
    }
    
    try {
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/b207b689-8405-4a20-bd10-ddb3167454cd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:645',message:'Before FormData creation',data:{audioFileExists:!!audioFile,audioFileName:audioFile?.name,audioFileSize:audioFile?.size,audioFileType:audioFile?.type},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        const formData = new FormData();
        formData.append('audio_file', audioFile);
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/b207b689-8405-4a20-bd10-ddb3167454cd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:648',message:'After FormData.append',data:{formDataHasAudioFile:formData.has('audio_file'),audioFileStillExists:!!audioFile},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        
        const headers = getAuthHeaders(false); // Don't set Content-Type for FormData - browser sets it automatically
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/b207b689-8405-4a20-bd10-ddb3167454cd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:653',message:'Before fetch request',data:{headers,hasContentType:!!headers['Content-Type'],url:`${API_BASE_URL}/api/process-video`},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B,C'})}).catch(()=>{});
        // #endregion
        let response;
        try {
            response = await fetch(`${API_BASE_URL}/api/process-video`, {
                method: 'POST',
                headers: headers,
                body: formData
            });
        } catch (fetchError) {
            // #region agent log
            fetch('http://127.0.0.1:7243/ingest/b207b689-8405-4a20-bd10-ddb3167454cd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:656',message:'Fetch error caught',data:{error:fetchError?.message,errorType:fetchError?.constructor?.name},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
            // #endregion
            // Handle network errors (no response received)
            const networkErrorMsg = fetchError instanceof Error 
                ? fetchError.message 
                : String(fetchError);
            throw new Error(`Network error: ${networkErrorMsg || 'Failed to connect to server'}`);
        }
        // #region agent log
        fetch('http://127.0.0.1:7243/ingest/b207b689-8405-4a20-bd10-ddb3167454cd',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:664',message:'Response received',data:{status:response.status,statusText:response.statusText,contentType:response.headers.get('content-type')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
        // #endregion
        
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
            let errorMessage = 'Failed to process audio file';
            try {
                const errorData = await response.json();
                // Handle FastAPI error format: {detail: "message"} or {message: "message"}
                if (typeof errorData === 'object' && errorData !== null) {
                    // Extract error message, ensuring nested objects are handled
                    const detail = errorData.detail;
                    const message = errorData.message;
                    
                    if (typeof detail === 'string' && detail) {
                        errorMessage = detail;
                    } else if (typeof message === 'string' && message) {
                        errorMessage = message;
                    } else if (detail || message) {
                        // If detail/message exist but are not strings, stringify them
                        errorMessage = JSON.stringify(detail || message);
                    } else {
                        // Fallback: stringify the entire error object
                        errorMessage = JSON.stringify(errorData);
                    }
                } else if (typeof errorData === 'string') {
                    errorMessage = errorData;
                } else {
                    // For any other type, convert to string
                    errorMessage = String(errorData);
                }
            } catch (e) {
                // If response is not JSON, try to get text
                try {
                    const errorText = await response.text();
                    if (errorText) {
                        errorMessage = errorText;
                    } else {
                        errorMessage = `Server error: ${response.status} ${response.statusText}`;
                    }
                } catch (textError) {
                    errorMessage = `Server error: ${response.status} ${response.statusText}`;
                }
            }
            
            // CRITICAL: Ensure errorMessage is always a string before throwing
            if (typeof errorMessage !== 'string') {
                try {
                    errorMessage = JSON.stringify(errorMessage);
                } catch (stringifyError) {
                    errorMessage = String(errorMessage);
                }
            }
            
            // Additional safeguard: if still not a string or is "[object Object]", use fallback
            if (!errorMessage || errorMessage === '[object Object]' || errorMessage.includes('[object')) {
                errorMessage = `Server error: ${response.status} ${response.statusText || 'Unknown error'}`;
            }
            
            throw new Error(errorMessage);
        }
        
        let data;
        try {
            data = await response.json();
        } catch (e) {
            throw new Error('Invalid response from server. Please try again.');
        }
        
        if (data.success) {
            transcriptData = data;
            videoInfo = {
                title: data.video_title,
                duration: data.video_duration,
                video_id: data.video_id
            };
            
            // Cache the processed data
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
                    console.error('Error caching processed data:', e);
                }
            }
            
            // Display transcript immediately after processing
            if (transcriptData) {
                displayTranscript();
            }
            
            // Hide spinner and re-enable buttons
            hideLoading();
            processBtn.disabled = false;
            const selectAudioBtn = document.getElementById('selectAudioBtn');
            if (selectAudioBtn) selectAudioBtn.disabled = false;
            
            if (statusDiv) {
                showStatus(statusDiv, 'Audio processed successfully! Please fill in guest information.', 'success');
            }
            const step2Card = document.getElementById('step2Card');
            if (step2Card) {
                step2Card.style.display = 'block';
            }
            const step1Card = document.getElementById('step1Card');
            if (step1Card) {
                step1Card.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            throw new Error('Processing failed');
        }
    } catch (error) {
        console.error('Error processing audio file:', error);
        
        // Hide spinner and re-enable buttons
        hideLoading();
        processBtn.disabled = false;
        const selectAudioBtn = document.getElementById('selectAudioBtn');
        if (selectAudioBtn) selectAudioBtn.disabled = false;
        
        if (statusDiv) {
            // Properly extract error message from various error formats
            let errorMsg = 'Unknown error occurred';
            if (error instanceof Error) {
                errorMsg = error.message || String(error);
            } else if (typeof error === 'string') {
                errorMsg = error;
            } else if (error && typeof error === 'object') {
                errorMsg = error.message || error.detail || error.error || JSON.stringify(error);
            } else {
                errorMsg = String(error);
            }
            // Ensure error message is not "[object Object]"
            if (errorMsg === '[object Object]' || errorMsg.includes('[object')) {
                errorMsg = 'An error occurred while processing the audio file. Please check the console for details.';
            }
            showStatus(statusDiv, `Error: ${errorMsg}`, 'error');
        }
    }
}

async function generateContent(forceRegenerate = false, regenerateType = null) {
    const guestName = document.getElementById('guestName').value.trim();
    const guestTitle = document.getElementById('guestTitle').value.trim();
    const guestCompany = document.getElementById('guestCompany').value.trim();
    const guestLinkedIn = document.getElementById('guestLinkedIn').value.trim();
    const statusDiv = document.getElementById('generatingStatus');
    const generateBtn = document.getElementById('generateContentBtn');
    
    // Get fileHash from cache if available (for updating processed data)
    let fileHash = null;
    if (videoInfo && videoInfo.video_id) {
        // Try to find the processed key that matches this video_id
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('processed_')) {
                try {
                    const processedData = localStorage.getItem(key);
                    if (processedData) {
                        const parsed = JSON.parse(processedData);
                        if (parsed.videoInfo && parsed.videoInfo.video_id === videoInfo.video_id) {
                            fileHash = key.replace('processed_', '');
                            break;
                        }
                    }
                } catch (e) {
                    // Continue searching
                }
            }
        }
    }
    
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
    
    // Check cache for existing content (unless forcing regenerate)
    if (!forceRegenerate && videoInfo && videoInfo.video_id) {
        const contentKey = `content_${videoInfo.video_id}`;
        const cachedContent = localStorage.getItem(contentKey);
        if (cachedContent) {
            try {
                const content = JSON.parse(cachedContent);
                if (content.data) {
                    // Check if guest info matches (simple check - could be enhanced)
                    const useCached = confirm('Content already generated for this project. Use cached content? Click OK to use cached, Cancel to regenerate.');
                    if (useCached) {
                        displayResults(content.data);
                        document.getElementById('resultsContainer').style.display = 'block';
                        document.getElementById('resultsContainer').scrollIntoView({ behavior: 'smooth' });
                        showStatus(statusDiv, 'Using cached content!', 'success');
                        return;
                    }
                }
            } catch (e) {
                console.error('Error parsing cached content:', e);
            }
        }
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
                    guest_name: guestName,
                    timestamp: Date.now()
                };
                localStorage.setItem(contentKey, JSON.stringify(contentData));
                
                // Also store guest name in the processed data for gallery display
                const processedKey = `processed_${fileHash || videoInfo.video_id}`;
                const processedData = localStorage.getItem(processedKey);
                if (processedData) {
                    try {
                        const parsed = JSON.parse(processedData);
                        parsed.guestName = guestName;
                        localStorage.setItem(processedKey, JSON.stringify(parsed));
                    } catch (e) {
                        console.error('Error updating processed data with guest name:', e);
                    }
                }
                
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
        
        // Show regenerate button
        const regenerateBtn = document.getElementById('regenerateContentBtn');
        if (regenerateBtn) {
            regenerateBtn.style.display = 'inline-block';
        }
        
    } catch (error) {
        console.error('Error generating content:', error);
        showStatus(statusDiv, `Error: ${error.message}`, 'error');
    } finally {
        generateBtn.disabled = false;
        hideLoading();
    }
}

// Display transcript separately (called after processing and when opening projects)
function displayTranscript() {
    const transcriptElement = document.getElementById('transcript');
    if (!transcriptElement) {
        console.error('Transcript element not found');
        return;
    }
    
    if (!transcriptData) {
        transcriptElement.textContent = 'No transcript data available. Please process an audio file first.';
        return;
    }
    
    // Prioritize transcript_with_timecodes if available
    if (transcriptData.transcript_with_timecodes) {
        const timecodes = transcriptData.transcript_with_timecodes;
        
        if (Array.isArray(timecodes) && timecodes.length > 0) {
            // Format array of timecode objects
            transcriptElement.textContent = formatTranscriptWithTimecodes(timecodes);
            return;
        } else if (typeof timecodes === 'string' && timecodes.trim()) {
            // If it's already a formatted string, use it directly
            transcriptElement.textContent = timecodes;
            return;
        }
    }
    
    // Fallback to plain transcript if timecodes not available or invalid
    if (transcriptData.transcript) {
        transcriptElement.textContent = transcriptData.transcript;
    } else {
        transcriptElement.textContent = 'No transcript data available. Please ensure the audio file was processed correctly.';
    }
}

// Display Results
function displayResults(data) {
    // Display transcript if available
    displayTranscript();
    
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
    
    return timecodes.map((item) => {
        // Handle both {start, text} and {start, end, text} formats
        const start = item.start !== undefined ? item.start : (item.start_time !== undefined ? item.start_time : 0);
        const timestamp = formatTimestamp(start);
        const text = item.text || item.transcript || '';
        return `${timestamp} ${text}`.trim();
    }).filter(line => line.length > 0).join('\n');
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

// Regenerate individual content type
async function regenerateContent(contentType, targetId) {
    if (!transcriptData) {
        alert('Please process an audio file first');
        return;
    }
    
    const guestName = document.getElementById('guestName')?.value.trim() || '';
    const guestTitle = document.getElementById('guestTitle')?.value.trim() || '';
    const guestCompany = document.getElementById('guestCompany')?.value.trim() || '';
    const guestLinkedIn = document.getElementById('guestLinkedIn')?.value.trim() || '';
    
    if (!guestName || !guestTitle || !guestCompany || !guestLinkedIn) {
        alert('Please fill in all guest information fields first');
        return;
    }
    
    const targetElement = document.getElementById(targetId);
    if (!targetElement) {
        console.error(`Target element ${targetId} not found`);
        return;
    }
    
    // Show loading state
    const originalContent = targetElement.textContent || targetElement.innerHTML;
    targetElement.textContent = 'Regenerating...';
    targetElement.style.opacity = '0.5';
    
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
        
        const response = await fetch(`${API_BASE_URL}/api/generate-content/${contentType}`, {
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
            throw new Error(error.detail || 'Failed to regenerate content');
        }
        
        const data = await response.json();
        const newContent = data[contentType];
        
        // Update the specific element
        if (targetId === 'blogPost' || targetId === 'linkedinPost') {
            targetElement.innerHTML = formatMarkdownLinks(newContent);
        } else if (targetId === 'clickbaitTitles' || targetId === 'quotes') {
            targetElement.innerHTML = formatList(Array.isArray(newContent) ? newContent : [newContent]);
        } else if (targetId === 'chapterTimestamps') {
            targetElement.textContent = Array.isArray(newContent) ? newContent.join('\n') : newContent;
        } else {
            targetElement.textContent = newContent;
        }
        
        // Update cached content
        if (videoInfo && videoInfo.video_id) {
            const contentKey = `content_${videoInfo.video_id}`;
            const cachedContent = localStorage.getItem(contentKey);
            if (cachedContent) {
                try {
                    const content = JSON.parse(cachedContent);
                    if (content.data) {
                        content.data[contentType] = newContent;
                        localStorage.setItem(contentKey, JSON.stringify(content));
                    }
                } catch (e) {
                    console.error('Error updating cached content:', e);
                }
            }
        }
        
        targetElement.style.opacity = '1';
    } catch (error) {
        console.error(`Error regenerating ${contentType}:`, error);
        targetElement.textContent = originalContent;
        targetElement.innerHTML = originalContent;
        targetElement.style.opacity = '1';
        alert(`Error regenerating content: ${error.message}`);
    }
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

function downloadAsTxt(targetId) {
    const element = document.getElementById(targetId);
    
    if (!element) {
        alert('Content not found');
        return;
    }
    
    let textToDownload = '';
    
    if (element) {
        // If it's HTML content (blog post, LinkedIn post), get text content
        textToDownload = element.textContent || element.innerText || '';
    }
    
    if (!textToDownload.trim()) {
        alert('Nothing to download');
        return;
    }
    
    // Filename mapping
    const filenameMap = {
        'transcript': 'transcript-with-timecodes.txt',
        'youtubeSummary': 'youtube-summary.txt',
        'blogPost': 'blog-post.txt',
        'twoLineSummary': 'two-line-summary.txt',
        'clickbaitTitles': 'clickbait-titles.txt',
        'quotes': 'quotes.txt',
        'chapterTimestamps': 'chapter-timestamps.txt',
        'linkedinPost': 'linkedin-post.txt',
        'keywords': 'keywords.txt',
        'hashtags': 'hashtags.txt'
    };
    
    const filename = filenameMap[targetId] || `${targetId}.txt`;
    
    // Create blob and download
    const blob = new Blob([textToDownload], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// Clear old cache entries to free up localStorage space
function clearOldCache() {
    try {
        const keysToRemove = [];
        const now = Date.now();
        const maxAge = 30 * 24 * 60 * 60 * 1000; // 30 days in milliseconds
        
        // Scan localStorage for old cache entries
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && (key.startsWith('processed_') || key.startsWith('audio_') || key.startsWith('content_'))) {
                try {
                    const item = localStorage.getItem(key);
                    if (item) {
                        const parsed = JSON.parse(item);
                        if (parsed.timestamp && (now - parsed.timestamp) > maxAge) {
                            keysToRemove.push(key);
                        }
                    }
                } catch (e) {
                    // If can't parse, might be old format, remove it
                    keysToRemove.push(key);
                }
            }
        }
        
        // Remove old entries
        keysToRemove.forEach(key => {
            try {
                localStorage.removeItem(key);
                console.log(`Removed old cache entry: ${key}`);
            } catch (e) {
                console.error(`Error removing cache entry ${key}:`, e);
            }
        });
        
        if (keysToRemove.length > 0) {
            console.log(`Cleared ${keysToRemove.length} old cache entries`);
        }
    } catch (e) {
        console.error('Error clearing old cache:', e);
    }
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
    
    // Load prompts if switching to prompts tab (requires authentication)
    if (tabName === 'prompts') {
        if (!authToken) {
            showLoginModal();
            // Switch back to content tab if not authenticated
            setTimeout(() => {
                switchTab('content');
                const contentTabBtn = document.querySelector('[data-tab="content"]');
                if (contentTabBtn) {
                    contentTabBtn.classList.add('active');
                }
            }, 100);
            return;
        }
        loadPrompts();
    }
    
    // Load gallery if switching to gallery tab
    if (tabName === 'gallery') {
        loadGallery();
    }
    
    // Update webhook URL if switching to API tab
    if (tabName === 'api') {
        const webhookUrlElement = document.getElementById('webhookUrl');
        if (webhookUrlElement) {
            webhookUrlElement.textContent = `${API_BASE_URL}/api/generate-content`;
        }
        // Hide API details when switching to tab
        hideApiDetails();
    }
}

function showApiDetails() {
    const apiDetails = document.getElementById('apiDetails');
    const apiTiles = document.querySelector('.api-tiles-container');
    if (apiDetails) apiDetails.style.display = 'block';
    if (apiTiles) apiTiles.style.display = 'none';
    // Update webhook URL
    const webhookUrlElement = document.getElementById('webhookUrl');
    if (webhookUrlElement) {
        webhookUrlElement.textContent = `${API_BASE_URL}/api/generate-content`;
    }
}

function hideApiDetails() {
    const apiDetails = document.getElementById('apiDetails');
    const apiTiles = document.querySelector('.api-tiles-container');
    if (apiDetails) apiDetails.style.display = 'none';
    if (apiTiles) apiTiles.style.display = 'grid';
}

function copyWebhookUrl() {
    const webhookUrl = `${API_BASE_URL}/api/generate-content`;
    navigator.clipboard.writeText(webhookUrl).then(() => {
        alert('Webhook URL copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy URL');
    });
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
                    
                    // Try to extract guest name from processed data or content
                    let guestName = data.guestName || null;
                    if (!guestName && generatedContent) {
                        guestName = generatedContent.guest_name || null;
                    }
                    
                    projects.push({
                        id: projectId,
                        key: key,
                        videoInfo: videoInfo,
                        transcriptData: data.transcriptData,
                        timestamp: data.timestamp || Date.now(),
                        hasContent: !!generatedContent,
                        contentKey: contentKey,
                        guestName: guestName
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
    
    // Get guest name - prioritize stored guestName, fallback to video title
    const guestName = project.guestName || project.videoInfo?.title || 'Untitled Project';
    
    card.innerHTML = `
        <div class="gallery-card-header">
            <h3 class="gallery-card-title">${escapeHtml(guestName)}</h3>
            <span class="gallery-card-date">${dateStr}</span>
        </div>
        <div class="gallery-card-body">
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
        
        // Clear guest information fields
        const guestNameInput = document.getElementById('guestName');
        const guestTitleInput = document.getElementById('guestTitle');
        const guestCompanyInput = document.getElementById('guestCompany');
        const guestLinkedInInput = document.getElementById('guestLinkedIn');
        if (guestNameInput) guestNameInput.value = '';
        if (guestTitleInput) guestTitleInput.value = '';
        if (guestCompanyInput) guestCompanyInput.value = '';
        if (guestLinkedInInput) guestLinkedInInput.value = '';
        
        // Display transcript
        displayTranscript();
        
        // Show step 2 (guest info) if transcript is loaded
        if (transcriptData) {
            document.getElementById('step2Card').style.display = 'block';
            document.getElementById('step1Card').scrollIntoView({ behavior: 'smooth' });
        }
        
        // Show regenerate button if content exists
        if (videoInfo && videoInfo.video_id) {
            const contentKey = `content_${videoInfo.video_id}`;
            const contentData = localStorage.getItem(contentKey);
            if (contentData) {
                const regenerateBtn = document.getElementById('regenerateContentBtn');
                if (regenerateBtn) {
                    regenerateBtn.style.display = 'inline-block';
                }
            }
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
        // Get video_id from processed data before deleting to clear OpenAI cache
        // Content is stored under content_${videoInfo.video_id}, not content_${projectId}
        let videoId = null;
        let contentKey = null;
        
        // First, read the processed data to get videoInfo.video_id
        const processedData = localStorage.getItem(cacheKey);
        if (processedData) {
            try {
                const parsed = JSON.parse(processedData);
                if (parsed.videoInfo && parsed.videoInfo.video_id) {
                    videoId = parsed.videoInfo.video_id;
                    contentKey = `content_${videoId}`;
                }
            } catch (e) {
                console.error('Error parsing processed data for deletion:', e);
            }
        }
        
        // Delete processed data
        localStorage.removeItem(cacheKey);
        
        // Delete audio file if exists
        localStorage.removeItem(`audio_${projectId}`);
        
        // Delete generated content if exists (using correct content key)
        if (contentKey) {
            localStorage.removeItem(contentKey);
        }
        
        // Clear OpenAI cache if video_id exists (clear all content_ keys for this video)
        // Also clear any processed_ keys that might reference this video
        if (videoId) {
            try {
                // Find and delete all content_ keys related to this video
                for (let i = localStorage.length - 1; i >= 0; i--) {
                    const key = localStorage.key(i);
                    if (key && key.startsWith('content_')) {
                        try {
                            const contentData = localStorage.getItem(key);
                            if (contentData) {
                                const parsed = JSON.parse(contentData);
                                if (parsed.video_id === videoId || parsed.data?.video_id === videoId) {
                                    localStorage.removeItem(key);
                                }
                            }
                        } catch (e) {
                            // If key contains videoId in the key name itself, remove it
                            if (key.includes(videoId)) {
                                localStorage.removeItem(key);
                            }
                        }
                    }
                }
                // Also clear any processed_ keys that reference this video_id
                for (let i = localStorage.length - 1; i >= 0; i--) {
                    const key = localStorage.key(i);
                    if (key && key.startsWith('processed_')) {
                        try {
                            const processedData = localStorage.getItem(key);
                            if (processedData) {
                                const parsed = JSON.parse(processedData);
                                if (parsed.videoInfo?.video_id === videoId) {
                                    localStorage.removeItem(key);
                                }
                            }
                        } catch (e) {
                            // Skip if can't parse
                        }
                    }
                }
            } catch (e) {
                console.error('Error clearing OpenAI cache:', e);
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
            document.getElementById('prompt_keywords').value = data.prompts.keywords || '';
            
            // Update previews after loading
            updatePromptPreviews();
        }
    } catch (error) {
        console.error('Error loading prompts:', error);
        showStatus(document.getElementById('promptsStatus'), 'Error loading prompts', 'error');
    }
}

async function savePrompts() {
    // Show warnings modal first
    showSaveWarnings();
}

// Actual save function (called after warnings confirmation)
async function performSavePrompts() {
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
            linkedin_post: document.getElementById('prompt_linkedin_post').value,
            keywords: document.getElementById('prompt_keywords').value
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
            
            // Update prompt previews after successful save
            updatePromptPreviews();
            
            // Re-disable all textareas (set them back to readonly)
            document.querySelectorAll('.prompt-textarea').forEach(textarea => {
                textarea.setAttribute('readonly', 'readonly');
            });
            
            // Remove editing class from all tiles
            document.querySelectorAll('.prompt-tile').forEach(tile => {
                tile.classList.remove('editing');
            });
        }
    } catch (error) {
        console.error('Error saving prompts:', error);
        showStatus(statusDiv, error.message || 'Error saving prompts', 'error');
    } finally {
        saveBtn.disabled = false;
    }
}

// Update prompt previews with truncated versions
function updatePromptPreviews() {
    const promptIds = ['youtube_summary', 'blog_post', 'clickbait_titles', 'two_line_summary', 
                       'quotes', 'chapter_timestamps', 'linkedin_post', 'keywords'];
    
    promptIds.forEach(promptId => {
        const textarea = document.getElementById(`prompt_${promptId}`);
        const previewDiv = document.querySelector(`[data-preview="${promptId}"]`);
        
        if (textarea && previewDiv) {
            const promptText = textarea.value || '';
            // Truncate to first 150 characters for preview
            const previewText = promptText.length > 150 
                ? promptText.substring(0, 150) + '...' 
                : promptText;
            
            previewDiv.textContent = previewText || 'No prompt set';
        }
    });
}

// Toggle prompt tile expand/collapse
function togglePromptExpand(promptId, button) {
    const tile = document.querySelector(`[data-prompt-id="${promptId}"]`);
    const contentDiv = tile?.querySelector('.prompt-tile-content');
    const previewDiv = tile?.querySelector('.prompt-tile-preview');
    const expandIcon = button?.querySelector('svg');
    
    if (!tile || !contentDiv) return;
    
    const isExpanded = contentDiv.style.display !== 'none';
    
    if (isExpanded) {
        // Collapse
        contentDiv.style.display = 'none';
        if (previewDiv) previewDiv.style.display = 'block';
        if (expandIcon) {
            expandIcon.innerHTML = '<path d="M6 9l6 6 6-6"/>';
        }
    } else {
        // Expand
        contentDiv.style.display = 'block';
        if (previewDiv) previewDiv.style.display = 'none';
        if (expandIcon) {
            expandIcon.innerHTML = '<path d="M6 15l6-6 6 6"/>';
        }
    }
}

// Show edit password modal
function showEditPasswordModal(promptId) {
    const modal = document.getElementById('editPasswordModal');
    if (!modal) return;
    
    // Store the prompt ID for verification
    modal.setAttribute('data-prompt-id', promptId);
    document.getElementById('editPasswordInput').value = '';
    modal.style.display = 'flex';
}

// Verify edit password and enable editing
async function verifyEditPassword() {
    const modal = document.getElementById('editPasswordModal');
    const passwordInput = document.getElementById('editPasswordInput');
    const promptId = modal?.getAttribute('data-prompt-id');
    
    if (!promptId || !passwordInput) return;
    
    const enteredPassword = passwordInput.value;
    
    if (!enteredPassword) {
        alert('Please enter a password');
        return;
    }
    
    // Check password by attempting API call
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: enteredPassword })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            // Password is correct - enable editing for this prompt
            const textarea = document.getElementById(`prompt_${promptId}`);
            const tile = document.querySelector(`[data-prompt-id="${promptId}"]`);
            
            if (textarea) {
                textarea.removeAttribute('readonly');
                textarea.focus();
            }
            
            if (tile) {
                tile.classList.add('editing');
            }
            
            // Close modal
            modal.style.display = 'none';
            passwordInput.value = '';
        } else {
            alert('Incorrect password. Access denied.');
            passwordInput.value = '';
            passwordInput.focus();
        }
    } catch (error) {
        console.error('Password verification error:', error);
        alert('Password verification failed. Please try again.');
        passwordInput.value = '';
        passwordInput.focus();
    }
}

// Show save warnings modal
function showSaveWarnings() {
    const modal = document.getElementById('saveWarningsModal');
    if (!modal) {
        // If modal doesn't exist, proceed with save directly
        performSavePrompts();
        return;
    }
    modal.style.display = 'flex';
}

// Copy variable to clipboard
function copyVariable(variable, button) {
    if (!variable) {
        alert('Nothing to copy');
        return;
    }
    
    navigator.clipboard.writeText(variable).then(() => {
        // Visual feedback
        if (button) {
            button.classList.add('copied');
            setTimeout(() => {
                button.classList.remove('copied');
            }, 2000);
        }
    }).catch(err => {
        console.error('Failed to copy variable:', err);
        alert('Failed to copy variable to clipboard');
    });
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