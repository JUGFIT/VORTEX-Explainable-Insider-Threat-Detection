import React, { useState } from 'react';
import Layout from '../components/Layout/Layout';
import {
    Settings as SettingsIcon,
    Shield,
    Bell,
    Database,
    User,
    Activity,
    Save,
    RefreshCw,
    Edit,
    AlertTriangle
} from 'lucide-react';

const Settings = () => {
    const [saving, setSaving] = useState(false);
    const [isEditingThresholds, setIsEditingThresholds] = useState(false);
    const [showEditWarning, setShowEditWarning] = useState(false);
    const [config, setConfig] = useState({
        anomalyThreshold: 0.15,
        alertFrequency: 'Immediate',
        dataRetention: 90,
        enableAutoRetrain: true,
        notificationEmails: 'security@vortex-defense.com',
        riskThresholds: {
            medium: 0.20,
            high: 0.40,
            critical: 0.70
        }
    });
    const [showFreqDropdown, setShowFreqDropdown] = useState(false);

    const handleSave = () => {
        setSaving(true);
        setTimeout(() => setSaving(false), 800);
    };

    return (
        <Layout title="System Settings">
            {/* Warning Popup */}
            {showEditWarning && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="bg-[#1a1f26] border border-red-500/30 w-[420px] p-6 rounded-xl shadow-2xl animate-fade-in-up">
                        <div className="flex items-center gap-3 mb-4 text-red-500">
                            <AlertTriangle size={24} />
                            <h3 className="text-lg font-bold">Warning: Core System Edit</h3>
                        </div>
                        <p className="text-sm text-gray-300 leading-relaxed mb-6">
                            Changing risk thresholds directly alters the core detection engine logic. Incorrect bounds may cause a flood of false anomalies or suppress critical threats.
                            <br /><br />
                            Are you sure you wish to continue modifying these parameters?
                        </p>
                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => setShowEditWarning(false)}
                                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg text-sm transition-colors font-medium"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => {
                                    setShowEditWarning(false);
                                    setIsEditingThresholds(true);
                                }}
                                className="px-4 py-2 bg-red-600/90 hover:bg-red-500 text-white font-bold rounded-lg text-sm transition-colors shadow-lg shadow-red-900/20"
                            >
                                Yes, Enable Edit
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="max-w-4xl space-y-6">
                {/* Detection Parameters */}
                <div className="card">
                    <div className="flex items-center gap-2 mb-6 text-white">
                        <Shield className="w-5 h-5 text-vortex-accent" />
                        <h3 className="text-lg font-bold">Detection Parameters</h3>
                    </div>

                    <div>
                        <div className="space-y-4">
                            <div className="flex justify-between items-start">
                                <div className="flex flex-col">
                                    <label className="text-sm font-semibold text-gray-400">Event Risk Sensitivity Thresholds</label>
                                    <span className="text-xs text-gray-500">Adjust the intensity boundaries for simulated and detected events.</span>
                                </div>
                                {!isEditingThresholds ? (
                                    <button
                                        onClick={() => setShowEditWarning(true)}
                                        className="btn-secondary py-1.5 px-3 flex items-center gap-2 text-xs h-[32px] text-gray-300 hover:text-white"
                                    >
                                        <Edit size={14} />
                                        <span>Change Thresholds</span>
                                    </button>
                                ) : (
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setIsEditingThresholds(false)}
                                            className="btn-secondary py-1.5 px-3 flex items-center gap-2 text-xs h-[32px] text-gray-400 hover:text-gray-200"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            onClick={() => {
                                                setSaving(true);
                                                setTimeout(() => {
                                                    setSaving(false);
                                                    setIsEditingThresholds(false);
                                                }, 800);
                                            }}
                                            className="btn-primary py-1.5 px-3 flex items-center gap-2 text-xs h-[32px]"
                                        >
                                            <Save size={14} />
                                            <span>{saving ? 'Saving...' : 'Save Changes'}</span>
                                        </button>
                                    </div>
                                )}
                            </div>

                            <div className={`grid grid-cols-1 md:grid-cols-3 gap-6 transition-opacity duration-300 ${!isEditingThresholds ? 'opacity-50 grayscale-[50%]' : ''}`}>
                                {/* Medium Threshold */}
                                <div className={`space-y-2 p-4 rounded-lg border ${isEditingThresholds ? 'bg-gray-800/20 border-yellow-500/20' : 'bg-gray-900/50 border-gray-700/50'}`}>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className={`${isEditingThresholds ? 'text-yellow-500' : 'text-gray-400'} font-bold`}>Medium Risk</span>
                                        <span className={`font-mono px-2 py-0.5 rounded ${isEditingThresholds ? 'bg-gray-800 text-white' : 'bg-gray-800 text-gray-400'}`}>{config.riskThresholds.medium.toFixed(2)}</span>
                                    </div>
                                    <input
                                        type="range" min="0.05" max={config.riskThresholds.high - 0.05} step="0.05"
                                        value={config.riskThresholds.medium}
                                        onChange={(e) => setConfig({ ...config, riskThresholds: { ...config.riskThresholds, medium: parseFloat(e.target.value) } })}
                                        disabled={!isEditingThresholds}
                                        className="w-full accent-yellow-500 disabled:cursor-not-allowed"
                                    />
                                    <div className="text-2xs text-gray-500 flex justify-between">
                                        <span>0.05</span>
                                        <span>{(config.riskThresholds.high - 0.05).toFixed(2)}</span>
                                    </div>
                                </div>

                                {/* High Threshold */}
                                <div className={`space-y-2 p-4 rounded-lg border ${isEditingThresholds ? 'bg-gray-800/20 border-orange-500/20' : 'bg-gray-900/50 border-gray-700/50'}`}>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className={`${isEditingThresholds ? 'text-orange-500' : 'text-gray-400'} font-bold`}>High Risk</span>
                                        <span className={`font-mono px-2 py-0.5 rounded ${isEditingThresholds ? 'bg-gray-800 text-white' : 'bg-gray-800 text-gray-400'}`}>{config.riskThresholds.high.toFixed(2)}</span>
                                    </div>
                                    <input
                                        type="range" min={config.riskThresholds.medium + 0.05} max={config.riskThresholds.critical - 0.05} step="0.05"
                                        value={config.riskThresholds.high}
                                        onChange={(e) => setConfig({ ...config, riskThresholds: { ...config.riskThresholds, high: parseFloat(e.target.value) } })}
                                        disabled={!isEditingThresholds}
                                        className="w-full accent-orange-500 disabled:cursor-not-allowed"
                                    />
                                    <div className="text-2xs text-gray-500 flex justify-between">
                                        <span>{(config.riskThresholds.medium + 0.05).toFixed(2)}</span>
                                        <span>{(config.riskThresholds.critical - 0.05).toFixed(2)}</span>
                                    </div>
                                </div>

                                {/* Critical Threshold */}
                                <div className={`space-y-2 p-4 rounded-lg border ${isEditingThresholds ? 'bg-gray-800/20 border-red-500/20' : 'bg-gray-900/50 border-gray-700/50'}`}>
                                    <div className="flex justify-between items-center text-sm">
                                        <span className={`${isEditingThresholds ? 'text-red-500' : 'text-gray-400'} font-bold`}>Critical Risk</span>
                                        <span className={`font-mono px-2 py-0.5 rounded ${isEditingThresholds ? 'bg-gray-800 text-white' : 'bg-gray-800 text-gray-400'}`}>{config.riskThresholds.critical.toFixed(2)}</span>
                                    </div>
                                    <input
                                        type="range" min={config.riskThresholds.high + 0.05} max="0.95" step="0.05"
                                        value={config.riskThresholds.critical}
                                        onChange={(e) => setConfig({ ...config, riskThresholds: { ...config.riskThresholds, critical: parseFloat(e.target.value) } })}
                                        disabled={!isEditingThresholds}
                                        className="w-full accent-red-500 disabled:cursor-not-allowed"
                                    />
                                    <div className="text-2xs text-gray-500 flex justify-between">
                                        <span>{(config.riskThresholds.high + 0.05).toFixed(2)}</span>
                                        <span>0.95</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Data Management */}
                <div className="card">
                    <div className="flex items-center gap-2 mb-6 text-white">
                        <Database className="w-5 h-5 text-blue-400" />
                        <h3 className="text-lg font-bold">Data Management</h3>
                    </div>

                    <div className="space-y-8">
                        <div>
                            <label className="text-sm font-semibold text-gray-400">Retention Period (Days)</label>
                            <div className="flex items-center gap-4 mt-2">
                                <input
                                    type="number"
                                    value={config.dataRetention}
                                    onChange={(e) => setConfig({ ...config, dataRetention: parseInt(e.target.value) })}
                                    className="bg-vortex-dark border border-gray-700 rounded-lg text-sm text-white px-4 py-2 w-24 focus:border-vortex-accent"
                                />
                                <span className="text-xs text-gray-500">Historical logs will be purged after {config.dataRetention} days.</span>
                            </div>
                        </div>

                        {/* Simulation Purge Section */}
                        <div className="pt-6 border-t border-gray-800">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div>
                                    <h4 className="text-sm font-bold text-gray-200">Purge Simulated Data</h4>
                                    <p className="text-xs text-gray-500 mt-1 max-w-md">
                                        Permanently remove all telemetry generated through the Event Log Generator from the CSV records.
                                        This will reset the dataset to its base synthetic state.
                                    </p>
                                </div>
                                <button
                                    onClick={async () => {
                                        if (window.confirm("Are you sure you want to permanently delete ALL simulated events from the CSV storage? This cannot be undone.")) {
                                            try {
                                                setSaving(true);
                                                const { purgeSimulatedEvents } = await import('../services/api');
                                                const result = await purgeSimulatedEvents();
                                                alert(`Success: ${result.message}`);
                                                window.dispatchEvent(new Event('refreshDashboard'));
                                            } catch (err) {
                                                alert("Failed to purge events: " + (err.message || "Unknown error"));
                                            } finally {
                                                setSaving(false);
                                            }
                                        }
                                    }}
                                    className="px-6 py-2.5 bg-red-500/10 border border-red-500/30 text-red-500 hover:bg-red-500 hover:text-white rounded-lg text-sm font-bold transition-all whitespace-nowrap"
                                >
                                    Purge Simulated Events
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </Layout>
    );
};

export default Settings;
