import React, { useState, useEffect } from 'react';
import { X, User, Zap, ShieldAlert, Sliders, CheckCircle2, Search, Info, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import { getSimulationOptions, injectThreat } from '../../services/api';

const SimulationPanel = ({ isOpen, onClose, onShowReveal }) => {
    const [loading, setLoading] = useState(true);
    const [injecting, setInjecting] = useState(false);
    const [options, setOptions] = useState({ users: [], scenarios: {} });
    const [searchQuery, setSearchQuery] = useState('');

    // Selection state
    const [selectedUser, setSelectedUser] = useState('');
    const [selectedScenario, setSelectedScenario] = useState('');
    const [parameters, setParameters] = useState({});
    const [results, setResults] = useState(null);

    useEffect(() => {
        if (isOpen) {
            fetchOptions();
        }
    }, [isOpen]);

    const fetchOptions = async () => {
        try {
            setLoading(true);
            const data = await getSimulationOptions();
            setOptions(data);
            // Pre-select first user and scenario
            if (data.users.length > 0) setSelectedUser(data.users[0]);
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
                parameters: parameters
            };
            const data = await injectThreat(payload);
            setResults(data);
            if (onShowReveal) onShowReveal(data);
        } catch (error) {
            console.error('Injection failed:', error);
            alert('Injection failed. Check console for details.');
        } finally {
            setInjecting(false);
        }
    };

    const filteredUsers = options.users.filter(u =>
        u.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
            <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-fade-in">
                {/* Header */}
                <div className="p-4 border-b border-gray-700 flex items-center justify-between bg-gray-800/50">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                            <Zap className="w-6 h-6 text-purple-500" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold">Threat Simulation</h2>
                            <p className="text-xs text-gray-400">Demo Environment & Injection Console</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-700 rounded-full transition-colors">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {loading ? (
                    <div className="flex-1 flex flex-col items-center justify-center p-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mb-4"></div>
                        <p className="text-gray-400">Loading simulation datasets...</p>
                    </div>
                ) : results ? (
                    /* Success Result View */
                    <div className="flex-1 overflow-y-auto p-6 text-center">
                        <div className="w-20 h-20 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <CheckCircle2 className="w-12 h-12 text-green-500" />
                        </div>
                        <h3 className="text-2xl font-bold mb-2">Threat Injected Successfully!</h3>
                        <p className="text-gray-400 mb-8 max-w-md mx-auto">
                            The simulation for <span className="text-white font-semibold">{results.injection_details?.user_id || selectedUser}</span> has been processed.
                            {results.events_injected} security events were added to the audit trail.
                        </p>

                        <div className="grid grid-cols-2 gap-4 mb-8 text-left">
                            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                                <div className="text-xs text-gray-400 mb-1 uppercase tracking-wider font-bold">Expected Detection</div>
                                <div className="text-lg text-orange-400 font-semibold">High / Critical</div>
                            </div>
                            <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
                                <div className="text-xs text-gray-400 mb-1 uppercase tracking-wider font-bold">Latency</div>
                                <div className="text-lg text-purple-400 font-semibold">&lt; 1.0s (Real-time)</div>
                            </div>
                        </div>

                        <div className="flex flex-col gap-3">
                            <button
                                onClick={onClose}
                                className="btn-primary py-3"
                            >
                                Go to Dashboard
                            </button>
                            <button
                                onClick={() => setResults(null)}
                                className="text-gray-400 hover:text-white transition-colors text-sm"
                            >
                                Inject Another Scenario
                            </button>
                        </div>
                    </div>
                ) : (
                    /* Main Configuration View */
                    <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                        <div className="space-y-8">
                            {/* Step 1: Target Selector */}
                            <section>
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center text-xs font-bold">1</span>
                                    <h3 className="font-semibold text-gray-200">Select Target User</h3>
                                </div>

                                <div className="relative mb-3">
                                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <input
                                        type="text"
                                        placeholder="Search users..."
                                        className="w-full bg-gray-800 border-gray-700 pl-10 pr-4 py-2 text-sm"
                                        value={searchQuery}
                                        onChange={(e) => setSearchQuery(e.target.value)}
                                    />
                                </div>

                                <select
                                    className="w-full bg-gray-800 border-gray-700 py-3 px-4 focus:ring-purple-500"
                                    value={selectedUser}
                                    onChange={(e) => setSelectedUser(e.target.value)}
                                >
                                    {filteredUsers.map(u => (
                                        <option key={u} value={u}>{u}</option>
                                    ))}
                                </select>
                                <p className="text-[10px] text-gray-500 mt-2 italic flex items-center gap-1">
                                    <Info className="w-3 h-3" /> Showing users from organizational behavioral logs
                                </p>
                            </section>

                            {/* Step 2: Scenario Selection */}
                            <section>
                                <div className="flex items-center gap-2 mb-4">
                                    <span className="w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center text-xs font-bold">2</span>
                                    <h3 className="font-semibold text-gray-200">Select Threat Scenario</h3>
                                </div>

                                <div className="grid grid-cols-1 gap-3">
                                    {Object.entries(options.scenarios).map(([id, scenario]) => (
                                        <div
                                            key={id}
                                            onClick={() => handleScenarioChange(id, scenario)}
                                            className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${selectedScenario === id
                                                ? 'border-purple-500 bg-purple-500/10'
                                                : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                                                }`}
                                        >
                                            <div className="flex items-center gap-3 mb-2">
                                                <div className={`p-2 rounded-md ${selectedScenario === id ? 'bg-purple-500 text-white' : 'bg-gray-700 text-gray-400'}`}>
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
                            </section>

                            {/* Step 3: Parameters */}
                            {selectedScenario && (
                                <section className="animate-fade-in">
                                    <div className="flex items-center gap-2 mb-4">
                                        <span className="w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center text-xs font-bold">3</span>
                                        <h3 className="font-semibold text-gray-200">Configure Intensity</h3>
                                    </div>

                                    <div className="bg-gray-800 border border-gray-700 rounded-lg p-5 space-y-6">
                                        {options.scenarios[selectedScenario].parameters.map(param => (
                                            <div key={param.id} className="space-y-3">
                                                <div className="flex items-center justify-between">
                                                    <label className="text-sm font-medium text-gray-300 flex items-center gap-2">
                                                        <Sliders className="w-3 h-3 text-purple-500" />
                                                        {param.name}
                                                    </label>
                                                    <span className="text-xs font-mono bg-gray-700 px-2 py-0.5 rounded text-purple-300">
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
                                                        className="w-full accent-purple-500"
                                                    />
                                                ) : param.type === 'number' ? (
                                                    <input
                                                        type="number"
                                                        min={param.min}
                                                        max={param.max}
                                                        value={parameters[param.id]}
                                                        onChange={(e) => handleParamChange(param.id, e.target.value)}
                                                        className="w-full bg-gray-700 border-gray-600 py-2 px-3 text-sm"
                                                    />
                                                ) : param.type === 'toggle' ? (
                                                    <div className="flex items-center gap-3">
                                                        <button
                                                            onClick={() => handleParamChange(param.id, !parameters[param.id])}
                                                            className={`w-12 h-6 rounded-full relative transition-colors ${parameters[param.id] ? 'bg-purple-500' : 'bg-gray-600'}`}
                                                        >
                                                            <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${parameters[param.id] ? 'left-7' : 'left-1'}`}></div>
                                                        </button>
                                                        <span className="text-xs text-gray-400">{parameters[param.id] ? 'Enabled' : 'Disabled'}</span>
                                                    </div>
                                                ) : param.type === 'dropdown' ? (
                                                    <select
                                                        className="w-full bg-gray-700 border-gray-600 py-2 px-3 text-sm"
                                                        value={parameters[param.id]}
                                                        onChange={(e) => handleParamChange(param.id, e.target.value)}
                                                    >
                                                        {param.options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                                                    </select>
                                                ) : null}
                                            </div>
                                        ))}
                                    </div>

                                    {/* Prediction Preview */}
                                    <div className="mt-4 p-3 bg-orange-500/10 border border-orange-500/30 rounded flex items-start gap-3">
                                        <AlertTriangle className="w-5 h-5 text-orange-500 shrink-0 mt-0.5" />
                                        <div>
                                            <h5 className="text-xs font-bold text-orange-500 uppercase">Detection Analytics</h5>
                                            <p className="text-[11px] text-gray-400 leading-normal">
                                                Given current parameters, this attack is likely to be detected as <strong>CRITICAL</strong> severity within
                                                the next detection cycle (approx 1 second). Internal anomaly score estimated at <strong>0.88 - 0.95</strong>.
                                            </p>
                                        </div>
                                    </div>
                                </section>
                            )}
                        </div>
                    </div>
                )}

                {/* Footer */}
                {!results && !loading && (
                    <div className="p-4 border-t border-gray-700 bg-gray-800/30 flex items-center justify-between">
                        <div className="text-xs text-gray-500">
                            Target: <span className="text-gray-300 font-mono">{selectedUser}</span>
                        </div>
                        <button
                            onClick={handleInject}
                            disabled={injecting || !selectedUser || !selectedScenario}
                            className={`btn-primary flex items-center gap-2 px-8 ${injecting ? 'opacity-70 cursor-not-allowed' : ''}`}
                        >
                            {injecting ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                    Injecting...
                                </>
                            ) : (
                                <>
                                    <Zap className="w-4 h-4" />
                                    Inject Threat
                                </>
                            )}
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SimulationPanel;
