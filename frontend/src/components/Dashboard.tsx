import React, { useEffect, useState } from 'react';
import { api, type Package } from '../api/client';
import { Play, Pause, Plus, Download, Settings, LogOut, FolderInput, FileUp } from 'lucide-react';
import { SettingsModal } from './SettingsModal';

// Buffer types
interface BufferPackage {
    package: string;
    links: string[];
    passwords?: string;
}

interface DlcFile {
    filename: string;
    size: number;
    timestamp: number;
}

// Helper for type-safe error handling
const getErrorMessage = (error: unknown): string => {
    if (error && typeof error === 'object' && 'response' in error) {
        const resp = error as { response?: { data?: { message?: string; detail?: string } } };
        return resp.response?.data?.message || resp.response?.data?.detail || 'Unknown error';
    }
    if (error instanceof Error) return error.message;
    return String(error);
};

export const Dashboard: React.FC = () => {
    const [packages, setPackages] = useState<Package[]>([]);
    const [linkGrabberPackages, setLinkGrabberPackages] = useState<Package[]>([]);
    const [activeTab, setActiveTab] = useState<'downloads' | 'linkgrabber'>(() => {
        return (localStorage.getItem('activeTab') as 'downloads' | 'linkgrabber') || 'downloads';
    });

    useEffect(() => {
        localStorage.setItem('activeTab', activeTab);
    }, [activeTab]);
    const [newLinks, setNewLinks] = useState('');
    const [settingsOpen, setSettingsOpen] = useState(false);
    const [expandedPackages, setExpandedPackages] = useState<Set<string>>(new Set());

    const togglePackage = (uuid: string) => {
        const newSet = new Set(expandedPackages);
        if (newSet.has(uuid)) {
            newSet.delete(uuid);
        } else {
            newSet.add(uuid);
        }
        setExpandedPackages(newSet);
    };

    const [contextMenu, setContextMenu] = useState<{
        visible: boolean;
        x: number;
        y: number;
        packageId: string | null;
    }>({ visible: false, x: 0, y: 0, packageId: null });

    // Close context menu on click elsewhere
    useEffect(() => {
        const handleClick = () => setContextMenu({ ...contextMenu, visible: false });
        document.addEventListener('click', handleClick);
        return () => document.removeEventListener('click', handleClick);
    }, [contextMenu]);



    const [bufferCount, setBufferCount] = useState(0);
    const [bufferExpanded, setBufferExpanded] = useState(false);
    const [bufferDetails, setBufferDetails] = useState<{ packages: BufferPackage[], dlc_files: DlcFile[] }>({ packages: [], dlc_files: [] });

    const [isConnected, setIsConnected] = useState(false);

    const fetchBufferDetails = async () => {
        try {
            const res = await api.get('/buffer/details');
            setBufferDetails(res.data);
        } catch (error) {
            console.error("Failed to fetch buffer details", error);
        }
    };

    const fetchStatus = async () => {
        try {
            const res = await api.get('/system/status');
            setBufferCount(res.data.buffer_count);
            setIsConnected(res.data.jd_online);
        } catch {
            setIsConnected(false);
        }
    };

    // Initial fetch of package data
    const fetchData = async () => {
        try {
            if (activeTab === 'downloads') {
                const res = await api.get('/downloads');
                setPackages(res.data);
            } else {
                const res = await api.get('/linkgrabber');
                setLinkGrabberPackages(res.data);
            }
        } catch (error) {
            console.error("Failed to fetch packages", error);
            // Don't set connected false here, rely on status endpoint
        }
    };

    useEffect(() => {
        fetchData();
        fetchStatus();
        fetchBufferDetails();
        const interval = setInterval(() => {
            fetchData();
            fetchStatus();
            fetchBufferDetails();
        }, 2000);
        return () => clearInterval(interval);
    }, [activeTab]);

    const handleAddLinks = async () => {
        if (!newLinks) return;
        try {
            await api.post('/downloads/links', newLinks.split('\n').filter(l => l.trim()));
            setNewLinks('');
            // Switch to LinkGrabber to see result, as they usually go there first
            setActiveTab('linkgrabber');
        } catch (error: unknown) {
            console.error("Failed to add links", error);
            alert(`Failed to Add Links: ${getErrorMessage(error)}`);
        }
    };

    const handleStart = async () => {
        try {
            if (activeTab === 'downloads') {
                await api.post('/downloads/start');
                alert('Downloads Started');
            } else {
                // Confirm all in LinkGrabber
                await api.post('/linkgrabber/confirm-all');
                alert('All LinkGrabber Items Moved to Downloads');
                // Optimistically switch to downloads
                setActiveTab('downloads');
            }
        } catch (e: unknown) {
            alert(`Action Failed: ${getErrorMessage(e)}`);
            console.error(e);
        }
    };

    const handleStop = async () => {
        await api.post('/downloads/stop');
        alert('Downloads Stopped');
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        window.location.reload();
    };

    const handleContextMenu = (e: React.MouseEvent, pkgId: string) => {
        e.preventDefault();
        setContextMenu({
            visible: true,
            x: e.pageX,
            y: e.pageY,
            packageId: pkgId
        });
    };

    const handleMoveToDl = async () => {
        if (contextMenu.packageId) {
            try {
                await api.post('/linkgrabber/move', [contextMenu.packageId]);
                setContextMenu({ ...contextMenu, visible: false });
                alert('Package Moved to Downloads');
                fetchData(); // Soft refresh
            } catch (e: unknown) {
                alert(`Move Failed: ${getErrorMessage(e)}`);
            }
        }
    };

    const handleSetDirectory = async () => {
        if (contextMenu.packageId) {
            const dir = prompt("Enter Download Directory:\n\nSupported variables:\n<jd:packagename>\n<jd:simpledate>\n<jd:orgsource>\n\nExample: /home/downloads/<jd:packagename>");
            if (dir) {
                try {
                    await api.post('/linkgrabber/set-directory', {
                        packageIds: [contextMenu.packageId],
                        directory: dir
                    });
                    setContextMenu({ ...contextMenu, visible: false });
                    alert('Directory Updated');
                    fetchData();
                } catch (e: unknown) {
                    alert(`Update Failed: ${getErrorMessage(e)}`);
                }
            }
        }
    };

    const handleDelete = async () => {
        if (contextMenu.packageId) {
            try {
                const endpoint = activeTab === 'downloads' ? '/downloads/delete' : '/linkgrabber/delete';
                await api.post(endpoint, [contextMenu.packageId]);
                alert('Package Deleted');
                setContextMenu({ ...contextMenu, visible: false });
                fetchData(); // Soft refresh, no reload
            } catch (e: unknown) {
                alert(`Delete Failed: ${getErrorMessage(e)}`);
                console.error(e);
            }
        }
    };

    const currentList = activeTab === 'downloads' ? packages : linkGrabberPackages;

    return (
        <div className="min-h-screen p-8 text-gray-200 font-sans relative overflow-hidden">
            {/* Background elements preserved by outer layout usually, assuming standalone component structure here */}
            {/* Grid Background */}
            <div className="fixed inset-0 cyber-grid z-0 pointer-events-none" />

            <div className="relative z-10 max-w-6xl mx-auto">
                <header className="flex justify-between items-center mb-10 bg-cyber-card/80 backdrop-blur-md p-6 rounded-2xl border border-gray-800 shadow-2xl relative z-50">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 flex items-center justify-center">
                            <img src="/logo.png" alt="ER-j-Manager Logo" className="w-full h-full object-contain filter drop-shadow-[0_0_5px_rgba(236,72,153,0.5)]" />
                        </div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyber-neon to-cyber-purple neon-text tracking-wider">
                            JDownloader Manager
                        </h1>
                    </div>
                    <div className="flex gap-4">
                        <div className="flex items-center bg-gray-800 rounded-lg p-1 border border-gray-700">
                            <button
                                onClick={() => setActiveTab('downloads')}
                                className={`px-4 py-2 rounded-md transition-all ${activeTab === 'downloads' ? 'bg-cyber-purple text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                            >
                                Downloads
                            </button>
                            <button
                                onClick={() => setActiveTab('linkgrabber')}
                                className={`px-4 py-2 rounded-md transition-all ${activeTab === 'linkgrabber' ? 'bg-cyber-purple text-white shadow-lg' : 'text-gray-400 hover:text-white'}`}
                            >
                                LinkGrabber
                            </button>
                        </div>

                        <button onClick={handleStart} className="flex items-center gap-2 px-4 py-2 bg-cyber-neon/10 text-cyber-neon border border-cyber-neon rounded hover:bg-cyber-neon/20 transition-all shadow-[0_0_10px_rgba(34,211,238,0.2)]">
                            <Play size={18} /> Start All
                        </button>
                        <button onClick={handleStop} className="flex items-center gap-2 px-4 py-2 bg-red-500/10 text-red-400 border border-red-500 rounded hover:bg-red-500/20 transition-all">
                            <Pause size={18} /> Stop All
                        </button>
                        <button onClick={() => setSettingsOpen(true)} className="p-2 bg-gray-700/50 text-gray-300 border border-gray-600 rounded hover:bg-gray-700 hover:text-cyber-neon transition-all">
                            <Settings size={20} />
                        </button>
                        <div className="flex items-center bg-gray-900/50 rounded-full px-4 py-2 border border-gray-700 mx-4" title={isConnected ? "JDownloader Online" : "JDownloader Offline - Buffering Mode"}>
                            <div className={`w-3 h-3 rounded-full mr-2 ${isConnected ? "bg-green-500 shadow-[0_0_8px_#22c55e]" : "bg-red-500 shadow-[0_0_8px_#ef4444] animate-pulse"}`}></div>
                            <span className={`text-sm font-medium ${isConnected ? "text-green-400" : "text-red-400"}`}>
                                {isConnected ? "JD Online" : "JD Offline"}
                            </span>
                        </div>

                        <button onClick={handleLogout} className="p-2 bg-red-500/10 text-red-400 border border-red-500/50 rounded hover:bg-red-500/20 hover:text-red-200 transition-all" title="Logout">
                            <LogOut size={20} />
                        </button>
                    </div>
                </header>

                {/* Buffer Section */}
                {bufferCount > 0 && (
                    <div className="mb-6">
                        <div
                            className="p-4 bg-yellow-500/10 border border-yellow-500/50 rounded-xl cursor-pointer"
                            onClick={() => setBufferExpanded(!bufferExpanded)}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3 text-yellow-500">
                                    <div className="w-2 h-2 rounded-full bg-yellow-500 animate-ping" />
                                    <span className="font-semibold">⚠️ {bufferCount} Items waiting for JDownloader Connection</span>
                                    <span className="text-sm text-yellow-400/70">(click to {bufferExpanded ? 'collapse' : 'expand'})</span>
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={async (e) => {
                                            e.stopPropagation();
                                            try {
                                                const res = await api.post('/system/buffer/replay');
                                                alert(`Replay triggered. ${res.data.status}`);
                                                fetchStatus();
                                                fetchData();
                                                fetchBufferDetails();
                                            } catch (e: unknown) {
                                                alert(`Replay Failed: ${getErrorMessage(e)}`);
                                            }
                                        }}
                                        className="px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/40 text-yellow-500 border border-yellow-500 rounded-lg transition-all"
                                    >
                                        Retry Now
                                    </button>
                                    <button
                                        onClick={async (e) => {
                                            e.stopPropagation();
                                            if (confirm('Clear entire buffer? This cannot be undone.')) {
                                                try {
                                                    await api.delete('/buffer/clear');
                                                    fetchStatus();
                                                    fetchBufferDetails();
                                                } catch (e: unknown) {
                                                    alert(`Clear Failed: ${getErrorMessage(e)}`);
                                                }
                                            }
                                        }}
                                        className="px-4 py-2 bg-red-500/20 hover:bg-red-500/40 text-red-400 border border-red-500 rounded-lg transition-all"
                                    >
                                        Clear All
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Expanded Buffer Details */}
                        {bufferExpanded && (
                            <div className="mt-2 p-4 bg-gray-900/50 border border-gray-700 rounded-xl space-y-3 max-h-96 overflow-y-auto">
                                {bufferDetails.packages.map((pkg, index: number) => (
                                    <div key={index} className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <div className="font-semibold text-cyber-neon">{pkg.package || 'Unnamed Package'}</div>
                                                <div className="text-sm text-gray-400 mt-1">
                                                    {pkg.links?.length || 0} links
                                                </div>
                                                <ul className="text-xs text-gray-500 mt-2 space-y-1 max-h-24 overflow-y-auto">
                                                    {pkg.links?.slice(0, 5).map((link: string, i: number) => (
                                                        <li key={i} className="truncate max-w-md">{link}</li>
                                                    ))}
                                                    {pkg.links?.length > 5 && (
                                                        <li className="text-gray-600">...and {pkg.links.length - 5} more</li>
                                                    )}
                                                </ul>
                                            </div>
                                            <button
                                                onClick={async () => {
                                                    try {
                                                        await api.delete(`/buffer/package/${index}`);
                                                        fetchStatus();
                                                        fetchBufferDetails();
                                                    } catch (e: unknown) {
                                                        alert(`Delete Failed: ${getErrorMessage(e)}`);
                                                    }
                                                }}
                                                className="p-1 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded transition-all"
                                                title="Delete Package"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    </div>
                                ))}

                                {bufferDetails.dlc_files.map((dlc) => (
                                    <div key={dlc.filename} className="p-3 bg-gray-800/50 rounded-lg border border-gray-700">
                                        <div className="flex justify-between items-center">
                                            <div>
                                                <div className="font-semibold text-purple-400">📦 {dlc.filename}</div>
                                                <div className="text-sm text-gray-400">
                                                    {(dlc.size / 1024).toFixed(1)} KB
                                                </div>
                                            </div>
                                            <button
                                                onClick={async () => {
                                                    try {
                                                        await api.delete(`/buffer/dlc/${dlc.filename}`);
                                                        fetchStatus();
                                                        fetchBufferDetails();
                                                    } catch (e: unknown) {
                                                        alert(`Delete Failed: ${getErrorMessage(e)}`);
                                                    }
                                                }}
                                                className="p-1 text-red-400 hover:text-red-300 hover:bg-red-500/20 rounded transition-all"
                                                title="Delete DLC"
                                            >
                                                ✕
                                            </button>
                                        </div>
                                    </div>
                                ))}

                                {bufferDetails.packages.length === 0 && bufferDetails.dlc_files.length === 0 && (
                                    <div className="text-gray-500 text-center py-4">Buffer is empty</div>
                                )}
                            </div>
                        )}
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 relative z-0">
                    <div className="lg:col-span-2 space-y-6">
                        <div className="comet-border p-1 overflow-hidden" style={{ '--comet-duration': '12s', '--comet-delay': '-2s' } as React.CSSProperties}>
                            <div className="bg-cyber-card rounded-xl p-4 min-h-[500px]">
                                {currentList.map(pkg => (
                                    <div
                                        key={pkg.uuid}
                                        className="bg-cyber-card border border-gray-800 rounded-xl p-6 hover:border-cyber-purple/50 transition-all shadow-lg group relative overflow-hidden mb-4 cursor-context-menu"
                                        onContextMenu={(e) => handleContextMenu(e, pkg.uuid)}
                                    >
                                        <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-cyber-neon to-cyber-purple opacity-0 group-hover:opacity-100 transition-opacity" />
                                        <div className="flex justify-between items-start mb-4 cursor-pointer" onClick={() => togglePackage(pkg.uuid)}>
                                            <div className="flex items-center gap-3">
                                                <div className={`transition-transform duration-300 ${expandedPackages.has(pkg.uuid) ? 'rotate-90' : ''}`}>
                                                    <Play size={12} className="text-gray-500 fill-gray-500" />
                                                </div>
                                                <div>
                                                    <h3 className="text-xl font-semibold text-white group-hover:text-cyber-neon transition-colors select-none">{pkg.name}</h3>
                                                    <div className="flex items-center gap-2 text-sm text-gray-400 mt-1">
                                                        <span className={`w-2 h-2 rounded-full ${pkg.status === 'RUNNING' ? 'bg-green-500 animate-pulse' : 'bg-gray-500'}`} />
                                                        {pkg.status}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-sm text-gray-400">{(pkg.loaded_bytes / 1024 / 1024).toFixed(2)} MB / {(pkg.total_bytes / 1024 / 1024).toFixed(2)} MB</div>
                                                <div className="text-xs text-cyber-purple mt-1">
                                                    {pkg.links.length} files
                                                </div>
                                            </div>
                                        </div>

                                        {/* Progress Bar */}
                                        <div className="w-full bg-gray-800 rounded-full h-2 overflow-hidden mb-4">
                                            <div
                                                className="bg-gradient-to-r from-cyber-neon to-cyber-purple h-full transition-all duration-500 relative"
                                                style={{ width: `${pkg.total_bytes > 0 ? (pkg.loaded_bytes / pkg.total_bytes) * 100 : 0}%` }}
                                            >
                                                <div className="absolute inset-0 bg-white/20 animate-pulse" />
                                            </div>
                                        </div>

                                        {/* Expanded Links View */}
                                        {expandedPackages.has(pkg.uuid) && (
                                            <div className="mt-4 bg-gray-900/50 rounded-lg p-3 border border-gray-800 space-y-2 animate-in fade-in slide-in-from-top-2">
                                                {pkg.links.map(link => (
                                                    <div key={link.uuid} className="flex justify-between items-center text-xs py-2 border-b border-gray-800 last:border-0 hover:bg-white/5 px-2 rounded - transition-colors">
                                                        <div className="flex items-center gap-2 truncate flex-1 min-w-0">
                                                            <div className={`w-1.5 h-1.5 rounded-full ${link.status === 'FINISHED' ? 'bg-green-500' : 'bg-gray-600'}`} />
                                                            <span className="text-gray-300 truncate" title={link.name}>{link.name}</span>
                                                        </div>
                                                        <div className="text-gray-500 font-mono pl-4 shrink-0">
                                                            {(link.bytes_total / 1024 / 1024).toFixed(2)} MB
                                                        </div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))}
                                {currentList.length === 0 && (
                                    <div className="text-center py-20 text-gray-500 bg-cyber-card/50 rounded-xl border border-dashed border-gray-800">
                                        <Download size={48} className="mx-auto mb-4 opacity-20" />
                                        <p>No packages found in {activeTab === 'downloads' ? 'Downloads' : 'LinkGrabber'}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-6">
                        <div className="comet-border p-1 sticky top-8 overflow-hidden" style={{ '--comet-duration': '8s', '--comet-delay': '-5s' } as React.CSSProperties}>
                            <div className="bg-cyber-card rounded-xl p-6">
                                <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                    <Plus size={20} className="text-cyber-neon" /> Add Links
                                </h3>
                                <textarea
                                    className="w-full bg-gray-900/50 border border-gray-700 rounded-lg p-3 text-sm text-gray-300 focus:border-cyber-purple focus:ring-1 focus:ring-cyber-purple outline-none transition-all resize-none glass-input"
                                    rows={5}
                                    placeholder="Paste links here..."
                                    value={newLinks}
                                    onChange={e => setNewLinks(e.target.value)}
                                />
                                <div className="mt-4 flex gap-4">
                                    <button
                                        onClick={handleAddLinks}
                                        className="flex-1 bg-cyber-purple hover:bg-cyber-purple/80 text-white font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyber-purple/20 hover:shadow-cyber-purple/40 active:scale-95"
                                    >
                                        <Plus size={18} /> Add Links
                                    </button>
                                    <label className="flex-1 bg-cyber-neon/10 hover:bg-cyber-neon/20 text-cyber-neon border border-cyber-neon/30 hover:border-cyber-neon/60 font-bold py-3 rounded-lg transition-all cursor-pointer flex items-center justify-center gap-2 shadow-lg hover:shadow-cyber-neon/20 active:scale-95">
                                        <input type="file" className="hidden" accept=".dlc" onChange={async (e) => {
                                            const file = e.target.files?.[0];
                                            if (!file) return;
                                            try {
                                                const formData = new FormData();
                                                formData.append('file', file);
                                                await api.post('/linkgrabber/add-file', formData, {
                                                    headers: { 'Content-Type': 'multipart/form-data' }
                                                });
                                                alert('DLC Container Added (or Buffered)');
                                                // Switch to LinkGrabber
                                                setActiveTab('linkgrabber');
                                                fetchData();
                                            } catch (err: unknown) {
                                                console.error(err);
                                                alert("Failed to upload DLC");
                                            } finally {
                                                e.target.value = ''; // reset
                                            }
                                        }} />
                                        <FileUp size={18} /> Upload DLC
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />

            {
                contextMenu.visible && (
                    <div
                        className="absolute z-50 bg-gray-900 border border-gray-700 rounded-lg shadow-xl py-2 min-w-[150px] backdrop-blur-md"
                        style={{ top: contextMenu.y, left: contextMenu.x }}
                    >
                        {activeTab === 'linkgrabber' && (
                            <>
                                <button
                                    onClick={handleMoveToDl}
                                    className="w-full text-left px-4 py-2 hover:bg-cyber-purple/20 hover:text-cyber-neon transition-colors flex items-center gap-2"
                                >
                                    <Play size={14} /> Start Download
                                </button>
                                <button
                                    onClick={handleSetDirectory}
                                    className="w-full text-left px-4 py-2 hover:bg-blue-500/20 hover:text-blue-400 transition-colors flex items-center gap-2"
                                >
                                    <FolderInput size={14} /> Set Path
                                </button>
                            </>
                        )}
                        <button
                            className="w-full text-left px-4 py-2 hover:bg-red-500/20 hover:text-red-400 transition-colors flex items-center gap-2"
                            onClick={handleDelete}
                        >
                            <LogOut size={14} className="rotate-180" /> Delete
                        </button>
                    </div>
                )
            }
        </div >
    );
};
