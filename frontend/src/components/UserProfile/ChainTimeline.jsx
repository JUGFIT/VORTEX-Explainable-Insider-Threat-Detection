import { useState } from 'react';
import { ChevronDown, ChevronUp, Clock, AlertTriangle, Activity } from 'lucide-react';
import RiskBadge from '../Common/RiskBadge';

const ChainTimeline = ({ chain }) => {
    const [isExpanded, setIsExpanded] = useState(false);

    const formatDuration = (hours) => {
        if (hours < 1) return `${Math.round(hours * 60)} minutes`;
        if (hours < 24) return `${hours.toFixed(1)} hours`;
        return `${(hours / 24).toFixed(1)} days`;
    };

    // Helper to render basic markdown bolding
    const renderNarrative = (text) => {
        if (!text) return null;
        const parts = text.split(/(\*\*.*?\*\*)/g);
        return parts.map((part, i) => {
            if (part.startsWith('**') && part.endsWith('**')) {
                return <strong key={i} className="text-white font-black">{part.slice(2, -2)}</strong>;
            }
            return part;
        });
    };

    const isCritical = chain.severity?.toLowerCase() === 'critical' || (chain.chain_risk || 0) > 0.8;

    return (
        <div className={`card card-glass card-cyber ${isCritical ? 'card-cyber-red border-red-500/20' : 'border-gray-800'}`}>
            {/* Header - Always Visible */}
            <div
                className="cursor-pointer transition-all relative z-10"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                            <RiskBadge level={chain.severity} />
                            <span className="text-[10px] font-black uppercase tracking-widest text-purple-400 opacity-80">
                                {chain.pattern_type}
                            </span>
                        </div>
                        <h4 className="text-lg font-black text-white mb-1 leading-tight tracking-tight group-hover:text-vortex-accent transition-colors">
                            {chain.pattern_name}
                        </h4>
                        <p className="text-xs text-gray-400 font-medium leading-relaxed line-clamp-1 max-w-[450px]">
                            {chain.pattern_description}
                        </p>
                    </div>
                    <button className="text-gray-500 hover:text-white p-1.5 rounded-lg bg-gray-900/50 border border-gray-800 group-hover:border-vortex-accent/40 transition-all">
                        {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-vortex-accent" />
                        ) : (
                            <ChevronDown className="w-4 h-4" />
                        )}
                    </button>
                </div>

                {/* Quick Stats Condensed Row */}
                <div className="flex items-center gap-5 mt-4 border-t border-gray-800/30 pt-3">
                    <div className="flex items-center gap-1.5 group/stat">
                        <Activity className="w-3 h-3 text-vortex-accent" />
                        <span className="text-[10px] font-bold text-gray-300">{chain.event_count} signals</span>
                    </div>
                    <div className="flex items-center gap-1.5 group/stat">
                        <Clock className="w-3 h-3 text-orange-400" />
                        <span className="text-[10px] font-bold text-gray-300">{formatDuration(chain.duration_hours)}</span>
                    </div>
                    <div className="flex items-center gap-1.5 group/stat">
                        <AlertTriangle className={`w-3 h-3 ${isCritical ? 'text-red-500' : 'text-yellow-500'}`} />
                        <span className={`text-[10px] font-black ${isCritical ? 'text-red-500' : 'text-yellow-500'}`}>
                            Risk: {(chain.chain_risk || 0).toFixed(2)}
                        </span>
                    </div>
                </div>
            </div>

            {/* Expanded Content - Event Timeline */}
            {isExpanded && (
                <div className="border-t border-gray-700 p-4 bg-gray-900/50 animate-fade-in">
                    {/* Narrative */}
                    <div className="mb-4 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                        <h5 className="text-sm font-semibold text-purple-300 mb-2 flex items-center gap-2">
                            <AlertTriangle className="w-4 h-4" />
                            Attack Narrative
                        </h5>
                        <p className="text-sm text-gray-300 leading-relaxed">{renderNarrative(chain.narrative)}</p>
                    </div>

                    {/* Event Timeline */}
                    <div className="mb-4">
                        <h5 className="text-sm font-semibold text-gray-300 mb-3">Event Sequence:</h5>
                        <div className="relative">
                            {/* Timeline Line */}
                            <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-500 via-purple-500/50 to-transparent"></div>

                            {/* Events */}
                            <div className="space-y-4">
                                {chain.events.map((event, index) => (
                                    <div key={event.event_id} className="relative pl-10">
                                        {/* Timeline Dot */}
                                        <div
                                            className={`absolute left-2.5 top-2 w-3 h-3 rounded-full border-2 ${event.risk_level === 'Critical' || event.risk_level === 'High'
                                                ? 'bg-red-500 border-red-400'
                                                : event.risk_level === 'Medium'
                                                    ? 'bg-yellow-500 border-yellow-400'
                                                    : 'bg-green-500 border-green-400'
                                                }`}
                                        ></div>

                                        {/* Event Card */}
                                        <div className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                                            <div className="flex items-start justify-between mb-2">
                                                <div>
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className="text-xs font-mono text-gray-400">
                                                            #{index + 1}
                                                        </span>
                                                        <RiskBadge level={event.risk_level} />
                                                    </div>
                                                    <div className="text-xs text-gray-400">
                                                        {new Date(event.timestamp).toLocaleString('en-GB')}
                                                    </div>
                                                </div>
                                                <div className="text-right">
                                                    <div className="text-sm font-semibold text-orange-400">
                                                        {(event.anomaly_score || 0).toFixed(3)}
                                                    </div>
                                                    <div className="text-xs text-gray-400">Score</div>
                                                </div>
                                            </div>

                                            {/* Event Tags */}
                                            {event.tags && event.tags.length > 0 && (
                                                <div className="flex flex-wrap gap-1 mt-2">
                                                    {event.tags.map((tag, idx) => (
                                                        <span
                                                            key={idx}
                                                            className="px-2 py-0.5 bg-gray-700 text-gray-300 text-xs rounded"
                                                        >
                                                            {tag}
                                                        </span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Metrics Grid */}
                    <div className="grid grid-cols-3 gap-3 mb-4">
                        <div className="text-center p-3 bg-gray-800 rounded border border-gray-700">
                            <div className="text-lg font-bold text-purple-400">
                                {(chain.individual_risk_sum || 0).toFixed(2)}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">Individual Risk Sum</div>
                        </div>
                        <div className="text-center p-3 bg-gray-800 rounded border border-gray-700">
                            <div className="text-lg font-bold text-red-400">
                                {(chain.chain_risk || 0).toFixed(2)}
                            </div>
                            <div className="text-xs text-gray-400 mt-1">Chain Risk</div>
                        </div>
                        <div className="text-center p-3 bg-gray-800 rounded border border-gray-700">
                            <div className="text-lg font-bold text-orange-400">
                                {(chain.amplification_factor || 0).toFixed(2)}x
                            </div>
                            <div className="text-xs text-gray-400 mt-1">Amplification</div>
                        </div>
                    </div>

                    {/* Matched Sequence */}
                    {chain.matched_sequence && chain.matched_sequence.length > 0 && (
                        <div>
                            <h5 className="text-sm font-semibold text-gray-300 mb-2">Pattern Signature:</h5>
                            <div className="flex flex-wrap gap-2">
                                {chain.matched_sequence.map((step, idx) => (
                                    <div key={idx} className="flex items-center gap-2">
                                        <span className="px-3 py-1 bg-purple-500/20 text-purple-300 text-xs rounded-full border border-purple-500/50">
                                            {step}
                                        </span>
                                        {idx < chain.matched_sequence.length - 1 && (
                                            <span className="text-gray-600">→</span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ChainTimeline;
