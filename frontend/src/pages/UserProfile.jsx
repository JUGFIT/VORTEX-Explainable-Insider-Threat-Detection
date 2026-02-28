import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout/Layout';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import RiskBadge from '../components/Common/RiskBadge';
import BehavioralBadge from '../components/UserProfile/BehavioralBadge';
import ChainTimeline from '../components/UserProfile/ChainTimeline';
import {
    ArrowLeft, TrendingUp, TrendingDown, AlertTriangle,
    Calendar, Shield, User, Activity, Clock, FileText,
    ExternalLink, HardDrive, Zap, X, ShieldAlert, Sliders, CheckCircle2, Search, Info
} from 'lucide-react';
import { getUserBaseline, getUserTrajectory, getUserRisks, getUserChains, getUserChainsList, getUserEscalation, getUserPatterns, getSimulationStatus } from '../services/api';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, Legend, AreaChart, Area, BarChart, Bar, ReferenceLine
} from 'recharts';

const UserProfile = () => {
    const { userId } = useParams();
    const navigate = useNavigate();

    // State
    const [currentTimeWindow, setCurrentTimeWindow] = useState(30);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [baseline, setBaseline] = useState(null);
    const [trajectory, setTrajectory] = useState(null);
    const [recentEvents, setRecentEvents] = useState([]);
    const [chains, setChains] = useState([]);
    const [chainsSummary, setChainsSummary] = useState({ total_chains: 0 });
    const [escalation, setEscalation] = useState(null);
    const [patterns, setPatterns] = useState([]);
    const [simSnapshot, setSimSnapshot] = useState(null);   // before-injection snapshot
    const [simCurrent, setSimCurrent] = useState(null);    // live status

    useEffect(() => {
        fetchUserProfile(currentTimeWindow);
    }, [userId, currentTimeWindow]);

    const fetchUserProfile = async (days) => {
        try {
            if (loading) setLoading(true);
            else setRefreshing(true);

            const [
                baselineData,
                trajectoryData,
                risksData,
                chainsSummaryData,
                chainsListData,
                escalationData,
                patternsData
            ] = await Promise.all([
                getUserBaseline(userId),
                getUserTrajectory(userId, days),
                getUserRisks(userId).catch(() => ({ recent_events: [] })),
                getUserChains(userId).catch(() => ({ total_chains: 0, chains_by_severity: {}, chains_by_type: {} })),
                getUserChainsList(userId).catch(() => []),
                getUserEscalation(userId).catch(() => null),
                getUserPatterns(userId).catch(() => [])
            ]);

            setBaseline(baselineData);
            setTrajectory(trajectoryData);
            setRecentEvents(risksData.recent_events || []);
            setChainsSummary(chainsSummaryData);
            setChains(chainsListData);
            setEscalation(escalationData || trajectoryData.escalation_details);
            setPatterns(patternsData);

            // Fetch live simulation status
            const simStatus = await getSimulationStatus(userId).catch(() => null);
            setSimCurrent(simStatus);
        } catch (error) {
            console.error('Error fetching user profile:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleTimeWindowChange = (days) => {
        setCurrentTimeWindow(days);
    };

    const handleRefresh = () => {
        fetchUserProfile(currentTimeWindow);
    };

    // Capture a snapshot BEFORE injection so we can show the delta
    const captureSnapshot = async () => {
        try {
            const status = await getSimulationStatus(userId);
            setSimSnapshot(status);
            // Show a brief visual confirmation instead of a blocking alert
        } catch (e) {
            console.error('Failed to capture snapshot:', e.message);
        }
    };

    const clearSnapshot = () => setSimSnapshot(null);

    const timeOptions = [
        { label: '24 Hours', value: 1 },
        { label: '1 Week', value: 7 },
        { label: '30 Days', value: 30 },
        { label: '90 Days', value: 90 },
    ];

    // ── Normalise trajectory to 0-100 Risk % ──────────────────────────────
    // Isolation Forest scores are negative (more negative = higher anomaly).
    // We flip and scale them so 0 = perfectly normal, 100 = maximum threat.
    // Cumulative risk is also normalised independently so both lines stay
    // readable on the same 0-100 scale (dual Y-axes under the hood).
    const chartData = useMemo(() => {
        if (!trajectory?.trajectory?.length) return [];
        const raw = trajectory.trajectory.map(d => d.avg_risk ?? 0);
        const rawCum = trajectory.trajectory.map(d => d.running_cumulative_risk ?? d.cumulative_risk ?? 0);

        const minVal = Math.min(...raw); const maxVal = Math.max(...raw); const range = maxVal - minVal || 1;
        const minCum = Math.min(...rawCum); const maxCum = Math.max(...rawCum); const rangeCum = maxCum - minCum || 1;

        // baseline on the same normalised daily-risk scale
        const rawBaseline = baseline?.baseline?.baseline_score ?? 0;
        const baselinePct = Math.round(((maxVal - rawBaseline) / range) * 100);

        return trajectory.trajectory.map((d, i) => {
            const score = d.avg_risk ?? 0;
            const riskPct = Math.round(((maxVal - score) / range) * 100);
            // cumulative: higher running total = more suspicious, so map max->100
            const cum = rawCum[i];
            const cumulativePct = Math.round(((cum - minCum) / rangeCum) * 100);
            return {
                date: d.date,
                riskPct,
                cumulativePct,
                baselinePct,
                aboveBaseline: riskPct > baselinePct,
                events: d.events,
                high: d.high_risk_events,
            };
        });
    }, [trajectory, baseline]);

    if (loading) {
        return (
            <Layout title={`System Identity: ${userId}`}>
                <div className="flex flex-col items-center justify-center h-[60vh]">
                    <LoadingSpinner size={64} />
                    <p className="text-gray-500 mt-6 font-mono animate-pulse uppercase tracking-widest text-xs">
                        Accessing Secure Behavioral Repository
                    </p>
                </div>
            </Layout>
        );
    }

    if (!baseline || !trajectory) {
        return (
            <Layout title={`Identity Error: ${userId}`} subtitle="The requested profile could not be localized">
                <div className="card max-w-lg mx-auto mt-20 text-center border-red-500/20">
                    <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
                        <AlertTriangle className="text-red-500 w-8 h-8" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">Internal Profile Missing</h3>
                    <p className="text-gray-400 mb-6">The behavioral manager was unable to locate a verified baseline for user <span className="text-white font-mono">{userId}</span>.</p>
                    <button onClick={() => navigate('/users')} className="btn-primary flex items-center justify-center gap-2 w-full">
                        <ArrowLeft size={18} />
                        Return to User Directory
                    </button>
                </div>
            </Layout>
        );
    }

    return (
        <Layout title={`Agent Identity: ${userId}`}>
            {/* Action Bar */}
            <div className="flex items-center gap-4 mb-8">
                <button
                    onClick={() => navigate('/users')}
                    className="flex items-center space-x-2 text-gray-500 hover:text-white transition-colors group"
                >
                    <ArrowLeft size={20} className="group-hover:-translate-x-1 transition-transform" />
                    <span className="font-bold uppercase tracking-wider text-xs">Behavioral Database</span>
                </button>
                <div className="ml-auto flex items-center gap-2">
                    {refreshing && <div className="animate-spin h-4 w-4 border-2 border-vortex-accent border-t-transparent rounded-full" />}
                    <button
                        onClick={handleRefresh}
                        disabled={refreshing}
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white border border-gray-700 transition-all disabled:opacity-50"
                        title="Refresh profile data (use after threat injection)"
                    >
                        <Activity size={13} className={refreshing ? 'animate-spin' : ''} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* ── Before / After Injection Comparison Panel ── */}
            <div className={`mb-8 rounded-2xl border p-5 ${simSnapshot ? 'border-purple-500/40 bg-purple-500/5' : 'border-gray-800 bg-gray-900/40'}`}>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
                    <div className="flex items-center gap-3">
                        <Zap className="w-5 h-5 text-purple-400" />
                        <div>
                            <h3 className="font-black text-sm uppercase tracking-widest text-gray-300">Injection Impact Tracker</h3>
                            <p className="text-2xs text-gray-500 mt-0.5">
                                {simSnapshot
                                    ? 'Snapshot captured. Inject a threat, then refresh to see the delta.'
                                    : 'Capture a baseline snapshot before injecting a threat to measure impact.'}
                            </p>
                        </div>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={captureSnapshot}
                            className="btn-secondary text-xs px-4 py-2 flex items-center gap-2"
                            style={{ borderColor: 'rgba(168,85,247,0.4)' }}
                        >
                            <ShieldAlert size={14} className="text-purple-400" />
                            {simSnapshot ? 'Re-Capture Snapshot' : 'Capture Snapshot (Before)'}
                        </button>
                        {simSnapshot && (
                            <button onClick={clearSnapshot} className="btn-secondary text-xs px-3 py-2 flex items-center gap-1 text-gray-500">
                                <X size={12} /> Clear
                            </button>
                        )}
                    </div>
                </div>

                {simCurrent && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {[
                            { label: 'Total Events', before: simSnapshot?.total_events, after: simCurrent.total_events, fmt: v => v?.toLocaleString() ?? '—', higherIsBad: true },
                            { label: 'High Risk Events', before: simSnapshot?.high_risk_events, after: simCurrent.high_risk_events, fmt: v => v?.toLocaleString() ?? '—', higherIsBad: true },
                            { label: 'Avg Anomaly Score', before: simSnapshot?.avg_anomaly_score, after: simCurrent.avg_anomaly_score, fmt: v => v != null ? v.toFixed(4) : '—', higherIsBad: true },
                            { label: 'Baseline Score', before: simSnapshot?.baseline_score, after: simCurrent.baseline_score, fmt: v => v != null ? v.toFixed(4) : '—', higherIsBad: true },
                        ].map(({ label, before, after, fmt, higherIsBad }) => {
                            const hasBefore = before != null;
                            const delta = hasBefore ? after - before : null;
                            const isWorse = delta != null && (higherIsBad ? delta > 0 : delta < 0);
                            const isBetter = delta != null && (higherIsBad ? delta < 0 : delta > 0);
                            return (
                                <div key={label} className="bg-gray-950/60 rounded-xl p-4 border border-gray-800 flex flex-col justify-between">
                                    <div className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-3">{label}</div>
                                    <div className="flex items-end justify-between">
                                        <div className="flex flex-col">
                                            <div className="text-[10px] text-gray-600 uppercase font-bold mb-1">{hasBefore ? 'Current (After)' : 'Current Value'}</div>
                                            <div className={`text-xl font-black font-mono tracking-tight ${isWorse ? 'text-red-400' : isBetter ? 'text-green-400' : 'text-white'}`}>
                                                {fmt(after)}
                                            </div>
                                        </div>
                                        {hasBefore && (
                                            <div className="flex flex-col items-end text-right">
                                                <div className="text-[10px] text-gray-600 uppercase font-bold mb-1">Baseline</div>
                                                <div className="text-sm font-mono text-gray-400 opacity-60 line-through mb-0.5">{fmt(before)}</div>
                                                <div className={`text-xs font-bold font-mono px-1.5 py-0.5 rounded bg-gray-900/80 ${isWorse ? 'text-red-400' : isBetter ? 'text-green-400' : 'text-gray-500'}`}>
                                                    {delta > 0 ? '+' : ''}{typeof delta === 'number' && delta % 1 !== 0 ? delta.toFixed(4) : delta}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Profile Overview Header */}

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
                <div className="lg:col-span-1 card bg-gradient-to-br from-gray-900 to-black border-vortex-accent/30 relative overflow-hidden">
                    <div className="absolute -right-4 -top-4 w-24 h-24 bg-vortex-accent/10 blur-3xl rounded-full"></div>
                    <div className="relative z-10 flex flex-col items-center py-4">
                        <div className="w-20 h-20 bg-gray-800 rounded-2xl flex items-center justify-center mb-4 shadow-2xl border border-gray-700">
                            <User size={40} className="text-vortex-accent" />
                        </div>
                        <h2 className="text-2xl font-black text-white">{userId}</h2>
                        <p className="text-2xs text-vortex-accent font-bold uppercase tracking-widest mt-1">Verified Organizational Identity</p>

                        <div className="mt-6 w-full space-y-3 px-2">
                            <div className="flex justify-between py-2 border-b border-gray-800">
                                <span className="text-xs text-gray-500 uppercase font-bold">Status</span>
                                <span className="text-xs font-bold text-green-500 flex items-center gap-1">
                                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                                    Active
                                </span>
                            </div>
                            <div className="flex justify-between py-2">
                                <span className="text-xs text-gray-500 uppercase font-bold">Risk Level</span>
                                <RiskBadge level={baseline.baseline_risk_level} />
                            </div>
                        </div>
                    </div>
                </div>

                <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Personalized Baseline Card */}
                    <div className="card flex flex-col justify-between">
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Shield className="w-4 h-4 text-vortex-accent" />
                                <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Personalized Baseline</h3>
                            </div>
                            <div className="text-4xl font-black text-white mb-2">
                                {baseline.baseline?.baseline_score?.toFixed(3) || '0.000'}
                            </div>
                            <p className="text-xs text-gray-500 leading-relaxed">
                                Standardized behavioral deviation based on historical audit telemetry.
                            </p>
                        </div>
                        <div className="mt-4 flex items-center justify-between pt-4 border-t border-gray-800">
                            <span className="text-2xs font-bold text-gray-500 uppercase">Detection Confidence</span>
                            <span className="text-xs font-mono font-bold text-vortex-accent">{((baseline.data_quality?.confidence || 0) * 100).toFixed(0)}%</span>
                        </div>
                    </div>

                    {/* Trend Indicator */}
                    <div className={`card flex flex-col justify-between border-l-4 transition-all ${trajectory.trend?.toLowerCase() === 'escalating'
                        ? 'border-l-red-500 bg-red-500/5'
                        : trajectory.trend?.toLowerCase() === 'declining'
                            ? 'border-l-green-500 bg-green-500/5'
                            : 'border-l-blue-500 bg-blue-500/5'
                        }`}>
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Activity className="w-4 h-4 text-gray-400" />
                                <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Risk Trajectory</h3>
                            </div>
                            <div className={`text-3xl font-black mb-2 flex items-center gap-3 transition-colors ${trajectory.trend?.toLowerCase() === 'escalating'
                                ? 'text-red-500'
                                : trajectory.trend?.toLowerCase() === 'declining'
                                    ? 'text-green-500'
                                    : 'text-blue-500'
                                }`}>
                                <span className="capitalize">{trajectory.trend}</span>
                                {trajectory.trend?.toLowerCase() === 'escalating' ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
                            </div>
                            <p className="text-xs text-gray-500 leading-relaxed">
                                Current trend based on the last {currentTimeWindow} days of security events.
                            </p>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-800/30">
                            <div className="flex justify-between items-center">
                                <span className="text-2xs font-bold text-gray-500 uppercase">Cumulative Score</span>
                                <span className="text-xs font-bold font-mono">{(trajectory?.current_cumulative_risk || 0).toFixed(1)}</span>
                            </div>
                        </div>
                    </div>

                    {/* Meta Info */}
                    <div className="card flex flex-col justify-between">
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Clock className="w-4 h-4 text-orange-500" />
                                <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Activity Stats</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <div className="text-2xl font-black text-white">{trajectory.summary.total_events}</div>
                                    <div className="text-2xs text-gray-500 uppercase font-bold">Total Operations</div>
                                </div>
                                <div>
                                    <div className="text-2xl font-black text-red-500">{trajectory.summary.high_risk_count}</div>
                                    <div className="text-2xs text-gray-500 uppercase font-bold">High Risk Events</div>
                                </div>
                            </div>
                        </div>
                        <div className="mt-4 pt-4 border-t border-gray-800">
                            <div className="flex justify-between items-center">
                                <span className="text-2xs font-bold text-gray-500 uppercase">Alert Chains Detected</span>
                                <span className="text-xs font-bold font-mono text-orange-500">{chainsSummary.total_chains || 0}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main Content: Chart & Behavioral Fingerprint */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                {/* Visual Trajectory Chart */}
                <div className="lg:col-span-2 card bg-gray-950/40 relative">

                    {/* Chart header: title + time selector side by side */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                        <div>
                            <h3 className="text-lg font-bold">Risk Progression Map</h3>
                            <p className="text-2xs text-gray-500 italic mt-0.5">Points represent daily aggregates; large markers indicate high-risk events.</p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                            {refreshing && <div className="animate-spin h-4 w-4 border-2 border-vortex-accent border-t-transparent rounded-full"></div>}
                            <div className="bg-gray-900/80 p-1 rounded-xl border border-gray-800 flex items-center">
                                {timeOptions.map((opt) => (
                                    <button
                                        key={opt.value}
                                        onClick={() => handleTimeWindowChange(opt.value)}
                                        className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${currentTimeWindow === opt.value
                                            ? 'bg-vortex-accent text-white shadow-lg'
                                            : 'text-gray-500 hover:text-gray-300'
                                            }`}
                                    >
                                        {opt.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Compact legend */}
                    <div className="flex items-center gap-5 mb-4 px-1">
                        <div className="flex items-center gap-1.5 cursor-default" title="Daily Risk % — how risky this user's activity was each day (0 = normal, 100 = maximum threat)">
                            <div className="w-6 h-2.5 rounded-sm" style={{ background: 'linear-gradient(to bottom, rgba(239,68,68,0.55), rgba(239,68,68,0.05))' }} />
                            <span className="text-xs text-gray-500 font-medium">Daily Risk %</span>
                        </div>
                        <div className="flex items-center gap-1.5 cursor-default" title="Cumulative Threat Load — total suspicious activity building up over time. A steady climb here reveals slow-burn insider threats that never spike on a single day.">
                            <div className="w-6 h-0" style={{ borderTop: '2px solid #8b5cf6' }} />
                            <span className="text-xs text-gray-500 font-medium">Cumulative Load</span>
                        </div>
                        <div className="flex items-center gap-1.5 cursor-default" title="Baseline — this user's normal expected risk level. Days above this line are suspicious.">
                            <div className="w-6 h-0" style={{ borderTop: '2px dashed #f59e0b' }} />
                            <span className="text-xs text-gray-500 font-medium">Baseline</span>
                        </div>
                    </div>

                    <div className="h-[320px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData} margin={{ top: 10, right: 40, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorRiskPct" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0.03} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    stroke="#4b5563"
                                    fontSize={10}
                                    tickFormatter={(val) => val.split('-').slice(1).join('/')}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                {/* Left axis: Daily Risk % */}
                                <YAxis
                                    yAxisId="left"
                                    stroke="#ef4444"
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    domain={[0, 100]}
                                    tickFormatter={(v) => `${v}%`}
                                    ticks={[0, 25, 50, 75, 100]}
                                    width={36}
                                />
                                {/* Right axis: Cumulative Load % */}
                                <YAxis
                                    yAxisId="right"
                                    orientation="right"
                                    stroke="#8b5cf6"
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    domain={[0, 100]}
                                    tickFormatter={(v) => `${v}%`}
                                    ticks={[0, 50, 100]}
                                    width={36}
                                />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', fontSize: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.5)' }}
                                    formatter={(value, name, props) => {
                                        if (name === 'riskPct') {
                                            const above = props.payload?.aboveBaseline;
                                            const tag = above ? '⚠️ Above Baseline' : '✅ Normal';
                                            return [`${value}%  ${tag}`, 'Daily Risk'];
                                        }
                                        if (name === 'cumulativePct') {
                                            return [`${value}%`, 'Cumulative Load'];
                                        }
                                        return [value, name];
                                    }}
                                    labelFormatter={(label) => `📅 ${label}`}
                                />
                                {/* Baseline threshold */}
                                <ReferenceLine
                                    yAxisId="left"
                                    y={chartData[0]?.baselinePct ?? 50}
                                    stroke="#f59e0b"
                                    strokeDasharray="6 3"
                                    strokeWidth={1.5}
                                    label={{
                                        value: `Baseline ${chartData[0]?.baselinePct ?? 50}%`,
                                        position: 'insideTopRight',
                                        fill: '#f59e0b',
                                        fontSize: 10,
                                        fontWeight: 'bold',
                                    }}
                                />
                                {/* Daily risk area with clickable dots */}
                                <Area
                                    yAxisId="left"
                                    type="monotone"
                                    dataKey="riskPct"
                                    stroke="#ef4444"
                                    strokeWidth={2}
                                    fillOpacity={1}
                                    fill="url(#colorRiskPct)"
                                    name="riskPct"
                                    animationDuration={1000}
                                    dot={(dotProps) => {
                                        const { cx, cy, payload } = dotProps;
                                        if (!payload || cx == null || cy == null) return null;
                                        const isAbove = payload.aboveBaseline;
                                        const r = payload.high > 0 ? 5 : 3;
                                        return (
                                            <circle
                                                key={`dot-${payload.date}`}
                                                cx={cx}
                                                cy={cy}
                                                r={r}
                                                fill={isAbove ? '#ef4444' : '#6b7280'}
                                                stroke={isAbove ? '#fca5a5' : '#374151'}
                                                strokeWidth={1}
                                                style={{ cursor: 'pointer' }}
                                                onClick={() => navigate(`/alerts?user=${encodeURIComponent(userId)}&date=${payload.date}`)}
                                            />
                                        );
                                    }}
                                    activeDot={(dotProps) => {
                                        const { cx, cy, payload } = dotProps;
                                        return (
                                            <circle
                                                key={`adot-${payload?.date}`}
                                                cx={cx}
                                                cy={cy}
                                                r={7}
                                                fill="#ef4444"
                                                stroke="#fca5a5"
                                                strokeWidth={2}
                                                style={{ cursor: 'pointer' }}
                                                onClick={() => navigate(`/alerts?user=${encodeURIComponent(userId)}&date=${payload.date}`)}
                                            />
                                        );
                                    }}
                                />
                                {/* Cumulative threat load line */}
                                <Line
                                    yAxisId="right"
                                    type="monotone"
                                    dataKey="cumulativePct"
                                    stroke="#8b5cf6"
                                    strokeWidth={2}
                                    dot={false}
                                    name="cumulativePct"
                                    animationDuration={1000}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Behavioral Metadata */}
                <div className="lg:col-span-1 card flex flex-col">
                    <h3 className="text-lg font-bold mb-1">Behavioral DNS</h3>
                    <p className="text-2xs text-gray-500 uppercase font-black tracking-widest mb-6">Individualized Feature Attribution</p>

                    <div className="space-y-6 flex-1">
                        <div className="flex flex-wrap gap-2">
                            <BehavioralBadge
                                type="off-hours"
                                value={baseline.behavioral_fingerprint?.after_hours_ratio_mean || 0}
                                threshold={0.3}
                            />
                            <BehavioralBadge
                                type="high-file-access"
                                value={baseline.behavioral_fingerprint?.file_access_events_mean || 0}
                                threshold={10}
                            />
                            <BehavioralBadge
                                type="usb-user"
                                value={baseline.behavioral_fingerprint?.usb_usage_mean || 0}
                                threshold={0.1}
                            />
                            <BehavioralBadge
                                type="sensitive-access"
                                value={baseline.behavioral_fingerprint?.sensitive_files_mean || 0}
                                threshold={0.5}
                            />
                        </div>

                        <div className="bg-gray-900/40 rounded-xl p-4 border border-gray-800/50">
                            <h4 className="text-2xs font-black uppercase tracking-widest text-vortex-accent mb-4">Baseline Comparison (Z-Scores)</h4>
                            <div className="space-y-4">
                                {baseline.behavioral_fingerprint && Object.entries(baseline.behavioral_fingerprint).slice(0, 5).map(([key, value]) => (
                                    <div key={key}>
                                        <div className="flex justify-between text-2xs mb-1 font-bold text-gray-400">
                                            <span className="capitalize">{key.replace(/_/g, ' ').replace('mean', '').trim()}</span>
                                            <span className="font-mono">{typeof value === 'number' ? value.toFixed(3) : value}</span>
                                        </div>
                                        <div className="h-1 w-full bg-gray-800 rounded-full overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-blue-600 to-purple-600"
                                                style={{ width: `${Math.min((value / (key.includes('ratio') ? 1 : 100)) * 100, 100)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="p-3 bg-purple-500/5 border border-purple-500/10 rounded-lg">
                            <h5 className="text-2xs font-black uppercase text-purple-400 mb-1">Observation Note</h5>
                            <p className="text-xs text-gray-500 leading-tight italic">
                                "The agent's behavior is currently benchmarking at <span className="text-white font-bold">{(baseline.baseline_risk_level || 'Unknown').toLowerCase()}</span> levels of organizational risk. Recent file interactions show {(baseline.behavioral_fingerprint?.sensitive_files_mean || 0) > 2 ? 'elevated' : 'normal'} sensitivity access."
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Attack Chains Timeline */}
            {(chainsSummary.total_chains > 0 || chains.length > 0) && (
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-6">
                        <Shield className="w-5 h-5 text-orange-500" />
                        <h3 className="text-xl font-black uppercase tracking-tighter">Detected Threat Chains</h3>
                        <div className="px-2 py-0.5 bg-orange-500/20 text-orange-400 text-2xs font-black rounded-md border border-orange-500/30">
                            CRITICAL SIGNAL
                        </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {Array.isArray(chains) && chains.slice(0, 4).map((chain, idx) => (
                            <ChainTimeline key={chain.chain_id || idx} chain={chain} />
                        ))}
                    </div>
                </div>
            )}

            {/* Bottom Section: Events & Patterns */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Recent Behavior Feed */}
                <div className="lg:col-span-2 card p-0 overflow-hidden">
                    <div className="p-5 border-b border-gray-800 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Activity className="w-4 h-4 text-vortex-accent" />
                            <h3 className="font-bold">Anomalous Activity Feed</h3>
                        </div>
                        <span className="text-2xs font-bold text-gray-500 uppercase">{recentEvents.length} events detected</span>
                    </div>
                    <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left">
                            <thead className="bg-gray-950/50 sticky top-0 z-10 backdrop-blur-md">
                                <tr>
                                    <th className="py-3 px-5 text-2xs font-black uppercase text-gray-500 tracking-widest">Type/Flag</th>
                                    <th className="py-3 px-5 text-2xs font-black uppercase text-gray-500 tracking-widest">Timestamp</th>
                                    <th className="py-3 px-5 text-2xs font-black uppercase text-gray-500 tracking-widest text-right">Risk Score</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800">
                                {recentEvents.map((event) => (
                                    <tr
                                        key={event.event_id}
                                        className="group hover:bg-gray-800/40 transition-colors cursor-pointer"
                                        onClick={() => navigate(`/event/${event.event_id}`)}
                                    >
                                        <td className="py-4 px-5">
                                            <div className="flex items-center gap-3">
                                                <div className="w-8 h-8 rounded bg-gray-900 flex items-center justify-center p-1.5 border border-gray-700 group-hover:border-vortex-accent/40 transition-colors">
                                                    {event.anomaly_score > 0.7 ? <AlertTriangle size={14} className="text-red-500" /> : <HardDrive size={14} className="text-gray-500" />}
                                                </div>
                                                <div>
                                                    <div className="text-xs font-bold text-gray-200 group-hover:text-vortex-accent transition-colors">Event {event.event_id.split('_').pop()}</div>
                                                    <div className="text-2xs text-gray-500 font-mono uppercase">{event.risk_level} SIGNAL</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="py-4 px-5">
                                            <div className="flex items-center gap-2 text-xs text-gray-400">
                                                <Clock size={12} className="text-gray-600" />
                                                {new Date(event.timestamp).toLocaleString('en-GB')}
                                            </div>
                                        </td>
                                        <td className="py-4 px-5 text-right">
                                            <span className={`font-mono font-bold text-sm ${event.anomaly_score > 0.7 ? 'text-red-500' :
                                                event.anomaly_score > 0.4 ? 'text-orange-500' : 'text-gray-400'
                                                }`}>
                                                {(event.anomaly_score || 0).toFixed(3)}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                                {recentEvents.length === 0 && (
                                    <tr>
                                        <td colSpan="3" className="py-20 text-center text-gray-600 italic text-sm">No recent anomalous patterns detected for this identity.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Behavioral Metadata / Patterns */}
                <div className="lg:col-span-1 space-y-6">
                    {/* Identification Card */}
                    <div className="card bg-vortex-accent/5 border-vortex-accent/20">
                        <div className="flex items-center gap-2 mb-4">
                            <FileText className="w-4 h-4 text-vortex-accent" />
                            <h3 className="text-xs font-black uppercase text-gray-400 tracking-widest">Metadata Artifacts</h3>
                        </div>
                        <div className="space-y-4">
                            <div className="bg-black/20 p-3 rounded-lg border border-gray-800">
                                <span className="text-2xs font-bold text-gray-500 uppercase block mb-1">Access Profile</span>
                                <span className="text-xs text-gray-300">Default Organizational User (Tier 2 Analysis)</span>
                            </div>
                            <div className="bg-black/20 p-3 rounded-lg border border-gray-800">
                                <span className="text-2xs font-bold text-gray-500 uppercase block mb-1">Historical Window</span>
                                <span className="text-xs text-gray-300">Continuous monitoring since data initialization</span>
                            </div>
                            {escalation && (
                                <div className={`p-3 rounded-lg border flex items-center justify-between ${escalation.is_escalating ? 'bg-red-500/10 border-red-500/30' : 'bg-green-500/10 border-green-500/30'
                                    }`}>
                                    <span className="text-2xs font-bold uppercase">Dynamic Escalation</span>
                                    <span className={`text-2xs font-black uppercase ${escalation.is_escalating ? 'text-red-500' : 'text-green-500'
                                        }`}>
                                        {escalation.is_escalating ? 'DANGER: ESCALATING' : 'NORMAL: STABLE'}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Quick Access Info */}
                    <div className="card border-dashed border-gray-700 bg-transparent py-4 px-6 flex items-center justify-between">
                        <div className="flex flex-col">
                            <span className="text-2xs font-black text-gray-500 uppercase">Audit Link</span>
                            <span className="text-xs font-mono text-vortex-accent hover:underline cursor-pointer flex items-center gap-1">
                                RAW_JSON_EXPORT_{userId.toUpperCase()}
                                <ExternalLink size={10} />
                            </span>
                        </div>
                        <div className="p-2 bg-gray-800 rounded">
                            <Shield size={18} className="text-gray-600" />
                        </div>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default UserProfile;
