import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout/Layout';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import RiskBadge from '../components/Common/RiskBadge';
import { ArrowLeft, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { getExplanation, getRiskEvents } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const EventDetail = () => {
    const { eventId } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [explanation, setExplanation] = useState(null);
    const [eventInfo, setEventInfo] = useState(null);

    useEffect(() => {
        fetchEventDetails();
    }, [eventId]);

    const fetchEventDetails = async () => {
        try {
            setLoading(true);

            // Fetch explanation
            const explData = await getExplanation(eventId);
            setExplanation(explData);

            // Fetch event basic info
            const events = await getRiskEvents({});
            const event = events.find(e => e.event_id === eventId);
            setEventInfo(event);
        } catch (error) {
            console.error('Error fetching event details:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Layout title="Event Details" subtitle={`Loading ${eventId}...`}>
                <LoadingSpinner size={48} className="h-96" />
            </Layout>
        );
    }

    if (!explanation || !eventInfo) {
        return (
            <Layout title="Event Details" subtitle="Event not found">
                <div className="card">
                    <p className="text-gray-400">Unable to load event details.</p>
                    <button onClick={() => navigate('/alerts')} className="btn-primary mt-4">
                        Back to Alerts
                    </button>
                </div>
            </Layout>
        );
    }

    // Prepare chart data
    const chartData = explanation.explanation
        .sort((a, b) => Math.abs(b.shap_contribution) - Math.abs(a.shap_contribution))
        .slice(0, 10)
        .map(item => ({
            feature: item.feature.replace(/_/g, ' ').replace(/zscore/g, ''),
            value: item.shap_contribution,
            isHighRisk: item.is_high_risk_contributor,
        }));

    // Lightweight markdown → JSX renderer helpers
    // Handles: **bold**, *italic*
    const inlineFormat = (str, key) => {
        if (!str) return null;
        // Split on **bold** and *italic* markers
        const parts = str.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);
        return (
            <span key={key}>
                {parts.map((part, i) => {
                    if (part.startsWith('**') && part.endsWith('**'))
                        return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
                    if (part.startsWith('*') && part.endsWith('*'))
                        return <em key={i} className="text-gray-400 not-italic">{part.slice(1, -1)}</em>;
                    return part;
                })}
            </span>
        );
    };

    // Handles: **bold**, *italic*, numbered list items, blank lines
    const renderNarrative = (text) => {
        if (!text) return null;
        const lines = text.split('\n');

        const elements = [];
        let listItems = [];

        const flushList = () => {
            if (listItems.length) {
                elements.push(
                    <ol key={`list-${elements.length}`} className="space-y-1.5 my-3 ml-1">
                        {listItems.map((item, i) => (
                            <li key={i} className="flex gap-2 text-gray-300">
                                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-red-900/60 text-red-300 flex items-center justify-center text-2xs font-bold mt-0.5">{i + 1}</span>
                                <span>{inlineFormat(item, i)}</span>
                            </li>
                        ))}
                    </ol>
                );
                listItems = [];
            }
        };

        lines.forEach((line, idx) => {
            const numbered = line.match(/^\d+\.\s+(.+)$/);
            if (numbered) {
                listItems.push(numbered[1]);
            } else {
                flushList();
                if (line.trim() === '') {
                    elements.push(<div key={`br-${idx}`} className="h-2" />);
                } else {
                    elements.push(
                        <p key={idx} className="text-gray-300 leading-relaxed">
                            {inlineFormat(line, idx)}
                        </p>
                    );
                }
            }
        });
        flushList();
        return elements;
    };

    return (
        <Layout
            title={`Event: ${eventId}`}
        >
            {/* Back Button */}
            <button
                onClick={() => navigate('/alerts')}
                className="flex items-center space-x-2 text-gray-400 hover:text-white mb-6 transition-colors"
            >
                <ArrowLeft size={20} />
                <span>Back to Alerts</span>
            </button>

            {/* Event Summary Card */}
            <div className="card mb-6">
                <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center space-x-3 mb-4">
                            <h2 className="text-2xl font-bold">Event Summary</h2>
                            <RiskBadge level={eventInfo.risk_level} />
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                            <div className="min-w-0">
                                <p className="text-sm text-gray-400 mb-1">Event ID</p>
                                <p className="font-mono text-lg truncate text-white" title={eventInfo.event_id}>{eventInfo.event_id}</p>
                            </div>
                            <div className="min-w-0">
                                <p className="text-sm text-gray-400 mb-1">User ID</p>
                                <button
                                    onClick={() => navigate(`/user/${eventInfo.user_id}`)}
                                    className="text-lg text-vortex-accent hover:text-vortex-accent-hover truncate block w-full text-left"
                                    title={eventInfo.user_id}
                                >
                                    {eventInfo.user_id}
                                </button>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400 mb-1">Timestamp</p>
                                <p className="text-lg text-white whitespace-nowrap">{new Date(eventInfo.timestamp).toLocaleString('en-GB')}</p>
                            </div>
                            <div>
                                <p className="text-sm text-gray-400 mb-1">Anomaly Score</p>
                                <p className="text-2xl font-bold text-risk-critical">
                                    {eventInfo.anomaly_score.toFixed(3)}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="flex items-center space-x-2 flex-shrink-0">
                        {eventInfo.anomaly_flag_truth === 1 ? (
                            <div className="flex items-center space-x-2 bg-red-900/30 border border-red-500/30 px-4 py-2 rounded-lg whitespace-nowrap">
                                <XCircle size={20} className="text-red-400" />
                                <span className="text-red-200 font-semibold">Confirmed Anomaly</span>
                            </div>
                        ) : (
                            <div className="flex items-center space-x-2 bg-green-900/30 border border-green-500/30 px-4 py-2 rounded-lg whitespace-nowrap">
                                <CheckCircle size={20} className="text-green-400" />
                                <span className="text-green-200 font-semibold">Normal Behavior</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Threat Narrative */}
            {explanation.narrative && (
                <div className="card mb-6 border-l-4 border-risk-critical">
                    <div className="flex items-start space-x-3 mb-3">
                        <AlertTriangle size={24} className="text-risk-critical flex-shrink-0 mt-1" />
                        <div className="flex-1">
                            <h3 className="text-lg font-semibold mb-3">Threat Narrative</h3>
                            <div className="space-y-0.5">
                                {renderNarrative(explanation.narrative)}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* SHAP Feature Contributions */}
            <div className="card mb-6">
                <h3 className="text-lg font-semibold mb-4">Feature Contributions (SHAP Analysis)</h3>
                <p className="text-sm text-gray-400 mb-4">
                    Base value: <span className="font-mono">{explanation.base_value.toFixed(4)}</span>
                </p>

                <ResponsiveContainer width="100%" height={400}>
                    <BarChart data={chartData} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis type="number" stroke="#9ca3af" />
                        <YAxis
                            dataKey="feature"
                            type="category"
                            width={150}
                            stroke="#9ca3af"
                            style={{ fontSize: '12px' }}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1f2937', border: 'none' }}
                            formatter={(value) => value.toFixed(4)}
                        />
                        <Bar dataKey="value">
                            {chartData.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={entry.value > 0 ? '#ef4444' : '#10b981'}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>

            {/* Detailed Feature Table */}
            <div className="card mb-6">
                <h3 className="text-lg font-semibold mb-4">Detailed Feature Analysis</h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-800">
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Feature</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Value at Risk</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">SHAP Contribution</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Impact</th>
                            </tr>
                        </thead>
                        <tbody>
                            {explanation.explanation
                                .sort((a, b) => Math.abs(b.shap_contribution) - Math.abs(a.shap_contribution))
                                .map((feature, idx) => (
                                    <tr key={idx} className="border-b border-gray-800">
                                        <td className="py-3 px-4 text-sm">
                                            {feature.feature.replace(/_/g, ' ')}
                                        </td>
                                        <td className="py-3 px-4 text-sm font-mono">
                                            {feature.value_at_risk.toFixed(4)}
                                        </td>
                                        <td className="py-3 px-4 text-sm font-mono">
                                            <span className={feature.shap_contribution > 0 ? 'text-risk-critical' : 'text-risk-low'}>
                                                {feature.shap_contribution > 0 ? '+' : ''}
                                                {feature.shap_contribution.toFixed(4)}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4">
                                            {feature.is_high_risk_contributor ? (
                                                <span className="badge badge-high">High Risk</span>
                                            ) : (
                                                <span className="badge bg-gray-700 text-gray-300">Low Impact</span>
                                            )}
                                        </td>
                                    </tr>
                                ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Mitigation Suggestions */}
            {explanation.mitigation_suggestions && explanation.mitigation_suggestions.length > 0 && (
                <div className="card border-l-4 border-blue-500">
                    <h3 className="text-lg font-semibold mb-4">Recommended Mitigation Actions</h3>
                    <ol className="space-y-3">
                        {explanation.mitigation_suggestions.map((suggestion, idx) => (
                            <li key={idx} className="flex items-start space-x-3">
                                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs font-bold">
                                    {idx + 1}
                                </span>
                                <p className="text-gray-300 flex-1">{inlineFormat(suggestion, idx)}</p>
                            </li>
                        ))}
                    </ol>
                </div>
            )}
        </Layout>
    );
};

export default EventDetail;
