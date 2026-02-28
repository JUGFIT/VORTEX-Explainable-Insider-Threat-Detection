import React, { useState, useEffect } from 'react';
import { X, User, Zap, ShieldAlert, Sliders, CheckCircle2, Search, Info, AlertTriangle, TrendingUp, TrendingDown, Clock, History } from 'lucide-react';
import { getSimulationOptions, injectThreat } from '../../services/api';

const CustomSelectDropdown = ({ value, onChange, options, label, placeholder }) => {
    const [isOpen, setIsOpen] = React.useState(false);
    const dropdownRef = React.useRef(null);

    React.useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, [isOpen]);

    return (
        <div className="flex-1 relative" ref={dropdownRef}>
            {label && <label className="text-xs text-gray-400 mb-1 block">{label}</label>}
            <div
                className="w-full bg-[#12151a] border border-white/10 py-2.5 px-4 rounded cursor-pointer flex justify-between items-center transition-colors hover:border-gray-600"
                onClick={() => setIsOpen(!isOpen)}
            >
                <span className={!value ? "text-gray-500" : "text-white"}>{options.find(o => o.value === value)?.label || placeholder || ''}</span>
                <svg className="fill-current h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20">
                    <path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z" />
                </svg>
            </div>

            {isOpen && (
                <div className="absolute top-full left-0 right-0 mt-2 max-h-48 overflow-y-auto bg-[#1c2128] border border-white/10 rounded shadow-2xl z-50 custom-scrollbar">
                    {options.map(opt => (
                        <div
                            key={opt.value}
                            className={`px-4 py-2 cursor-pointer transition-colors ${opt.value === value ? 'bg-vortex-accent/20 text-vortex-accent font-bold' : 'text-gray-300 hover:bg-white/5 hover:text-white'}`}
                            onClick={() => {
                                onChange(opt.value);
                                setIsOpen(false);
                            }}
                        >
                            {opt.label}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const AlarmTimePicker = ({ value, onChange }) => {
    // Treat empty value as 12:00 for display purposes
    const [h, m] = value ? value.split(':').map(Number) : [12, 0];
    const currentHour = isNaN(h) ? 12 : h;
    const currentMinute = isNaN(m) ? 0 : m;

    React.useEffect(() => {
        // Init state if empty
        if (!value) onChange('12:00');
    }, []);

    const updateTime = (newHour, newMinute) => {
        const hStr = newHour.toString().padStart(2, '0');
        const mStr = newMinute.toString().padStart(2, '0');
        onChange(`${hStr}:${mStr}`);
    };

    const pad = (n) => n.toString().padStart(2, '0');

    const hourOptions = Array.from({ length: 24 }, (_, i) => ({ value: i, label: pad(i) }));
    const minuteOptions = Array.from({ length: 60 }, (_, i) => ({ value: i, label: pad(i) }));

    return (
        <div className="flex gap-4">
            <CustomSelectDropdown
                label="Hour"
                value={currentHour}
                options={hourOptions}
                onChange={(val) => updateTime(val, currentMinute)}
            />

            <div className="flex flex-col justify-end pb-2">
                <span className="text-xl font-bold text-gray-500">:</span>
            </div>

            <CustomSelectDropdown
                label="Minute"
                value={currentMinute}
                options={minuteOptions}
                onChange={(val) => updateTime(currentHour, val)}
            />
        </div>
    );
};

const SimulationPanel = ({ isOpen, onClose, onShowReveal, inline = false }) => {
    const [loading, setLoading] = useState(true);
    const [injecting, setInjecting] = useState(false);
    const [options, setOptions] = useState({ users: [], scenarios: {} });
    const [searchQuery, setSearchQuery] = useState('');

    // Selection state
    const [selectedUser, setSelectedUser] = useState('');
    const [selectedScenario, setSelectedScenario] = useState('');
    const [parameters, setParameters] = useState({});
    const [activeTab, setActiveTab] = useState(1);
    const [results, setResults] = useState(null);
    const [timeMode, setTimeMode] = useState('current');
    const [customTime, setCustomTime] = useState('');
    const [customDate, setCustomDate] = useState('');
    const [history, setHistory] = useState(() => {
        const saved = localStorage.getItem('vortex_simulation_history');
        return saved ? JSON.parse(saved) : [];
    });

    useEffect(() => {
        localStorage.setItem('vortex_simulation_history', JSON.stringify(history));
    }, [history]);

    useEffect(() => {
        if (isOpen || inline) {
            fetchOptions();
        }
    }, [isOpen, inline]);

    const fetchOptions = async () => {
        try {
            setLoading(true);
            const data = await getSimulationOptions();
            setOptions(data);
            // Pre-select first scenario but DO NOT pre-select user so that selection is explicitly required
            if (Object.keys(data.scenarios).length > 0) {
                const firstScenarioId = Object.keys(data.scenarios)[0];
                handleScenarioChange(firstScenarioId, data.scenarios[firstScenarioId]);
            }
        } catch (error) {
            console.error('Error fetching simulation options:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleScenarioChange = (id, scenario) => {
        setSelectedScenario(id);
        // Initialize default parameters
        const defaults = {};
        scenario.parameters.forEach(p => {
            defaults[p.id] = p.default;
        });
        setParameters(defaults);
    };

    const handleParamChange = (id, value) => {
        setParameters(prev => ({ ...prev, [id]: value }));
    };

    const handleInject = async () => {
        try {
            setInjecting(true);
            const payload = {
                user_id: selectedUser,
                scenario_id: selectedScenario,
                parameters: parameters,
                time_mode: timeMode,
                custom_time: customTime,
                custom_date: customDate
            };
            const data = await injectThreat(payload);
            setResults(data);

            // Add to history
            const historyItem = {
                id: Date.now(),
                timestamp: new Date().toISOString(),
                user: selectedUser,
                scenario: options.scenarios[selectedScenario].name,
                events: data.events_injected || 5,
                status: 'Success'
            };
            setHistory(prev => [historyItem, ...prev].slice(0, 50));

            if (onShowReveal) onShowReveal(data);
        } catch (error) {
            console.error('Injection failed:', error);
            alert(`Injection failed: ${error.message || 'Unknown error'}. Check console for details.`);
        } finally {
            setInjecting(false);
        }
    };

    const filteredUsers = options.users.filter(u =>
        u.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const getIntensityPreview = () => {
        if (!selectedScenario || !options.scenarios[selectedScenario]) return { level: 'High / Critical', score: '0.88 - 0.95', color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500/30' };
        let val = 0.5;
        if (selectedScenario === 'data_exfiltration') {
            const files = Number(parameters['file_count']) || 5;
            const size = Number(parameters['upload_size']) || 1000;
            val = (files / 100.0 + size / 5000.0) / 2.0;
        } else if (selectedScenario === 'reconnaissance') {
            val = (Number(parameters['intensity']) || 200) / 1000.0;
        } else if (selectedScenario === 'unauthorized_access') {
            val = (Number(parameters['attempts']) || 3) / 10.0;
        } else if (selectedScenario === 'insider_sabotage') {
            val = (Number(parameters['mod_count']) || 5) / 20.0;
        } else if (selectedScenario === 'lateral_movement') {
            val = (Number(parameters['scan_intensity']) || 50) / 500.0;
        } else if (selectedScenario === 'credential_harvesting') {
            val = (Number(parameters['account_count']) || 10) / 50.0;
        }

        if (val <= 0.2) return { level: 'Low', score: '0.10 - 0.30', color: 'text-green-500', bg: 'bg-green-500/10', border: 'border-green-500/30' };
        if (val <= 0.4) return { level: 'Medium', score: '0.40 - 0.60', color: 'text-yellow-500', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' };
        if (val <= 0.7) return { level: 'High', score: '0.70 - 0.85', color: 'text-orange-500', bg: 'bg-orange-500/10', border: 'border-orange-500/30' };
        return { level: 'Critical', score: '0.88 - 0.99', color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500/30' };
    };

    const renderSidebar = () => {
        const steps = [
            { id: 1, label: 'Configure Simulation', icon: Zap, done: !!selectedUser && !!selectedScenario && Object.keys(parameters).length > 0 },
            { id: 3, label: 'Injection History', icon: History, done: history.length > 0 }
        ];

        return (
            <div className="w-72 bg-vortex-dark border-r border-white/5 h-full flex flex-col z-20">
                <div className="py-6 px-6 border-b border-white/5 flex items-center gap-3">
                    <div className="w-10 h-10 bg-vortex-accent/20 rounded-lg flex items-center justify-center">
                        <Zap className="w-6 h-6 text-vortex-accent" />
                    </div>
                    <div>
                        <h2 className="text-lg font-bold leading-tight">Event Log<br />Generator</h2>
                    </div>
                </div>

                <div className="flex-1 p-4 space-y-2">
                    {steps.map((step) => {
                        const active = activeTab === step.id;
                        return (
                            <button
                                key={step.id}
                                onClick={() => setActiveTab(step.id)}
                                className={`w-full flex items-center space-x-4 px-5 py-3 rounded-2xl transition-all duration-300 group relative border text-left ${active
                                    ? 'bg-white/10 text-white border-white/10 shadow-[0_4px_12px_rgba(0,0,0,0.2)]'
                                    : 'text-gray-400 hover:bg-white/5 hover:text-white border-transparent'
                                    }`}
                            >
                                {/* Active Focus Indicator (Glow Dot) */}
                                {active && (
                                    <div className="absolute left-1.5 w-1 h-1 rounded-full bg-vortex-accent shadow-[0_0_12px_rgba(31,111,235,1)]" />
                                )}

                                <div className={`transition-all duration-300 ${active ? 'text-vortex-accent scale-110' : 'group-hover:text-gray-200'}`}>
                                    <step.icon size={20} />
                                </div>

                                <span className={`transition-all duration-300 tracking-tight ${active
                                    ? 'text-base font-bold translate-x-1'
                                    : 'text-sm font-medium group-hover:translate-x-0.5'
                                    }`}>
                                    {step.label}
                                </span>
                            </button>
                        );
                    })}
                </div>
            </div>
        );
    };

    const preview = getIntensityPreview();

    if (!isOpen && !inline) return null;

    const content = (
        <div className={`bg-vortex-dark/95 ${inline ? 'h-full flex flex-row' : 'border border-white/10 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col'} overflow-hidden animate-fade-in`}>
            {inline && renderSidebar()}

            <div className="flex-1 flex flex-col overflow-hidden relative">
                {/* Header for modal only */}
                {!inline && (
                    <div className="p-4 border-b border-white/10 flex items-center justify-between bg-[#12151a]/50">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-vortex-accent/20 rounded-lg flex items-center justify-center">
                                <Zap className="w-6 h-6 text-vortex-accent" />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold">Event Log Generator</h2>
                                <p className="text-xs text-gray-400">Demo Environment & Telemetry Generator</p>
                            </div>
                        </div>
                        {!inline && (
                            <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors">
                                <X className="w-6 h-6" />
                            </button>
                        )}
                    </div>
                )}

                {activeTab === 3 ? (
                    /* History View */
                    <div className="flex-1 overflow-y-auto p-8 custom-scrollbar relative animate-fade-in">
                        <div className="mb-8">
                            <h2 className="text-3xl font-black text-white mb-2 tracking-tight">Injection History</h2>
                            <p className="text-gray-400">Review past simulation events and telemetry injections.</p>
                        </div>

                        {history.length === 0 ? (
                            <div className="flex-1 flex flex-col items-center justify-center py-20 text-center opacity-40">
                                <History className="w-16 h-16 mb-4" />
                                <p className="text-lg">No simulations launched yet</p>
                                <p className="text-xs">Your event logs will appear here once generated.</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {history.map(item => (
                                    <div
                                        key={item.id}
                                        className="bg-[#12151a]/80 border border-white/5 p-4 rounded-xl flex items-center justify-between hover:border-vortex-accent/30 transition-all group"
                                    >
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-lg bg-vortex-accent/10 flex items-center justify-center group-hover:bg-vortex-accent/20 transition-colors">
                                                <Zap className="w-5 h-5 text-vortex-accent/70" />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-bold text-white tracking-tight">{item.scenario}</span>
                                                    <span className="text-[10px] bg-green-500/10 text-green-500 px-1.5 py-0.5 rounded font-black uppercase">{item.status}</span>
                                                </div>
                                                <div className="text-xs text-gray-400 mt-1">
                                                    Target: <span className="text-gray-300 font-mono">{item.user}</span> •
                                                    <span className="ml-1">{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm font-bold text-white">{item.events} Events</div>
                                            <div className="text-[10px] text-gray-500 uppercase font-black">{new Date(item.timestamp).toLocaleDateString()}</div>
                                        </div>
                                    </div>
                                ))}
                                <button
                                    onClick={() => { if (confirm('Clear history?')) setHistory([]); }}
                                    className="w-full py-4 text-xs text-gray-600 hover:text-red-400 transition-colors uppercase font-black tracking-widest mt-8"
                                >
                                    Clear History Log
                                </button>
                            </div>
                        )}
                    </div>
                ) : loading ? (
                    <div className="flex-1 flex flex-col items-center justify-center p-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-vortex-accent mb-4"></div>
                        <p className="text-gray-400">Loading simulation datasets...</p>
                    </div>
                ) : results ? (
                    /* Success Result View */
                    <div className="flex-1 overflow-y-auto p-12 text-center animate-fade-in">
                        <div className="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-8 animate-scale-in border-4 border-green-500/30">
                            <CheckCircle2 className="w-14 h-14 text-green-500" strokeWidth={3} />
                        </div>
                        <h3 className="text-3xl font-black mb-3 tracking-tight">Activity Log Injected</h3>
                        <p className="text-gray-400 mb-10 max-w-sm mx-auto leading-relaxed">
                            Telemetry for <code className="text-vortex-accent font-mono bg-vortex-accent/5 px-2 py-0.5 rounded">{results.injection_details?.user_id || selectedUser}</code> has been integrated into the security event stream.
                        </p>

                        <div className="grid grid-cols-2 gap-4 mb-12 text-left max-w-lg mx-auto">
                            <div className="bg-[#12151a]/80 p-5 rounded-2xl border border-white/5">
                                <div className="text-[10px] text-gray-500 mb-1 uppercase tracking-widest font-black">Audit Status</div>
                                <div className="text-lg font-bold text-green-500 flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                    Live Log
                                </div>
                            </div>
                            <div className="bg-[#12151a]/80 p-5 rounded-2xl border border-white/5">
                                <div className="text-[10px] text-gray-500 mb-1 uppercase tracking-widest font-black">Events Injected</div>
                                <div className="text-lg text-white font-bold">{results.events_injected || 5} Records</div>
                            </div>
                        </div>

                        <div className="flex flex-col gap-4 max-w-md mx-auto">
                            <button
                                onClick={onClose}
                                className="btn-primary py-4 rounded-xl font-bold text-lg shadow-lg"
                            >
                                Return to Dashboard
                            </button>
                            <button
                                onClick={() => setResults(null)}
                                className="text-gray-500 hover:text-white transition-all text-sm font-semibold hover:tracking-wide"
                            >
                                Generate Another Scenario
                            </button>
                        </div>
                    </div>
                ) : (
                    /* Main Configuration View */
                    <div className="flex-1 overflow-y-auto p-8 pb-32 custom-scrollbar relative">
                        <div className="w-full max-w-5xl space-y-8">
                            {/* Step 1: Target Selector & Time */}
                            {(!inline || activeTab === 1) && (
                                <section className="animate-fade-in">
                                    {!inline && (
                                        <div className="flex items-center gap-2 mb-4">
                                            <span className="w-6 h-6 rounded-full bg-vortex-accent text-white flex items-center justify-center text-xs font-bold">1</span>
                                            <h3 className="font-semibold text-gray-200">Select Target & Time</h3>
                                        </div>
                                    )}

                                    {inline && (
                                        <div className="mb-6">
                                            <h2 className="text-3xl font-bold text-white mb-2">Configure Simulation</h2>
                                            <p className="text-gray-400">Select the employee, timing, and threat pattern to inject.</p>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        <div>
                                            <div className="flex items-center gap-2 mb-4">
                                                <User className="w-5 h-5 text-gray-400" />
                                                <h3 className="font-semibold text-gray-200">Target User</h3>
                                            </div>
                                            <div className="relative mb-3">
                                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                                <input
                                                    type="text"
                                                    placeholder="Search users..."
                                                    className="w-full bg-[#12151a] border-white/10 pl-10 pr-4 py-2 text-sm rounded focus:ring-1 focus:ring-vortex-accent"
                                                    value={searchQuery}
                                                    onChange={(e) => setSearchQuery(e.target.value)}
                                                />
                                            </div>

                                            <CustomSelectDropdown
                                                value={selectedUser}
                                                options={filteredUsers.map(u => ({ value: u, label: u }))}
                                                onChange={(val) => setSelectedUser(val)}
                                                placeholder="Choose a user from the logs..."
                                            />
                                            <p className="text-2xs text-gray-500 mt-2 italic flex items-center gap-1">
                                                <Info className="w-3 h-3" /> Showing users from organizational behavioral logs
                                            </p>
                                        </div>

                                        <div>
                                            <div className="flex items-center gap-2 mb-4">
                                                <Clock className="w-5 h-5 text-gray-400" />
                                                <h3 className="font-semibold text-gray-200">Execution Date & Time</h3>
                                            </div>
                                            <div className="grid grid-cols-1 gap-3 mb-6">
                                                {[
                                                    { id: 'current', label: 'Current Time' },
                                                    { id: 'custom', label: 'Custom Time' }
                                                ].map(mode => (
                                                    <button
                                                        key={mode.id}
                                                        onClick={() => setTimeMode(mode.id)}
                                                        className={`p-3 rounded-lg border text-sm font-semibold transition-all ${timeMode === mode.id
                                                            ? 'bg-vortex-accent/20 border-vortex-accent text-white'
                                                            : 'bg-[#12151a] border-white/10 text-gray-400 hover:border-gray-600'
                                                            }`}
                                                    >
                                                        {mode.label}
                                                    </button>
                                                ))}
                                            </div>

                                            {timeMode === 'custom' && (
                                                <div className="animate-fade-in relative mt-2 space-y-4">
                                                    <div>
                                                        <label className="text-xs text-gray-400 mb-1 block">Date</label>
                                                        <input
                                                            type="date"
                                                            value={customDate}
                                                            onChange={(e) => setCustomDate(e.target.value)}
                                                            className="w-full bg-[#12151a] border border-white/10 p-2 text-white rounded focus:ring-1 focus:ring-vortex-accent [color-scheme:dark]"
                                                        />
                                                    </div>
                                                    <div>
                                                        <AlarmTimePicker
                                                            value={customTime}
                                                            onChange={(newTime) => setCustomTime(newTime)}
                                                        />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </div>


                                </section>
                            )}

                            {/* Step 2: Scenario Selection & Configuration */}
                            {(!inline || activeTab === 1) && (
                                <section className="animate-fade-in pb-24 mt-12 border-t border-white/5 pt-12">
                                    {!inline && (
                                        <div className="flex items-center gap-2 mb-4">
                                            <span className="w-6 h-6 rounded-full bg-vortex-accent text-white flex items-center justify-center text-xs font-bold">2</span>
                                            <h3 className="font-semibold text-gray-200">Activity Scenario</h3>
                                        </div>
                                    )}

                                    {inline && (
                                        <div className="mb-6">
                                            <h2 className="text-2xl font-bold text-white mb-2">Activity Scenario</h2>
                                            <p className="text-gray-400">Choose the type of insider threat pattern and tune its properties.</p>
                                        </div>
                                    )}

                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-8">
                                        {Object.entries(options.scenarios).map(([id, scenario]) => (
                                            <div
                                                key={id}
                                                onClick={() => handleScenarioChange(id, scenario)}
                                                className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${selectedScenario === id
                                                    ? 'border-vortex-accent bg-vortex-accent/10'
                                                    : 'border-white/10 bg-[#12151a] hover:border-gray-600'
                                                    }`}
                                            >
                                                <div className="flex items-center gap-3 mb-2">
                                                    <div className={`p-2 rounded-md ${selectedScenario === id ? 'bg-vortex-accent text-white' : 'bg-white/5 text-gray-400'}`}>
                                                        {id === 'data_exfiltration' ? <ShieldAlert className="w-4 h-4" /> :
                                                            id === 'reconnaissance' ? <Search className="w-4 h-4" /> :
                                                                id === 'unauthorized_access' ? <Info className="w-4 h-4" /> :
                                                                    id === 'insider_sabotage' ? <Zap className="w-4 h-4" /> :
                                                                        id === 'lateral_movement' ? <TrendingUp className="w-4 h-4" /> :
                                                                            <User className="w-4 h-4" />}
                                                    </div>
                                                    <h4 className="font-bold">{scenario.name}</h4>
                                                </div>
                                                <p className="text-xs text-gray-400 leading-relaxed">{scenario.description}</p>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Configuration Intensity (Shown only when a scenario is selected) */}
                                    {selectedScenario && (
                                        <div className="animate-fade-in mt-8">
                                            <div className="flex items-center gap-2 mb-4">
                                                <Sliders className="w-5 h-5 text-gray-400" />
                                                <h3 className="font-semibold text-gray-200">Configure Intensity</h3>
                                            </div>

                                            <div className="bg-[#12151a] border border-white/10 rounded-lg p-5 space-y-6">
                                                {options.scenarios[selectedScenario].parameters.map(param => (
                                                    <div key={param.id} className="space-y-3">
                                                        <div className="flex items-center justify-between">
                                                            <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                                                                <Sliders className="w-3 h-3 text-vortex-accent" />
                                                                {param.name}
                                                            </label>
                                                            <span className="text-xs font-mono bg-white/5 px-2 py-0.5 rounded text-vortex-accent/60">
                                                                {parameters[param.id]} {param.unit || ''}
                                                            </span>
                                                        </div>

                                                        {param.type === 'slider' ? (
                                                            <input
                                                                type="range"
                                                                min={param.min}
                                                                max={param.max}
                                                                step={1}
                                                                value={parameters[param.id]}
                                                                onChange={(e) => handleParamChange(param.id, e.target.value)}
                                                                className="w-full accent-vortex-accent"
                                                            />
                                                        ) : param.type === 'number' ? (
                                                            <input
                                                                type="number"
                                                                min={param.min}
                                                                max={param.max}
                                                                value={parameters[param.id]}
                                                                onChange={(e) => handleParamChange(param.id, e.target.value)}
                                                                className="w-full bg-white/5 border-gray-600 py-2 px-3 text-sm"
                                                            />
                                                        ) : param.type === 'toggle' ? (
                                                            <div className="flex items-center gap-3">
                                                                <button
                                                                    onClick={() => handleParamChange(param.id, !parameters[param.id])}
                                                                    className={`w-12 h-6 rounded-full relative transition-colors ${parameters[param.id] ? 'bg-vortex-accent' : 'bg-gray-600'}`}
                                                                >
                                                                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${parameters[param.id] ? 'left-7' : 'left-1'}`}></div>
                                                                </button>
                                                                <span className="text-xs text-gray-400">{parameters[param.id] ? 'Enabled' : 'Disabled'}</span>
                                                            </div>
                                                        ) : param.type === 'dropdown' ? (
                                                            <CustomSelectDropdown
                                                                value={parameters[param.id]}
                                                                options={param.options.map(opt => ({ value: opt, label: opt }))}
                                                                onChange={(val) => handleParamChange(param.id, val)}
                                                            />
                                                        ) : null}
                                                    </div>
                                                ))}
                                            </div>

                                            {/* Prediction Preview */}
                                            <div className={`mt-4 p-3 rounded flex items-start gap-3 border ${preview.bg} ${preview.border}`}>
                                                <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${preview.color}`} />
                                                <div>
                                                    <h5 className={`text-xs font-bold uppercase ${preview.color}`}>Detection Analytics</h5>
                                                    <p className="text-xs text-gray-400 leading-normal">
                                                        Given current parameters, this activity is likely to be detected as <strong>{preview.level.toUpperCase()}</strong> severity within
                                                        the next detection cycle (approx 1 second). Internal anomaly score estimated at <strong>{preview.score}</strong>.
                                                    </p>
                                                </div>
                                            </div>

                                            <div className="mt-3 p-3 bg-[#12151a]/50 rounded flex items-start gap-3 border border-white/10/50">
                                                <Info className="w-4 h-4 shrink-0 text-gray-400 mt-0.5" />
                                                <p className="text-xs text-gray-400 leading-normal">
                                                    <strong>Demo Mode Note:</strong> Low intensity generates routine logs (true negatives); high intensity generates suspicious activity logs (true positives).
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    <div className="mt-12 flex items-center justify-end border-t border-white/5 pt-8">

                                        <button
                                            onClick={handleInject}
                                            disabled={injecting || !selectedUser || !selectedScenario}
                                            className={`btn-primary flex items-center gap-2 px-12 py-5 rounded-2xl transition-all text-lg font-black tracking-tight ${injecting || !selectedUser || !selectedScenario ? 'opacity-50 cursor-not-allowed' : 'transform hover:-translate-y-1 active:scale-95'}`}
                                        >
                                            {injecting ? (
                                                <>
                                                    <div className="w-5 h-5 border-3 border-white/30 border-t-white rounded-full animate-spin"></div>
                                                    Processing...
                                                </>
                                            ) : (
                                                <>
                                                    <Zap className="w-6 h-6 fill-white/10" />
                                                    Generate Activity Log
                                                </>
                                            )}
                                        </button>
                                    </div>
                                </section>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );

    return inline ? content : (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            {content}
        </div>
    );
};

export default SimulationPanel;
