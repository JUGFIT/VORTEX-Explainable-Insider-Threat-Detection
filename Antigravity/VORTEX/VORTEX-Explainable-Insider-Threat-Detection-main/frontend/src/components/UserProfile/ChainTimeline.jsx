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

    return (
        <div className="border border-gray-700 rounded-lg bg-gray-800/50 overflow-hidden">
            {/* Header - Always Visible */}
            <div
                className="p-4 cursor-pointer hover:bg-gray-800/70 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                            <RiskBadge level={chain.severity} />
                            <span className="text-sm font-semibold text-purple-400">
                                {chain.pattern_type}
                            </span>
                        </div>
                        <h4 className="font-medium mb-1">{chain.pattern_name}</h4>
                        <p className="text-sm text-gray-400 line-clamp-1">
                            {chain.pattern_description}
                        </p>
                    </div>
                    <button className="text-gray-400 hover:text-white ml-4">
                        {isExpanded ? (
                            <ChevronUp className="w-5 h-5" />
                        ) : (
                            <ChevronDown className="w-5 h-5" />
                        )}
                    </button>
                </div>

                {/* Quick Stats */}
                <div className="flex items-center gap-4 mt-3 text-xs text-gray-400">
                    <div className="flex items-center gap-1">
                        <Activity className="w-4 h-4" />
                        <span>{chain.event_count} events</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        <span>{formatDuration(chain.duration_hours)}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <AlertTriangle className="w-4 h-4" />
                        <span>Risk: {(chain.chain_risk || 0).toFixed(2)}</span>
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
                                                        {new Date(event.timestamp).toLocaleString()}
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
