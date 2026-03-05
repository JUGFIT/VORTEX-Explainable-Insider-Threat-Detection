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
    RefreshCw
} from 'lucide-react';

const Settings = () => {
    const [saving, setSaving] = useState(false);
    const [config, setConfig] = useState({
        anomalyThreshold: 0.15,
        alertFrequency: 'Immediate',
        dataRetention: 90,
        enableAutoRetrain: true,
        notificationEmails: 'security@vortex-defense.com'
    });
    const [showFreqDropdown, setShowFreqDropdown] = useState(false);

    const handleSave = () => {
        setSaving(true);
        setTimeout(() => setSaving(false), 800);
    };

    return (
        <Layout title="System Settings" subtitle="Configure VORTEX detection parameters and system behavior">
            <div className="max-w-4xl space-y-6">
                {/* Detection Parameters */}
                <div className="card">
                    <div className="flex items-center gap-2 mb-6 text-white">
                        <Shield className="w-5 h-5 text-vortex-accent" />
                        <h3 className="text-lg font-bold">Detection Parameters</h3>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-400">Anomaly Confidence Threshold</label>
                            <div className="flex items-center gap-4">
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.05"
                                    value={config.anomalyThreshold}
                                    onChange={(e) => setConfig({ ...config, anomalyThreshold: parseFloat(e.target.value) })}
                                    className="flex-1 accent-vortex-accent"
                                />
                                <span className="text-sm font-mono text-white bg-gray-800 px-3 py-1 rounded border border-gray-700">
                                    {config.anomalyThreshold.toFixed(2)}
                                </span>
                            </div>
                            <p className="text-[10px] text-gray-500 italic">Lower values increase sensitivity (more alerts).</p>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-gray-400">Model Retraining Strategy</label>
                            <div className="flex items-center gap-3">
                                <button className="flex-1 py-2 px-4 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white hover:border-vortex-accent transition-all flex items-center justify-center gap-2">
                                    <RefreshCw className="w-4 h-4" />
                                    Force Retrain Now
                                </button>
                                <div className="flex items-center gap-2">
                                    <div className={`w-3 h-3 rounded-full ${config.enableAutoRetrain ? 'bg-green-500 animate-pulse' : 'bg-gray-600'}`} />
                                    <span className="text-xs text-gray-300">Auto-Active</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Notifications */}
                <div className="card">
                    <div className="flex items-center gap-2 mb-6 text-white">
                        <Bell className="w-5 h-5 text-orange-400" />
                        <h3 className="text-lg font-bold">Health & Notifications</h3>
                    </div>

                    <div className="space-y-6">
                        <div className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl border border-gray-800">
                            <div>
                                <h4 className="text-sm font-bold text-gray-200">System Alert Frequency</h4>
                                <p className="text-xs text-gray-500 mt-0.5">How often you want to receive digest emails.</p>
                            </div>
                            <div className="relative">
                                <button
                                    onClick={() => setShowFreqDropdown(!showFreqDropdown)}
                                    className="bg-vortex-darker border border-gray-700 rounded-lg text-sm text-white px-4 py-2 hover:border-vortex-accent cursor-pointer flex items-center justify-between min-w-[160px] transition-all"
                                >
                                    <span>{config.alertFrequency}</span>
                                    <Activity className={`w-4 h-4 ml-2 transition-transform ${showFreqDropdown ? 'rotate-180' : ''}`} />
                                </button>

                                {showFreqDropdown && (
                                    <div className="absolute right-0 mt-2 w-full bg-vortex-dark border border-gray-700 rounded-lg shadow-2xl z-50 overflow-hidden animate-fade-in backdrop-blur-xl">
                                        {['Immediate', 'Hourly Digest', 'Daily Digest', 'Off'].map((option) => (
                                            <button
                                                key={option}
                                                onClick={() => {
                                                    setConfig({ ...config, alertFrequency: option });
                                                    setShowFreqDropdown(false);
                                                }}
                                                className={`w-full text-left px-4 py-2 text-sm hover:bg-vortex-accent hover:text-white transition-colors ${config.alertFrequency === option ? 'text-vortex-accent font-bold bg-vortex-accent/10' : 'text-gray-300'}`}
                                            >
                                                {option}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex items-center justify-between p-4 bg-gray-800/30 rounded-xl border border-gray-800">
                            <div className="flex-1 mr-8">
                                <h4 className="text-sm font-bold text-gray-200">Notification Channels</h4>
                                <input
                                    type="text"
                                    value={config.notificationEmails}
                                    onChange={(e) => setConfig({ ...config, notificationEmails: e.target.value })}
                                    className="mt-2 w-full bg-vortex-dark border border-gray-700 rounded-lg text-sm text-white px-4 py-2 focus:border-vortex-accent font-mono"
                                />
                            </div>
                            <div className="flex gap-2">
                                <span className="bg-vortex-accent/20 text-vortex-accent px-2 py-1 rounded text-[10px] font-bold uppercase tracking-widest">Active Email</span>
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

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
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
                    </div>
                </div>

                {/* Save Button */}
                <div className="flex justify-end pt-4">
                    <button
                        onClick={handleSave}
                        className="flex items-center gap-2 bg-vortex-accent hover:bg-vortex-accent-hover text-white px-8 py-3 rounded-xl font-bold transition-all shadow-lg shadow-vortex-accent/20"
                        disabled={saving}
                    >
                        {saving ? (
                            <RefreshCw className="w-5 h-5 animate-spin" />
                        ) : (
                            <Save className="w-5 h-5" />
                        )}
                        {saving ? 'Saving...' : 'Update System Configuration'}
                    </button>
                </div>
            </div>
        </Layout>
    );
};

export default Settings;
