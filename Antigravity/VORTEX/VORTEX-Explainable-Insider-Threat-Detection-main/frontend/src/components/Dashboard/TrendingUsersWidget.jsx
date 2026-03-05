import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, AlertTriangle, User } from 'lucide-react';
import { getTrendingUsers } from '../../services/api';

const TrendingUsersWidget = () => {
    const [trendingUsers, setTrendingUsers] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchTrendingUsers();
        // Auto-refresh every 30 seconds
        const interval = setInterval(fetchTrendingUsers, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchTrendingUsers = async () => {
        try {
            const data = await getTrendingUsers();
            // Get top 6 users
            const users = Array.isArray(data) ? data : [];
            setTrendingUsers(users.slice(0, 6));
            setLoading(false);
        } catch (error) {
            console.error('Error fetching trending users:', error);
            setLoading(false);
        }
    };

    const getSeverityClass = (severity) => {
        switch (severity?.toLowerCase()) {
            case 'critical':
                return 'pulse-red';
            case 'high':
                return 'bg-risk-high';
            case 'medium':
                return 'bg-risk-medium';
            default:
                return 'bg-gray-600';
        }
    };

    if (loading) {
        return (
            <div className="card">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <TrendingUp className="w-5 h-5 text-red-500" />
                        Trending High-Risk Users
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
                    <TrendingUp className="w-5 h-5 text-red-500" />
                    Trending High-Risk Users
                </h3>
                <span className="text-xs text-gray-400">Top 5 Escalating</span>
            </div>

            {trendingUsers.length === 0 ? (
                <p className="text-gray-400 text-center py-4">No trending users</p>
            ) : (
                <div className="space-y-3">
                    {trendingUsers.map((user, index) => (
                        <Link
                            key={user.user_id}
                            to={`/user/${user.user_id}`}
                            className={`block p-3 rounded-lg border transition-all hover:border-purple-500 ${user.escalation_severity === 'Critical'
                                ? 'border-red-500 bg-red-500/10 pulse-border'
                                : 'border-gray-700 bg-gray-800/50'
                                }`}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    {/* Rank Badge */}
                                    <div
                                        className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${index === 0
                                            ? 'bg-yellow-500 text-gray-900'
                                            : index === 1
                                                ? 'bg-gray-400 text-gray-900'
                                                : index === 2
                                                    ? 'bg-orange-600 text-white'
                                                    : 'bg-gray-700 text-gray-300'
                                            }`}
                                    >
                                        {index + 1}
                                    </div>

                                    {/* User Info */}
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <User className="w-4 h-4 text-gray-400" />
                                            <span className="font-medium">{user.user_id}</span>
                                        </div>
                                        <div className="text-xs text-gray-400 mt-0.5">
                                            {user.recent_event_count || user.recent_events || 0} events last 7 days
                                        </div>
                                    </div>
                                </div>

                                {/* Risk Indicator */}
                                <div className="text-right">
                                    <div className="flex items-center gap-2 justify-end">
                                        {user.escalation_severity === 'Critical' && (
                                            <AlertTriangle className="w-4 h-4 text-red-500 animate-pulse" />
                                        )}
                                        <span
                                            className={`text-lg font-bold ${(user.percent_change || user.percent_increase || 0) >= 50
                                                ? 'text-red-500'
                                                : (user.percent_change || user.percent_increase || 0) >= 25
                                                    ? 'text-orange-500'
                                                    : 'text-yellow-500'
                                                }`}
                                        >
                                            +{Math.round(user.percent_change || user.percent_increase || 0)}%
                                        </span>
                                    </div>
                                    <div className="text-xs text-gray-400 mt-0.5">
                                        {user.escalation_severity || 'Medium'} Escalation
                                    </div>
                                </div>
                            </div>

                            {/* Risk Bar */}
                            <div className="mt-3 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                                <div
                                    className={`h-full transition-all ${getSeverityClass(
                                        user.escalation_severity
                                    )}`}
                                    style={{
                                        width: `${Math.min(user.percent_change || user.percent_increase || 0, 100)}%`,
                                    }}
                                ></div>
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
};

export default TrendingUsersWidget;
