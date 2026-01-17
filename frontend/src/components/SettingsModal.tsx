import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Download, Settings as SettingsIcon, X, Server, Shield, Plug, Book, Smartphone, Check, Copy, Save, AlertTriangle } from 'lucide-react';

interface Settings {
    jd_host: string;
    jd_port: number;
    use_mock: boolean;
    admin_password?: string;
    default_download_path?: string;
    use_default_download_path?: boolean;
}

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const SecurityTabContent = () => {
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    // Password Strength Calculation
    const getStrength = (pass: string) => {
        let score = 0;
        if (!pass) return 0;
        if (pass.length > 8) score += 1;
        if (pass.length > 12) score += 1;
        if (/[A-Z]/.test(pass)) score += 1;
        if (/[0-9]/.test(pass)) score += 1;
        if (/[^A-Za-z0-9]/.test(pass)) score += 1;
        return score;
    };

    const strength = getStrength(newPassword);

    // UI Helpers for Strength
    const getStrengthColor = (s: number) => {
        if (s < 2) return 'bg-red-500';
        if (s < 4) return 'bg-yellow-500';
        return 'bg-green-500';
    };

    const getStrengthText = (s: number) => {
        if (s < 2) return 'Weak';
        if (s < 4) return 'Medium';
        return 'Strong';
    };

    const handleChangePassword = async () => {
        setError('');
        setSuccess('');

        if (newPassword !== confirmPassword) {
            setError("New passwords do not match.");
            return;
        }

        if (strength < 2) {
            setError("Password is too weak.");
            return;
        }

        setLoading(true);
        try {
            await api.post('/auth/change-password', {
                old_password: oldPassword,
                new_password: newPassword
            });
            setSuccess("Password updated successfully!");
            setOldPassword('');
            setNewPassword('');
            setConfirmPassword('');
            // Optional: Close modal after delay?
        } catch (err: unknown) {
            const errorMessage = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed to change password.";
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 text-gray-300 text-sm">
            <div className="bg-gradient-to-r from-red-900/20 to-pink-900/10 p-4 rounded-xl border border-red-500/30">
                <div className="flex items-center gap-2 mb-2">
                    <Shield className="text-red-400" size={20} />
                    <h3 className="text-lg font-bold text-white neon-text-red">Change Admin Password</h3>
                </div>
                <p className="text-gray-400">
                    Update the password used to access this dashboard.
                </p>
            </div>

            <div className="space-y-4 max-w-md mx-auto">
                {error && (
                    <div className="p-3 bg-red-500/10 border border-red-500/50 text-red-400 rounded flex items-center gap-2">
                        <AlertTriangle size={16} /> {error}
                    </div>
                )}
                {success && (
                    <div className="p-3 bg-green-500/10 border border-green-500/50 text-green-400 rounded flex items-center gap-2">
                        <Check size={16} /> {success}
                    </div>
                )}

                <div>
                    <label className="block text-sm text-gray-400 mb-1">Current Password</label>
                    <input
                        type="password"
                        value={oldPassword}
                        onChange={(e) => setOldPassword(e.target.value)}
                        className="w-full bg-black/40 border border-gray-700 rounded p-2 text-white focus:border-cyber-purple focus:outline-none transition-colors"
                        placeholder="••••••"
                    />
                </div>

                <div className="border-t border-gray-800 my-4"></div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1">New Password</label>
                    <input
                        type="password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        className="w-full bg-black/40 border border-gray-700 rounded p-2 text-white focus:border-cyber-purple focus:outline-none transition-colors"
                        placeholder="••••••••"
                    />
                    {/* Strength Meter */}
                    {newPassword && (
                        <div className="mt-2">
                            <div className="flex justify-between text-xs mb-1">
                                <span className="text-gray-500">Strength</span>
                                <span className={`${getStrengthColor(strength).replace('bg-', 'text-')}`}>{getStrengthText(strength)}</span>
                            </div>
                            <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all duration-300 ${getStrengthColor(strength)}`}
                                    style={{ width: `${(strength / 5) * 100}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>

                <div>
                    <label className="block text-sm text-gray-400 mb-1">Confirm New Password</label>
                    <input
                        type="password"
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        className={`w-full bg-black/40 border border-gray-700 rounded p-2 text-white focus:outline-none transition-colors ${confirmPassword && newPassword !== confirmPassword ? 'border-red-500' : 'focus:border-cyber-purple'}`}
                        placeholder="••••••••"
                    />
                    {confirmPassword && newPassword !== confirmPassword && (
                        <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
                    )}
                </div>

                <button
                    onClick={handleChangePassword}
                    disabled={loading || !oldPassword || !newPassword || strength < 2 || newPassword !== confirmPassword}
                    className={`w-full py-2.5 rounded font-bold flex items-center justify-center gap-2 transition-all mt-4
                        ${loading || !oldPassword || !newPassword || strength < 2 || newPassword !== confirmPassword
                            ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                            : 'bg-cyber-purple hover:bg-cyber-purple/80 text-white shadow-lg hover:shadow-cyan-500/20'}`}
                >
                    {loading ? 'Updating...' : <><Save size={18} /> Update Password</>}
                </button>
            </div>
        </div>
    );
};

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
    const [settings, setSettings] = useState<Settings>({
        jd_host: 'host.docker.internal',
        jd_port: 3128,
        use_mock: true,
        admin_password: '',
        default_download_path: '',
        use_default_download_path: false
    });
    const [loading, setLoading] = useState(true);
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<'success' | 'error' | null>(null);
    const [activeTab, setActiveTab] = useState('general');
    const [helpContent, setHelpContent] = useState('');
    const [copiedToken, setCopiedToken] = useState(false);

    useEffect(() => {
        if (isOpen) {
            setLoading(true);
            api.get('/settings')
                .then(res => setSettings(res.data))
                .catch(err => console.error("Failed to load settings", err))
                .finally(() => setLoading(false));

            // Pre-fetch default help
            api.get('/settings/help')
                .then(res => setHelpContent(res.data.text))
                .catch(() => setHelpContent('Failed to load help.'));
        }
    }, [isOpen]);

    const [apiInfoMode, setApiInfoMode] = useState<'raw' | 'docs'>('raw');
    const [docsContent, setDocsContent] = useState('');

    useEffect(() => {
        if (isOpen && activeTab === 'api_info' && apiInfoMode === 'docs' && !docsContent) {
            setLoading(true);
            api.get('/settings/help/docs')
                .then(res => setDocsContent(res.data.text))
                .catch(() => setDocsContent('# Error\nFailed to load docs.'))
                .finally(() => setLoading(false));
        }
    }, [isOpen, activeTab, apiInfoMode]);

    // Simple Markdown Renderer (Headers, Bold, Tables)
    const SimpleMarkdown = ({ content }: { content: string }) => {
        if (!content) return null;

        // Split by lines
        return (
            <div className="space-y-2 text-sm text-gray-300">
                {content.split('\n').map((line, i) => {
                    // Headers
                    if (line.startsWith('# ')) return <h1 key={i} className="text-xl font-bold text-cyber-neon mt-4 border-b border-gray-700 pb-1">{line.replace('# ', '')}</h1>;
                    if (line.startsWith('## ')) return <h2 key={i} className="text-lg font-bold text-white mt-4 mb-2">{line.replace('## ', '')}</h2>;
                    if (line.startsWith('### ')) return <h3 key={i} className="text-md font-bold text-gray-200 mt-3">{line.replace('### ', '')}</h3>;

                    // Table Rows (Simple)
                    if (line.startsWith('|')) {
                        const cols = line.split('|').filter(c => c.trim());
                        if (line.includes('---')) return null; // Skip separator
                        return (
                            <div key={i} className="grid grid-cols-5 gap-2 py-1 border-b border-gray-800 text-xs hover:bg-white/5">
                                {cols.map((col, j) => (
                                    <div key={j} className={j === 0 ? "font-bold text-cyber-neon" : "text-gray-400 truncate"} title={col.trim()}>
                                        {col.trim().replace(/\*\*/g, '')}
                                    </div>
                                ))}
                            </div>
                        );
                    }

                    // Bold Text via classic split (very naive but works for "**text**")
                    const parts = line.split('**');
                    return (
                        <div key={i} className="min-h-[1.2em]">
                            {parts.map((part, j) =>
                                j % 2 === 1 ? <strong key={j} className="text-white">{part}</strong> : part
                            )}
                        </div>
                    );
                })}
            </div>
        );
    };

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
                        <SettingsIcon size={20} /> Settings
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="flex gap-2 mb-6 border-b border-gray-700 pb-2 overflow-x-auto shrink-0 min-h-[50px]">
                    <button
                        onClick={() => setActiveTab('general')}
                        className={`px-3 py-2 rounded transition-colors flex items-center gap-2 ${activeTab === 'general' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        <SettingsIcon size={16} /> General
                    </button>
                    <button
                        onClick={() => setActiveTab('api_info')}
                        className={`px-3 py-2 rounded transition-colors flex items-center gap-2 ${activeTab === 'api_info' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Server size={16} /> API Info
                    </button>
                    <button
                        onClick={() => setActiveTab('setup_guide')}
                        className={`px-3 py-2 rounded transition-colors flex items-center gap-2 ${activeTab === 'setup_guide' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Book size={16} /> Setup Guide
                    </button>
                    <button
                        onClick={() => setActiveTab('extension')}
                        className={`px-3 py-2 rounded transition-colors flex items-center gap-2 ${activeTab === 'extension' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Plug size={16} /> Browser Extension
                    </button>
                    <button
                        onClick={() => setActiveTab('security')}
                        className={`px-3 py-2 rounded transition-colors flex items-center gap-2 ${activeTab === 'security' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Shield size={16} /> Security
                    </button>
                    <button
                        onClick={() => setActiveTab('mobile')}
                        className={`px-3 py-2 rounded transition-colors flex items-center gap-2 ${activeTab === 'mobile' ? 'bg-cyber-purple/20 text-cyber-neon' : 'text-gray-400 hover:text-white'}`}
                    >
                        <Smartphone size={16} /> Smartphone
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
                    {loading && activeTab === 'general' ? (
                        <div className="text-center py-8 text-cyber-neon animate-pulse">Loading Configuration...</div>
                    ) : (
                        <>
                            {activeTab === 'mobile' && (
                                <div className="space-y-6">
                                    <div className="bg-black/40 p-4 rounded-lg border border-gray-800">
                                        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                                            <Smartphone size={20} className="text-cyber-neon" /> 1. Install App (PWA)
                                        </h3>
                                        <p className="text-gray-400 text-sm mb-4">
                                            Install this interface as a native app on your phone to get full screen experience and "Share to JDownloader" feature.
                                        </p>
                                        <ol className="list-decimal list-inside text-gray-300 text-sm space-y-2 ml-2">
                                            <li>Open this page in <b>Chrome</b> (Android) or <b>Safari</b> (iOS).</li>
                                            <li>Tap the browser menu (Three dots or Share icon).</li>
                                            <li>Select <b>"Add to Home Screen"</b> or "Install App".</li>
                                            <li>Usage: While browsing, tap <b>Share</b> &rarr; <b>JDownloader Manager</b> to add links properly.</li>
                                        </ol>
                                    </div>

                                    <div className="bg-black/40 p-4 rounded-lg border border-gray-800">
                                        <h3 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                                            <Plug size={20} className="text-cyber-neon" /> 2. Enable Click'n'Load (Android)
                                        </h3>
                                        <p className="text-gray-400 text-sm mb-4">
                                            Standard Chrome on Android blocks extensions. To use Click'n'Load buttons, you need <b>Microsoft Edge Canary</b>.
                                        </p>

                                        <div className="space-y-4">
                                            <div className="border-l-2 border-cyber-purple pl-4">
                                                <h4 className="font-bold text-white text-sm mb-1">Step A: Prepare Edge Canary</h4>
                                                <ul className="list-disc list-inside text-gray-400 text-xs space-y-1">
                                                    <li>Install "Microsoft Edge Canary" from Play Store.</li>
                                                    <li>Go to <code>edge://settings/about</code> via menu.</li>
                                                    <li>Tap "Edge Canary Version" <b>5 times</b> to enable Developer Options.</li>
                                                    <li>Go to <b>Settings</b> &rarr; <b>Developer Options</b> &rarr; Enable "Extension install by crx".</li>
                                                </ul>
                                            </div>

                                            <div className="border-l-2 border-cyber-purple pl-4">
                                                <h4 className="font-bold text-white text-sm mb-1">Step B: Install Plugin</h4>
                                                <p className="text-gray-400 text-xs mb-2">Download the dedicated mobile extension (.crx) below.</p>
                                                <a
                                                    href={api.defaults.baseURL ? `${api.defaults.baseURL}/extension/edge.zip` : '/api/v1/extension/edge.zip'}
                                                    download="edge.zip"
                                                    className="inline-flex items-center gap-2 px-3 py-2 bg-cyber-purple/20 hover:bg-cyber-purple/40 text-cyber-neon rounded transition-colors text-sm border border-cyber-purple/50"
                                                >
                                                    <Download size={16} /> Download Extension (.zip)
                                                </a>
                                                <p className="text-gray-500 text-[10px] mt-2 mb-4">
                                                    <strong>Important:</strong> Unzip the downloaded file first! Then open Edge Canary &rarr; Developer Options &rarr; "Extension install by crx" &rarr; Select the extracted <code>edge.crx</code> file.
                                                </p>

                                                <h4 className="font-bold text-white text-sm mb-1">Step C: Configuration</h4>
                                                <div className="bg-black/20 p-3 rounded border border-white/5">
                                                    <p className="text-xs text-gray-400 mb-1">Server URL:</p>
                                                    <code className="block bg-black/50 px-2 py-1 rounded text-cyber-neon text-xs mb-3 font-mono break-all border border-gray-800">
                                                        {window.location.origin}
                                                    </code>

                                                    <p className="text-xs text-gray-400 mb-1">Browser Auth Token:</p>
                                                    <div className="flex items-center gap-2">
                                                        <code className="bg-black/50 px-2 py-1 rounded text-cyber-neon text-xs flex-1 font-mono break-all border border-gray-800">
                                                            {localStorage.getItem('token') || 'Login required'}
                                                        </code>
                                                        <button
                                                            onClick={() => {
                                                                navigator.clipboard.writeText(localStorage.getItem('token') || '');
                                                                setCopiedToken(true);
                                                                setTimeout(() => setCopiedToken(false), 2000);
                                                            }}
                                                            className="p-1.5 bg-cyber-purple/20 hover:bg-cyber-purple/40 rounded text-cyber-neon transition-colors"
                                                            title="Copy Token"
                                                        >
                                                            {copiedToken ? <Check size={14} /> : <Copy size={14} />}
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}
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

                                    {!settings.use_mock && (
                                        <div className="text-xs text-yellow-500 bg-yellow-500/10 p-2 rounded mt-2">
                                            Note: Ensure your JDownloader has the Remote Control extension enabled on port {settings.jd_port}.
                                        </div>
                                    )}

                                    {/* Admin Password removed from General tab */}
                                    <div className="border-t border-gray-700 pt-4 pb-2 flex items-center justify-between">
                                        <span className="text-sm text-gray-300 font-bold">Enable Default Download Path</span>
                                        <button
                                            onClick={() => setSettings({ ...settings, use_default_download_path: !settings.use_default_download_path })}
                                            className={`w-12 h-6 rounded-full transition-colors relative ${settings.use_default_download_path ? 'bg-cyber-neon' : 'bg-gray-700'}`}
                                        >
                                            <div className={`w-4 h-4 rounded-full bg-white absolute top-1 transition-all ${settings.use_default_download_path ? 'left-7' : 'left-1'}`} />
                                        </button>
                                    </div>

                                    {settings.use_default_download_path && (
                                        <div className="animate-in fade-in slide-in-from-top-2 space-y-2 mb-4">
                                            <label className="block text-sm text-gray-400 mb-1">Default Download Path</label>
                                            <div className="glass-input-wrapper">
                                                <div className="absolute inset-0 z-0 bg-transparent"
                                                    style={{
                                                        animation: `border-rotate ${5 + Math.random() * 2}s linear infinite`,
                                                        animationDelay: `-${Math.random() * 5}s`
                                                    }}
                                                />
                                                <input
                                                    type="text"
                                                    value={settings.default_download_path || ''}
                                                    onChange={e => setSettings({ ...settings, default_download_path: e.target.value })}
                                                    className="glass-input p-2"
                                                    placeholder="/downloads/<jd:packagename>"
                                                />
                                            </div>
                                            <div className="text-xs text-gray-400 mt-2 p-3 bg-gray-800/50 rounded border border-gray-700">
                                                <p className="font-bold mb-2 text-gray-300">Supported variables:</p>
                                                <div className="grid grid-cols-1 gap-1 text-cyber-neon/80 font-mono pl-2">
                                                    <span>&lt;jd:packagename&gt;</span>
                                                    <span>&lt;jd:simpledate&gt;</span>
                                                    <span>&lt;jd:orgsource&gt;</span>
                                                </div>
                                            </div>
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
                                    <div className="flex bg-gray-900 p-1 rounded-lg border border-gray-700 shrink-0">
                                        <button
                                            onClick={() => setApiInfoMode('raw')}
                                            className={`flex-1 py-1.5 text-xs font-medium rounded transition-all ${apiInfoMode === 'raw' ? 'bg-gray-700 text-white shadow' : 'text-gray-500 hover:text-gray-300'}`}
                                        >
                                            Raw Help (Internal)
                                        </button>
                                        <button
                                            onClick={() => setApiInfoMode('docs')}
                                            className={`flex-1 py-1.5 text-xs font-medium rounded transition-all ${apiInfoMode === 'docs' ? 'bg-cyber-purple text-white shadow' : 'text-gray-500 hover:text-gray-300'}`}
                                        >
                                            Knowledge Base (Reference)
                                        </button>
                                    </div>

                                    {apiInfoMode === 'raw' ? (
                                        <>
                                            <p className="text-sm text-gray-400 shrink-0">Response from JDownloader <code>/help</code> endpoint:</p>
                                            <div className="flex-1 min-h-0 bg-gray-950 rounded-lg border border-gray-800 overflow-hidden">
                                                <pre className="h-full p-4 text-xs text-green-400 font-mono overflow-auto scrollbar-thin scrollbar-thumb-cyber-purple/20 whitespace-pre-wrap">
                                                    {helpContent || 'Loading or empty response...'}
                                                </pre>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="flex-1 min-h-0 bg-gray-900/50 rounded-lg border border-gray-800 overflow-hidden p-4 overflow-y-auto custom-scrollbar">
                                            {loading ? <div className="animate-pulse text-cyber-neon">Loading docs...</div> : <SimpleMarkdown content={docsContent} />}
                                        </div>
                                    )}
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
                                        <li>Disable the setting: <code className="bg-gray-800 px-1 rounded text-red-400">RemoteAPI: Deprecated Api Localhost Only</code>.</li>
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
                                        <div className="flex items-center gap-2 mb-2">
                                            <Plug className="text-cyber-neon" size={20} />
                                            <h3 className="text-lg font-bold text-white neon-text">Remote Click'n'Load</h3>
                                        </div>
                                        <p className="text-gray-400">
                                            Use this browser extension to send Click'n'Load links from <strong>any computer</strong> to your JDownloader Manager server.
                                        </p>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-white mb-3 flex items-center gap-2"><Download size={16} /> Download</h4>
                                        <a
                                            href={api.defaults.baseURL ? `${api.defaults.baseURL}/browser-extension.zip` : '/browser-extension.zip'}
                                            download="jd-manager-cnl-bridge.zip"
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-2 px-6 py-3 bg-cyber-purple hover:bg-cyber-purple/80 text-white font-bold rounded-lg transition-all shadow-lg hover:shadow-cyan-500/20"
                                        >
                                            <Download size={18} /> Download Extension (.zip)
                                        </a>
                                        <p className="text-xs text-gray-500 mt-2">Compatible with Chrome, Edge, Brave (Chromium-based browsers)</p>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-white mb-3 flex items-center gap-2"><SettingsIcon size={16} /> Installation</h4>
                                        <ol className="list-decimal list-inside space-y-2 marker:text-cyber-neon pl-2">
                                            <li>Extract the downloaded .zip file</li>
                                            <li>Open <code className="bg-gray-800 px-1 rounded">chrome://extensions/</code> in your browser</li>
                                            <li>Enable <strong>"Developer mode"</strong> (top right toggle)</li>
                                            <li>Click <strong>"Load unpacked"</strong></li>
                                            <li>Select the extracted folder</li>
                                        </ol>
                                    </div>

                                    <div>
                                        <h4 className="font-semibold text-white mb-3 flex items-center gap-2"><SettingsIcon size={16} /> Configuration</h4>
                                        <ol className="list-decimal list-inside space-y-2 marker:text-cyber-neon pl-2">
                                            <li>Click the extension icon in your toolbar</li>
                                            <li>Enter your <strong>Server URL</strong>: <code className="bg-gray-800 px-1 rounded text-cyber-neon">{window.location.origin}</code></li>
                                            <li>
                                                <div className="flex flex-col gap-1 mt-1 mb-2">
                                                    <span>Enter your <strong>Auth Token</strong>:</span>
                                                    <div className="flex items-center gap-2">
                                                        <code className="bg-gray-800 px-3 py-2 rounded text-cyber-neon text-xs break-all flex-1 border border-gray-700 font-mono">
                                                            {localStorage.getItem('token') || 'No token found (please login first)'}
                                                        </code>
                                                        <button
                                                            onClick={() => {
                                                                navigator.clipboard.writeText(localStorage.getItem('token') || '');
                                                                setCopiedToken(true);
                                                                setTimeout(() => setCopiedToken(false), 2000);
                                                            }}
                                                            className="p-2 bg-cyber-purple/20 hover:bg-cyber-purple/40 rounded text-cyber-neon transition-colors"
                                                            title="Copy Token"
                                                        >
                                                            {copiedToken ? <Check size={14} /> : <Copy size={14} />}
                                                        </button>
                                                    </div>
                                                </div>
                                            </li>
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

                            {activeTab === 'security' && (
                                <SecurityTabContent />
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};
