// Popup script for JDownloader Manager CNL Bridge

document.addEventListener('DOMContentLoaded', async () => {
    const serverUrlInput = document.getElementById('serverUrl');
    const tokenInput = document.getElementById('token');
    const enabledCheckbox = document.getElementById('enabled');
    const saveBtn = document.getElementById('saveBtn');
    const testBtn = document.getElementById('testBtn');
    const statusDiv = document.getElementById('status');
    const statusText = document.getElementById('statusText');
    const messageDiv = document.getElementById('message');

    // Load saved settings
    const settings = await chrome.runtime.sendMessage({ type: 'getSettings' });
    serverUrlInput.value = settings.serverUrl || '';
    tokenInput.value = settings.token || '';
    enabledCheckbox.checked = settings.enabled !== false;

    // Update status display
    if (settings.serverUrl && settings.token) {
        testConnection(settings.serverUrl, settings.token);
    }

    // Save settings
    saveBtn.addEventListener('click', async () => {
        const settings = {
            serverUrl: serverUrlInput.value.trim().replace(/\/$/, ''), // Remove trailing slash
            token: tokenInput.value.trim(),
            enabled: enabledCheckbox.checked
        };

        await chrome.runtime.sendMessage({ type: 'saveSettings', settings });
        showMessage('Settings saved!', 'success');

        // Test the connection after saving
        if (settings.serverUrl && settings.token) {
            testConnection(settings.serverUrl, settings.token);
        }
    });

    // Test connection
    testBtn.addEventListener('click', () => {
        const serverUrl = serverUrlInput.value.trim().replace(/\/$/, '');
        const token = tokenInput.value.trim();

        if (!serverUrl) {
            showMessage('Please enter a server URL', 'error');
            return;
        }

        testConnection(serverUrl, token);
    });

    async function testConnection(serverUrl, token) {
        statusDiv.className = 'status-indicator disconnected';
        statusText.textContent = 'Testing...';

        const result = await chrome.runtime.sendMessage({
            type: 'testConnection',
            serverUrl,
            token
        });

        if (result.success) {
            statusDiv.className = 'status-indicator connected';
            statusText.textContent = `Connected (JD: ${result.data.jd_online ? 'Online' : 'Offline'})`;
            showMessage('Connection successful!', 'success');
        } else {
            statusDiv.className = 'status-indicator disconnected';
            statusText.textContent = 'Connection Failed';
            showMessage(`Error: ${result.error}`, 'error');
        }
    }

    function showMessage(text, type) {
        messageDiv.textContent = text;
        messageDiv.className = `message ${type}`;
        messageDiv.style.display = 'block';
        setTimeout(() => {
            messageDiv.style.display = 'none';
        }, 3000);
    }
});
