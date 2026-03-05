import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Activity, ChevronDown, ChevronUp, Clock, Users, TrendingUp } from 'lucide-react';
import { getAttackPatterns } from '../../services/api';
import RiskBadge from '../Common/RiskBadge';

const GlobalAlertFeed = () => {
    const [patterns, setPatterns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState(null);

    useEffect(() => {
        fetchPatterns();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchPatterns, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchPatterns = async () => {
        try {
            const data = await getAttackPatterns();
            // Sort by severity and get recent patterns
            const patternsList = Array.isArray(data) ? data : [];
            const sorted = patternsList.sort((a, b) => {
                const severityOrder = { Critical: 0, High: 1, Medium: 2, Low: 3 };
                return (severityOrder[a.severity] || 4) - (severityOrder[b.severity] || 4);
            });
            setPatterns(sorted.slice(0, 10));
            setLoading(false);
        } catch (error) {
            console.error('Error fetching attack patterns:', error);
            setLoading(false);
        }
    };

    const toggleExpand = (patternId) => {
        setExpandedId(expandedId === patternId ? null : patternId);
    };

    const formatDuration = (hours) => {
        if (hours < 1) return `${Math.round(hours * 60)}m`;
        if (hours < 24) return `${Math.round(hours)}h`;
        return `${(hours / 24).toFixed(1)}d`;
    };

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

    if (loading) {
        return (
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <Activity className="w-5 h-5 text-purple-500" />
                        Global Alert Feed
                    </h3>
                </div>
                <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="card">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Activity className="w-5 h-5 text-purple-500" />
                    Global Alert Feed
                </h3>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    Live
                </div>
            </div>

            {patterns.length === 0 ? (
                <p className="text-gray-400 text-center py-4">No attack patterns detected</p>
            ) : (
                <div className="space-y-3 max-h-[600px] overflow-y-auto custom-scrollbar">
                    {patterns.map((pattern) => (
                        <div
                            key={pattern.pattern_name}
                            className="border border-gray-700 rounded-lg bg-gray-800/50 overflow-hidden transition-all hover:border-purple-500"
                        >
                            {/* Header */}
                            <div
                                className="p-4 cursor-pointer"
                                onClick={() => toggleExpand(pattern.pattern_name)}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-2">
                                            <RiskBadge level={pattern.severity} />
                                            <span className="text-sm font-semibold text-purple-400">
                                                {pattern.pattern_type}
                                            </span>
                                        </div>
                                        <h4 className="font-medium mb-1">{pattern.pattern_name}</h4>
                                        <p className="text-sm text-gray-400 line-clamp-2">
                                            {pattern.pattern_description || pattern.description}
                                        </p>
                                    </div>
                                    <button className="text-gray-400 hover:text-white ml-4">
                                        {expandedId === pattern.pattern_name ? (
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
                                        <span>{pattern.event_count || pattern.occurrence_count || 0} events</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <Clock className="w-4 h-4" />
                                        <span>~{formatDuration(pattern.duration_hours || pattern.avg_duration_hours || 0)}</span>
                                    </div>
                                    <div className="flex items-center gap-1">
                                        <TrendingUp className="w-4 h-4" />
                                        <span>Risk: {(pattern.chain_risk || pattern.avg_combined_risk || 0).toFixed(1)}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Expanded Details */}
                            {expandedId === pattern.pattern_name && (
                                <div className="border-t border-gray-700 p-4 bg-gray-900/50 animate-fade-in">
                                    {/* Narrative */}
                                    <div className="mb-4">
                                        <h5 className="text-sm font-semibold text-gray-300 mb-2">
                                            Attack Narrative:
                                        </h5>
                                        <p className="text-sm text-gray-400 leading-relaxed italic border-l-2 border-purple-500/30 pl-3 py-1">
                                            {renderNarrative(pattern.narrative || pattern.pattern_description || pattern.description)}
                                        </p>
                                    </div>

                                    {/* Metrics Grid */}
                                    <div className="grid grid-cols-3 gap-4 mb-4">
                                        <div className="text-center p-3 bg-gray-800 rounded">
                                            <div className="text-2xl font-bold text-purple-400">
                                                {(pattern.event_count || 0).toFixed(0)}
                                            </div>
                                            <div className="text-xs text-gray-400 mt-1">Events</div>
                                        </div>
                                        <div className="text-center p-3 bg-gray-800 rounded">
                                            <div className="text-2xl font-bold text-orange-400">
                                                {formatDuration(pattern.duration_hours || 0)}
                                            </div>
                                            <div className="text-xs text-gray-400 mt-1">Duration</div>
                                        </div>
                                        <div className="text-center p-3 bg-gray-800 rounded">
                                            <div className="text-2xl font-bold text-red-400">
                                                {(pattern.chain_risk || 0).toFixed(2)}
                                            </div>
                                            <div className="text-xs text-gray-400 mt-1">Avg Risk Score</div>
                                        </div>
                                    </div>

                                    {/* View Details Button */}
                                    <Link
                                        to={`/analytics`}
                                        className="block w-full text-center py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 rounded-lg transition-colors text-sm font-medium"
                                    >
                                        View Full Analytics →
                                    </Link>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default GlobalAlertFeed;
