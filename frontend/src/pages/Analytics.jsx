import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import RiskBadge from '../components/Common/RiskBadge';
import { TrendingUp, Target, GitBranch } from 'lucide-react';
import { getTrendingUsers, getChainPatterns } from '../services/api';
import { useNavigate } from 'react-router-dom';

const Analytics = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [trendingUsers, setTrendingUsers] = useState([]);
    const [attackPatterns, setAttackPatterns] = useState([]);

    useEffect(() => {
        fetchAnalytics();
    }, []);

    const fetchAnalytics = async () => {
        try {
            setLoading(true);

            const [trending, patterns] = await Promise.all([
                getTrendingUsers({ days: 7, limit: 10 }),
                getChainPatterns({ min_occurrences: 2 }),
            ]);

            setTrendingUsers(Array.isArray(trending) ? trending : trending.trending_users || []);
            setAttackPatterns(Array.isArray(patterns) ? patterns : patterns.patterns || []);
        } catch (error) {
            console.error('Error fetching analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Layout title="Analytics">
                <LoadingSpinner size={48} className="h-96" />
            </Layout>
        );
    }

    return (
        <Layout title="Analytics">
            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="card">
                    <div className="flex items-center space-x-3 mb-2">
                        <TrendingUp className="text-risk-critical" size={24} />
                        <h3 className="text-lg font-semibold">Trending Users</h3>
                    </div>
                    <p className="text-3xl font-bold">{trendingUsers.length}</p>
                    <p className="text-sm text-gray-400 mt-1">High-risk escalation detected</p>
                </div>

                <div className="card">
                    <div className="flex items-center space-x-3 mb-2">
                        <GitBranch className="text-risk-high" size={24} />
                        <h3 className="text-lg font-semibold">Attack Patterns</h3>
                    </div>
                    <p className="text-3xl font-bold">{attackPatterns.length}</p>
                    <p className="text-sm text-gray-400 mt-1">Identified behavioral patterns</p>
                </div>

                <div className="card">
                    <div className="flex items-center space-x-3 mb-2">
                        <Target className="text-purple-500" size={24} />
                        <h3 className="text-lg font-semibold">Detection Rate</h3>
                    </div>
                    <p className="text-3xl font-bold">94.2%</p>
                    <p className="text-sm text-gray-400 mt-1">Model accuracy</p>
                </div>
            </div>

            {/* Trending Users */}
            <div className="card mb-8">
                <h3 className="text-lg font-semibold mb-4">Trending High-Risk Users</h3>
                <p className="text-sm text-gray-400 mb-4">
                    Users with significant risk escalation in the past 7 days
                </p>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-800">
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Rank</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">User ID</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Events (7d)</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">High Risk Events</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Avg Score</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Escalation</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trendingUsers.map((user, idx) => (
                                <tr
                                    key={user.user_id}
                                    className="border-b border-gray-800 hover:bg-gray-800 transition-colors"
                                >
                                    <td className="py-3 px-4">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${idx === 0 ? 'bg-yellow-500 text-black' :
                                            idx === 1 ? 'bg-gray-400 text-black' :
                                                idx === 2 ? 'bg-orange-600 text-white' :
                                                    'bg-gray-700 text-gray-300'
                                            }`}>
                                            {idx + 1}
                                        </div>
                                    </td>
                                    <td className="py-3 px-4">
                                        <button
                                            onClick={() => navigate(`/user/${user.user_id}`)}
                                            className="text-vortex-accent hover:text-vortex-accent-hover font-medium"
                                        >
                                            {user.user_id}
                                        </button>
                                    </td>
                                    <td className="py-3 px-4 text-sm">{user.recent_event_count || user.event_count || 0}</td>
                                    <td className="py-3 px-4 text-sm font-semibold text-risk-critical">
                                        {user.high_risk_count || 'N/A'}
                                    </td>
                                    <td className="py-3 px-4 text-sm font-mono">
                                        {(user.avg_anomaly_score || user.current_risk || 0).toFixed(3)}
                                    </td>
                                    <td className="py-3 px-4">
                                        {(user.escalation_severity === 'Critical' || user.escalation_severity === 'High' || user.is_escalating) ? (
                                            <div className="flex items-center space-x-1">
                                                <TrendingUp size={16} className="text-risk-critical" />
                                                <span className="text-sm text-risk-critical font-semibold">
                                                    {user.escalation_severity || 'High'} (+{(user.escalation_rate || user.percent_change || 0).toFixed(0)}%)
                                                </span>
                                            </div>
                                        ) : (
                                            <span className="text-sm text-gray-500">{user.escalation_severity || 'Stable'}</span>
                                        )}
                                    </td>
                                    <td className="py-3 px-4">
                                        <button
                                            onClick={() => navigate(`/user/${user.user_id}`)}
                                            className="text-sm text-vortex-accent hover:text-vortex-accent-hover"
                                        >
                                            Investigate
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Attack Patterns */}
            <div className="card">
                <h3 className="text-lg font-semibold mb-4">Detected Attack Patterns</h3>
                <p className="text-sm text-gray-400 mb-4">
                    Common behavioral sequences associated with insider threats
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {attackPatterns.map((pattern, idx) => (
                        <div
                            key={idx}
                            className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-vortex-accent transition-colors"
                        >
                            <div className="flex items-start justify-between mb-3">
                                <div>
                                    <h4 className="font-semibold mb-1">{pattern.pattern_name || `Pattern #${idx + 1}`}</h4>
                                    <p className="text-xs text-gray-400">
                                        {(pattern.occurrence_count || 0)} occurrences • {(pattern.unique_users || 0)} users
                                    </p>
                                </div>
                                <RiskBadge level={pattern.avg_severity} />
                            </div>

                            <div className="space-y-2">
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-400">Avg Chain Length</span>
                                    <span className="font-mono">{(pattern.avg_chain_length || 0).toFixed(1)} events</span>
                                </div>
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-400">Avg Duration</span>
                                    <span className="font-mono">{(pattern.avg_duration_hours || 0).toFixed(1)}h</span>
                                </div>
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-gray-400">Avg Risk Score</span>
                                    <span className="font-mono text-risk-high">{(pattern.avg_risk_score || 0).toFixed(3)}</span>
                                </div>
                            </div>

                            {pattern.common_features && pattern.common_features.length > 0 && (
                                <div className="mt-3 pt-3 border-t border-gray-700">
                                    <p className="text-xs text-gray-400 mb-2">Common Features:</p>
                                    <div className="flex flex-wrap gap-1">
                                        {pattern.common_features.slice(0, 3).map((feature, fidx) => (
                                            <span key={fidx} className="text-xs bg-gray-700 px-2 py-1 rounded">
                                                {feature.replace(/_/g, ' ')}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>

                {attackPatterns.length === 0 && (
                    <div className="text-center py-12 text-gray-400">
                        No attack patterns detected yet
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default Analytics;
