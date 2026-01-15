import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { X, Save, Server } from 'lucide-react';

interface Settings {
    jd_host: string;
    jd_port: number;
    use_mock: boolean;
    admin_password?: string;
}

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
    const [settings, setSettings] = useState<Settings>({
        jd_host: 'host.docker.internal',
        jd_port: 3128,
        use_mock: true,
        admin_password: ''
    });
    const [loading, setLoading] = useState(true);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);
    const [activeTab, setActiveTab] = useState('general');
    const [helpContent, setHelpContent] = useState('');

    useEffect(() => {
        if (isOpen) {
            setLoading(true);
            api.get('/settings')
                .then(res => setSettings(res.data))
                .catch(err => console.error("Failed to load settings", err))
                .finally(() => setLoading(false));
        }
    }, [isOpen]);

    useEffect(() => {
        if (isOpen && activeTab === 'api_info') {
            api.get('/settings/help')
                .then(res => setHelpContent(res.data.text))
                .catch(() => setHelpContent('Failed to load help.'));
        }
    }, [isOpen, activeTab]);

    const handleSave = async () => {
        try {
            await api.post('/settings', settings);
            onClose();
            window.location.reload();
        } catch (error) {
            console.error("Failed to save settings", error);
            alert("Failed to save settings");
        }
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setTestResult(null);
        try {
            const res = await api.post('/settings/test', settings);
            if (res.data.status === 'ok') {
                setTestResult('success');
            } else {
                setTestResult('error');
                alert("Connection Failed: " + res.data.message);
            }
        } catch {
            setTestResult('error');
        } finally {
            setTesting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-4xl bg-cyber-card border border-cyber-neon/50 rounded-xl p-6 shadow-[0_0_20px_rgba(236,72,153,0.3)] max-h-[85vh] flex flex-col">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold flex items-center gap-2 neon-text">
                        <Server size={20} /> Settings
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="flex gap-2 mb-6 border-b border-gray-700 pb-2">
                    <button
                        onClick={() => setActiveTab('general')}
                        className={`px-3 py-1 rounded transition-colors ${activeTab === 'general' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        General
                    </button>
                    <button
                        onClick={() => setActiveTab('api_info')}
                        className={`px-3 py-1 rounded transition-colors ${activeTab === 'api_info' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        API Info
                    </button>
                    <button
                        onClick={() => setActiveTab('setup_guide')}
                        className={`px-3 py-1 rounded transition-colors ${activeTab === 'setup_guide' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        Setup Guide
                    </button>
                    <button
                        onClick={() => setActiveTab('extension')}
                        className={`px-3 py-1 rounded transition-colors ${activeTab === 'extension' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        🔌 Browser Extension
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    {loading && activeTab === 'general' ? (
                        <div className="text-center py-8 text-cyber-neon animate-pulse">Loading Configuration...</div>
                    ) : (
                        <>
                            {activeTab === 'general' && (
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">JDownloader Host / IP</label>
                                        <div className="glass-input-wrapper">
                                            <div className="absolute inset-0 z-0 bg-transparent"
                                                style={{
                                                    animation: `border-rotate ${3 + Math.random() * 2}s linear infinite`,
                                                    animationDelay: `-${Math.random() * 5}s`
                                                }}
                                            />
                                            <input
                                                type="text"
                                                value={settings.jd_host}
                                                onChange={e => setSettings({ ...settings, jd_host: e.target.value })}
                                                className="glass-input p-2"
                                                placeholder="e.g. host.docker.internal"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">Port</label>
                                        <div className="glass-input-wrapper">
                                            <div className="absolute inset-0 z-0 bg-transparent"
                                                style={{
                                                    animation: `border-rotate ${4 + Math.random() * 2}s linear infinite reverse`,
                                                    animationDelay: `-${Math.random() * 5}s`
                                                }}
                                            />
                                            <input
                                                type="number"
                                                value={settings.jd_port}
                                                onChange={e => setSettings({ ...settings, jd_port: parseInt(e.target.value) })}
                                                className="glass-input p-2"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm text-gray-400 mb-1">Admin Password</label>
                                        <div className="glass-input-wrapper">
                                            <div className="absolute inset-0 z-0 bg-transparent"
                                                style={{
                                                    animation: `border-rotate ${5 + Math.random() * 2}s linear infinite`,
                                                    animationDelay: `-${Math.random() * 5}s`
                                                }}
                                            />
                                            <input
                                                type="password"
                                                value={settings.admin_password || ''}
                                                onChange={e => setSettings({ ...settings, admin_password: e.target.value })}
                                                className="glass-input p-2"
                                                placeholder="Enter new password"
                                            />
                                        </div>
                                    </div>

                                    {!settings.use_mock && (
                                        <div className="text-xs text-yellow-500 bg-yellow-500/10 p-2 rounded">
                                            Note: Ensure your JDownloader has the Remote Control extension enabled on port {settings.jd_port}.
                                        </div>
                                    )}

                                    <div className="pt-4 space-y-2">
                                        <button
                                            onClick={handleSave}
                                            className="w-full py-2 bg-cyber-purple hover:bg-cyber-purple/80 text-white font-bold rounded flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-cyan-500/20"
                                        >
                                            <Save size={18} /> Save Configuration
                                        </button>

                                        <button
                                            onClick={handleTestConnection}
                                            disabled={testing}
                                            className={`w-full py-2 rounded font-bold flex items-center justify-center gap-2 transition-all ${testing ? 'bg-gray-600 cursor-wait' :
                                                testResult === 'success' ? 'bg-green-500/20 text-green-400 border border-green-500/50' :
                                                    testResult === 'error' ? 'bg-red-500/20 text-red-400 border border-red-500/50' :
                                                        'bg-gray-700 hover:bg-gray-600 text-gray-300'
                                                }`}
                                        >
                                            <Server size={18} />
                                            {testing ? 'Testing...' : testResult === 'success' ? 'Connected!' : 'Test Connection'}
                                        </button>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'api_info' && (
                                <div className="space-y-4 h-full flex flex-col min-h-0">
                                    <p className="text-sm text-gray-400 shrink-0">Response from JDownloader <code>/help</code> endpoint:</p>
                                    <div className="flex-1 min-h-0 bg-gray-950 rounded-lg border border-gray-800 overflow-hidden">
                                        <pre className="h-full p-4 text-xs text-green-400 font-mono overflow-auto scrollbar-thin scrollbar-thumb-cyber-purple/20 whitespace-pre-wrap">
                                            {helpContent || 'Loading or empty response...'}
                                        </pre>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'setup_guide' && (
                                <div className="space-y-4 text-gray-300 text-sm">
                                    <h3 className="text-lg font-bold text-white neon-text">Enabling Remote API</h3>
                                    <p>To control JDownloader 2 via this dashboard, you must enable the deprecated API:</p>
                                    <ol className="list-decimal list-inside space-y-3 marker:text-cyber-neon pl-2">
                                        <li>Open <strong>JDownloader 2</strong>.</li>
                                        <li>Go to <strong>Settings</strong> &gt; <strong>Advanced Settings</strong>.</li>
                                        <li>Search for <code>RemoteAPI</code>.</li>
                                        <li>Enable the setting: <br /><code className="bg-gray-800 px-1 rounded text-cyber-neon">RemoteAPI: Deprecated Api Enabled</code>.</li>
                                        <li>Restart JDownloader 2.</li>
                                    </ol>
                                    <p className="mt-6 text-xs text-gray-400 bg-gray-900/50 p-3 rounded border border-gray-800 border-l-2 border-l-cyber-purple">
                                        This dashboard communicates directly with your local JDownloader instance on port <strong>3128</strong> using the MyJDownloader API protocol tailored for local access.
                                    </p>
                                </div>
                            )}

                            {activeTab === 'extension' && (
                                <div className="space-y-6 text-gray-300 text-sm">
                                    <div className="bg-gradient-to-r from-cyber-purple/20 to-cyber-neon/10 p-4 rounded-xl border border-cyber-neon/30">
                                        <h3 className="text-lg font-bold text-white neon-text mb-2">🔌 Remote Click'n'Load</h3>
                                        <p className="text-gray-400">
                                            Use this browser extension to send Click'n'Load links from <strong>any computer</strong> to your JDownloader Manager server.
                                        </p>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-white mb-3">📥 Download</h4>
                                        <a
                                            href="/browser-extension.tar.gz"
                                            download="jd-manager-cnl-bridge.tar.gz"
                                            className="inline-flex items-center gap-2 px-6 py-3 bg-cyber-purple hover:bg-cyber-purple/80 text-white font-bold rounded-lg transition-all shadow-lg hover:shadow-cyan-500/20"
                                        >
                                            ⬇️ Download Extension (.tar.gz)
                                        </a>
                                        <p className="text-xs text-gray-500 mt-2">Compatible with Chrome, Edge, Brave (Chromium-based browsers)</p>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-white mb-3">🛠️ Installation</h4>
                                        <ol className="list-decimal list-inside space-y-2 marker:text-cyber-neon pl-2">
                                            <li>Extract the downloaded .zip file</li>
                                            <li>Open <code className="bg-gray-800 px-1 rounded">chrome://extensions/</code> in your browser</li>
                                            <li>Enable <strong>"Developer mode"</strong> (top right toggle)</li>
                                            <li>Click <strong>"Load unpacked"</strong></li>
                                            <li>Select the extracted folder</li>
                                        </ol>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-white mb-3">⚙️ Configuration</h4>
                                        <ol className="list-decimal list-inside space-y-2 marker:text-cyber-neon pl-2">
                                            <li>Click the extension icon in your toolbar</li>
                                            <li>Enter your <strong>Server URL</strong>: <code className="bg-gray-800 px-1 rounded text-cyber-neon">{window.location.origin}</code></li>
                                            <li>Enter your <strong>Auth Token</strong> (from browser localStorage → "token")</li>
                                            <li>Click <strong>Save</strong> and <strong>Test</strong></li>
                                        </ol>
                                    </div>

                                    <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
                                        <h4 className="font-semibold text-yellow-500 mb-2">💡 How it works</h4>
                                        <p className="text-xs text-gray-400">
                                            When you click a Click'n'Load button on a website, the extension intercepts the request
                                            (normally sent to <code>localhost:9666</code>) and forwards it to your JDownloader Manager server.
                                            The links are then buffered and replayed to your JDownloader when it's online.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};
