// JDownloader Manager CNL Bridge - Background Service Worker
// Redirects CNL requests from localhost:9666 to the configured remote server /cnl endpoint

const DEFAULT_SETTINGS = {
    serverUrl: '',
    token: '',
    enabled: true
};

async function getSettings() {
    const result = await chrome.storage.sync.get(DEFAULT_SETTINGS);
    return result;
}

// Update Dynamic Rules for Redirect
async function updateRules() {
    try {
        const settings = await getSettings();

        // Remove existing rules first
        const oldRules = await chrome.declarativeNetRequest.getDynamicRules();
        const oldRuleIds = oldRules.map(r => r.id);

        if (!settings.enabled || !settings.serverUrl) {
            console.log('CNL Bridge: Disabled or no server URL. Clearing rules.');
            if (oldRuleIds.length > 0) {
                await chrome.declarativeNetRequest.updateDynamicRules({
                    removeRuleIds: oldRuleIds,
                    addRules: []
                });
            }
            return;
        }

        const serverBase = settings.serverUrl.replace(/\/$/, '');
        // Redirect: http://localhost:9666/(.*) -> serverBase/cnl/\1
        const redirectTarget = `${serverBase}/cnl/\\1`;

        const rule = {
            "id": 1,
            "priority": 1,
            "action": {
                "type": "redirect",
                "redirect": { "regexSubstitution": redirectTarget }
            },
            "condition": {
                // Match localhost or 127.0.0.1 on port 9666
                "regexFilter": "^http://(?:127\\.0\\.0\\.1|localhost):9666/(.*)",
                "resourceTypes": ["xmlhttprequest", "main_frame", "sub_frame", "script", "image", "other"]
            }
        };

        await chrome.declarativeNetRequest.updateDynamicRules({
            removeRuleIds: oldRuleIds,
            addRules: [rule]
        });

        console.log(`CNL Bridge: Redirect rule active. 9666 -> ${redirectTarget}`);
    } catch (e) {
        console.error('Failed to update rules:', e);
    }
}

chrome.runtime.onInstalled.addListener(() => {
    updateRules();
    // Force icon update to fix Toolbar caching issues
    chrome.action.setIcon({
        path: {
            "16": "icons/icon16.png",
            "48": "icons/icon48.png",
            "128": "icons/icon128.png"
        }
    }).catch(err => console.error("Failed to set icon:", err));
});
chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'sync') {
        updateRules();
    }
});

// Popup Messaging
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'getSettings') {
        getSettings().then(sendResponse);
        return true;
    }

    if (message.type === 'saveSettings') {
        chrome.storage.sync.set(message.settings).then(() => {
            // Rules update triggered via storage.onChanged
            sendResponse({ success: true });
        });
        return true;
    }

    // Legacy test connection (ping)
    if (message.type === 'testConnection') {
        fetch(`${message.serverUrl}/api/v1/system/status`, {
            headers: { 'Authorization': `Bearer ${message.token}` }
        }).then(res => res.ok ? res.json() : Promise.reject(res.status))
            .then(data => sendResponse({ success: true, data }))
            .catch(err => sendResponse({ success: false, error: String(err) }));
        return true;
    }
});
