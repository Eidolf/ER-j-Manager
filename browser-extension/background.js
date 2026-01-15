// JDownloader Manager CNL Bridge - Background Service Worker
// Intercepts CNL requests to localhost:9666 and forwards to remote server

// Default settings
const DEFAULT_SETTINGS = {
    serverUrl: '',
    token: '',
    enabled: true
};

// Load settings from storage
async function getSettings() {
    const result = await chrome.storage.sync.get(DEFAULT_SETTINGS);
    return result;
}

// CNL endpoints we want to intercept
const CNL_ENDPOINTS = [
    '/flash/addcrypted',
    '/flash/addcrypted2',
    '/flash/add',
    '/flash/check',
    '/jdcheck.js'
];

// Handle CNL check request - respond with "JDownloader" to indicate we're ready
async function handleCheck() {
    return new Response('JDownloader', {
        status: 200,
        headers: { 'Content-Type': 'text/plain' }
    });
}

// Handle jdcheck.js request
async function handleJdCheck() {
    return new Response('jdownloader=true;', {
        status: 200,
        headers: { 'Content-Type': 'application/javascript' }
    });
}

// Forward CNL request to remote server
async function forwardToServer(request, settings) {
    if (!settings.serverUrl) {
        console.error('CNL Bridge: No server URL configured');
        return new Response('No server configured', { status: 500 });
    }

    try {
        // Parse the form data from the original request
        const formData = await request.formData();

        // Build the target URL
        const url = new URL(request.url);
        const targetUrl = `${settings.serverUrl}/cnl${url.pathname}`;

        // Forward the request
        const response = await fetch(targetUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${settings.token}`
            },
            body: formData
        });

        const text = await response.text();
        console.log(`CNL Bridge: Forwarded to ${targetUrl}, status: ${response.status}`);

        return new Response(text, {
            status: response.status,
            headers: { 'Content-Type': 'text/plain' }
        });
    } catch (error) {
        console.error('CNL Bridge: Forward failed', error);
        return new Response('failed', { status: 500 });
    }
}

// Listen for fetch events (via declarativeNetRequest in MV3)
// Note: MV3 doesn't support webRequest blocking, so we use a different approach

// We'll use chrome.webRequest.onBeforeRequest to detect CNL requests
// and chrome.webNavigation to intercept them

chrome.webRequest.onBeforeRequest.addListener(
    async (details) => {
        const url = new URL(details.url);
        const settings = await getSettings();

        if (!settings.enabled || !settings.serverUrl) {
            return; // Let it pass through normally
        }

        // Check if this is a CNL endpoint
        const isCnlRequest = CNL_ENDPOINTS.some(ep => url.pathname.startsWith(ep));

        if (isCnlRequest) {
            console.log('CNL Bridge: Intercepted request to', details.url);

            // For check endpoints, we respond directly
            if (url.pathname === '/flash/check') {
                // We can't respond directly in MV3, but we've set up server to handle this
            }
        }
    },
    {
        urls: [
            'http://127.0.0.1:9666/*',
            'http://localhost:9666/*'
        ]
    }
);

// Handle messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'getSettings') {
        getSettings().then(sendResponse);
        return true; // Will respond asynchronously
    }

    if (message.type === 'saveSettings') {
        chrome.storage.sync.set(message.settings).then(() => {
            sendResponse({ success: true });
        });
        return true;
    }

    if (message.type === 'testConnection') {
        testConnection(message.serverUrl, message.token).then(sendResponse);
        return true;
    }
});

// Test connection to remote server
async function testConnection(serverUrl, token) {
    try {
        const response = await fetch(`${serverUrl}/api/v1/system/status`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            return { success: true, data };
        } else {
            return { success: false, error: `HTTP ${response.status}` };
        }
    } catch (error) {
        return { success: false, error: error.message };
    }
}

console.log('JDownloader Manager CNL Bridge loaded');
