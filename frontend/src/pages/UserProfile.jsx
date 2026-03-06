import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout/Layout';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import RiskBadge from '../components/Common/RiskBadge';
import ChainTimeline from '../components/UserProfile/ChainTimeline';
import {
    ArrowLeft, TrendingUp, TrendingDown, AlertTriangle,
    Shield, User, Activity, Clock,
    HardDrive, ShieldAlert, CheckCircle2,
    Moon, Lock, Wifi, Usb, BarChart2
} from 'lucide-react';
import { getUserBaseline, getUserTrajectory, getUserRisks, getUserChains, getUserChainsList, getUserEscalation, getUserPatterns, getSimulationStatus } from '../services/api';
import {
    Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, AreaChart, Area, ReferenceLine
} from 'recharts';

// ─── Behavioral DNA Metric Panel (compact) ───────────────────────────────────
const BehaviorMetricPanel = ({ icon: Icon, label, userVal, orgVal, unit = '%', color = 'blue' }) => {
    const userPct = Math.min(userVal * 100, 100);
    const orgPct = Math.min(orgVal * 100, 100);
    const ratio = orgVal > 0 ? userVal / orgVal : 1;

    const statusColor = ratio >= 3 ? 'text-red-400' : ratio >= 1.5 ? 'text-yellow-400' : 'text-green-400';
    const barFill = ratio >= 3 ? '#ef4444' : ratio >= 1.5 ? '#f59e0b' : '#10b981';

    const colorMap = {
        blue: 'text-blue-400', purple: 'text-purple-400',
        orange: 'text-orange-400', red: 'text-red-400', yellow: 'text-yellow-400',
    };

    return (
        <div className="flex flex-col gap-1.5 py-2.5 border-b border-gray-800/50 last:border-0">
            {/* Label row */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                    <Icon size={12} className={colorMap[color] || 'text-gray-500'} />
                    <span className="text-xs font-medium text-gray-300">{label}</span>
                </div>
                <span className={`text-2xs font-bold font-mono ${statusColor}`}>
                    {ratio >= 1.5 ? `${ratio.toFixed(1)}× avg` : 'normal'}
                </span>
            </div>
            {/* Thin progress bar */}
            <div className="relative h-1.5 bg-gray-800 rounded-full overflow-visible">
                <div
                    className="absolute left-0 top-0 h-full rounded-full transition-all duration-700"
                    style={{ width: `${Math.min(userPct, 100)}%`, background: barFill, opacity: 0.8 }}
                />
                <div
                    className="absolute top-[-2px] w-px h-[10px] bg-white/50 rounded-full"
                    style={{ left: `${Math.min(orgPct, 100)}%` }}
                    title={`Org avg: ${(orgVal * 100).toFixed(1)}%`}
                />
            </div>
            {/* Values inline */}
            <div className="flex justify-between text-2xs font-mono">
                <span className="text-gray-400">You: <span className="text-white font-semibold">{(userVal * 100).toFixed(1)}{unit}</span></span>
                <span className="text-gray-600">avg {(orgVal * 100).toFixed(1)}{unit}</span>
            </div>
        </div>
    );
};

const UserProfile = () => {
    const { userId } = useParams();
    const navigate = useNavigate();

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
    const [simSnapshot, setSimSnapshot] = useState(null);
    const [simCurrent, setSimCurrent] = useState(null);

    useEffect(() => {
        fetchUserProfile(currentTimeWindow);
    }, [userId, currentTimeWindow]);

    const fetchUserProfile = async (days) => {
        try {
            if (loading) setLoading(true);
            else setRefreshing(true);

            const [
                baselineData, trajectoryData, risksData,
                chainsSummaryData, chainsListData, escalationData, patternsData
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

            const simStatus = await getSimulationStatus(userId).catch(() => null);
            setSimCurrent(simStatus);
        } catch (error) {
            console.error('Error fetching user profile:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleTimeWindowChange = (days) => setCurrentTimeWindow(days);

    const timeOptions = [
        { label: '24 Hours', value: 1 },
        { label: '1 Week', value: 7 },
        { label: '30 Days', value: 30 },
        { label: '90 Days', value: 90 },
    ];

    const chartData = useMemo(() => {
        if (!trajectory?.trajectory?.length) return [];
        const SCORE_CEIL = 0.5;
        const globalP50 = baseline?.global_context?.global_p50 ?? 0.15;
        const baselinePct = Math.round((globalP50 / SCORE_CEIL) * 100);
        const rawCum = trajectory.trajectory.map(d => d.running_cumulative_risk ?? d.cumulative_risk ?? 0);
        const maxCum = Math.max(...rawCum, 1);
        return trajectory.trajectory.map((d, i) => {
            const score = d.avg_risk ?? 0;
            const riskPct = Math.max(0, Math.min(100, Math.round((score / SCORE_CEIL) * 100)));
            const cum = rawCum[i] ?? 0;
            const cumulativePct = Math.round((cum / maxCum) * 100);
            return { date: d.date, riskPct, cumulativePct, baselinePct, aboveBaseline: riskPct > baselinePct, events: d.events, high: d.high_risk_events };
        });
    }, [trajectory, baseline]);

    // ── Loading / error states ────────────────────────────────────────────────
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

    // ── Derived values ────────────────────────────────────────────────────────
    const gc = baseline?.global_context || {};
    const zscore = gc.zscore_vs_global ?? 0;
    const metrics = gc.metrics || {};

    const zscoreColor = zscore > 1.5 ? 'text-red-400' : zscore > 0.5 ? 'text-yellow-400' : 'text-green-400';
    const zscoreBg = zscore > 1.5
        ? 'from-red-500/10 to-red-500/0 border-red-500/30'
        : zscore > 0.5
            ? 'from-yellow-500/10 to-yellow-500/0 border-yellow-500/30'
            : 'from-green-500/10 to-green-500/0 border-green-500/30';
    const riskLabel = zscore > 1.5 ? '⬆ High Risk'
        : zscore > 0.5 ? '⬆ Above Average'
            : zscore < -0.5 ? '⬇ Below Average'
                : '↔ Within Norm';

    return (
        <Layout title={`Behavioral Profile: ${userId}`}>

            {/* ── Attack Chain Alert Banner ─────────────────────────────── */}
            {chainsSummary.total_chains > 0 && (
                <div className="mb-8 p-5 rounded-2xl bg-red-500/10 border-2 border-red-500/40 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-11 h-11 bg-red-500 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(239,68,68,0.5)] shrink-0">
                            <ShieldAlert size={22} className="text-white" />
                        </div>
                        <div>
                            <p className="text-xs font-black uppercase tracking-widest text-red-400 mb-0.5">Multi-Stage Threat</p>
                            <h3 className="text-base font-black text-white">Attack Chain Detected</h3>
                            <p className="text-xs text-red-200/70 mt-0.5">This user is following a multi-stage malicious sequence tracking toward data exfiltration.</p>
                        </div>
                    </div>
                    <button
                        onClick={() => { const el = document.getElementById('chains-section'); if (el) el.scrollIntoView({ behavior: 'smooth' }); }}
                        className="shrink-0 px-5 py-2 bg-red-500 text-white font-black text-xs uppercase tracking-widest rounded-lg hover:bg-red-600 transition-all shadow-lg"
                    >
                        Analyze Chain
                    </button>
                </div>
            )}

            {/* ── Profile Header Row ────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-6">

                {/* Identity Card */}
                <div className="lg:col-span-1 card bg-gradient-to-br from-gray-900 to-black border-vortex-accent/30 relative overflow-hidden">
                    <div className="absolute -right-4 -top-4 w-24 h-24 bg-vortex-accent/10 blur-3xl rounded-full" />
                    <div className="relative z-10 flex flex-col items-center py-3">
                        <div className="w-16 h-16 bg-gray-800 rounded-2xl flex items-center justify-center mb-3 shadow-2xl border border-gray-700">
                            <User size={32} className="text-vortex-accent" />
                        </div>
                        <h2 className="text-xl font-black text-white">{userId}</h2>
                        <p className="text-2xs text-vortex-accent font-bold uppercase tracking-widest mt-1">Verified Identity</p>

                        <div className="mt-5 w-full space-y-2 px-2">
                            <div className="flex justify-between items-center py-2 border-b border-gray-800/50">
                                <span className="text-2xs font-bold text-gray-500 uppercase tracking-wider">Status</span>
                                <span className="text-xs font-bold text-green-400 flex items-center gap-1.5">
                                    <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
                                    Active
                                </span>
                            </div>
                            <div className="flex justify-between items-center py-2">
                                <span className="text-2xs font-bold text-gray-500 uppercase tracking-wider">Risk Level</span>
                                <RiskBadge level={baseline.baseline_risk_level} />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Metric Cards */}
                <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6">

                    {/* Risk vs Organisation */}
                    <div className={`card flex flex-col justify-between bg-gradient-to-br ${zscoreBg} border`}>
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <BarChart2 className="w-4 h-4 text-gray-400" />
                                <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Risk vs Organisation</h3>
                            </div>
                            <div className={`text-3xl font-black mb-1 ${zscoreColor}`}>
                                {zscore >= 0 ? '+' : ''}{zscore.toFixed(2)}σ
                            </div>
                            <p className={`text-xs font-bold mb-2 ${zscoreColor}`}>{riskLabel}</p>
                            <p className="text-2xs text-gray-500 leading-relaxed">
                                User avg: <span className="text-gray-200 font-mono">{gc.user_mean_score?.toFixed(3) ?? 'N/A'}</span>
                                {' · '}Org avg: <span className="text-gray-200 font-mono">{gc.global_mean?.toFixed(3) ?? 'N/A'}</span>
                            </p>
                        </div>
                        <div className="mt-4 flex items-center justify-between pt-3 border-t border-gray-800/50">
                            <span className="text-2xs font-bold text-gray-500 uppercase tracking-wider">Above org p95</span>
                            <span className={`text-xs font-mono font-bold ${(gc.pct_events_above_global_p95 ?? 0) > 5 ? 'text-red-400' : 'text-gray-400'}`}>
                                {(gc.pct_events_above_global_p95 ?? 0).toFixed(1)}%
                            </span>
                        </div>
                    </div>

                    {/* Dynamic Escalation (Replaced Risk Trajectory) */}
                    <div className={`card flex flex-col justify-between border-l-4 ${escalation?.is_escalating ? 'border-l-red-500 bg-red-500/5' : 'border-l-green-500 bg-green-500/5'}`}>
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <ShieldAlert className="w-4 h-4 text-gray-400" />
                                <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Dynamic Escalation</h3>
                            </div>
                            <div className={`text-3xl font-black mb-2 flex items-center gap-2 ${escalation?.is_escalating ? 'text-red-400' : 'text-green-400'}`}>
                                <span>{escalation?.is_escalating ? 'Escalating' : 'Stable'}</span>
                                {escalation?.is_escalating ? <TrendingUp size={24} /> : <CheckCircle2 size={24} />}
                            </div>
                            <p className="text-xs text-gray-500"> Behavioral risk trajectory evaluated against prior 7-day baseline.</p>
                        </div>
                        <div className="mt-4 pt-3 border-t border-gray-800/50">
                            <div className="flex justify-between items-center">
                                <span className="text-2xs font-bold text-gray-500 uppercase tracking-wider">vs Prior Week</span>
                                {escalation?.is_escalating ? (
                                    <span className="text-xs font-bold font-mono text-red-400">+{escalation.percent_change?.toFixed(0)}%</span>
                                ) : (
                                    <span className="text-xs font-bold font-mono text-green-400">Steady</span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Activity Stats */}
                    <div className="card flex flex-col justify-between">
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Clock className="w-4 h-4 text-gray-400" />
                                <h3 className="text-xs font-black uppercase tracking-widest text-gray-400">Activity Stats</h3>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <div className="text-2xl font-black text-white">{trajectory.summary.total_events}</div>
                                    <div className="text-2xs text-gray-500 uppercase font-bold tracking-wider mt-0.5">Total Events</div>
                                </div>
                                <div>
                                    <div className="text-2xl font-black text-red-400">{trajectory.summary.high_risk_count}</div>
                                    <div className="text-2xs text-gray-500 uppercase font-bold tracking-wider mt-0.5">High Risk</div>
                                </div>
                            </div>
                        </div>
                        <div className="mt-4 pt-3 border-t border-gray-800/50">
                            <div className="flex justify-between items-center">
                                <span className="text-2xs font-bold text-gray-500 uppercase tracking-wider">Threat Chains</span>
                                <span className={`text-xs font-bold font-mono ${chainsSummary.total_chains > 0 ? 'text-orange-400' : 'text-gray-400'}`}>
                                    {chainsSummary.total_chains || 0}
                                </span>
                            </div>
                        </div>
                    </div>

                </div>
            </div>

            {/* ── Chart & Behavioral DNA ────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">

                {/* Risk Progression Chart */}
                <div className="lg:col-span-2 card bg-gray-950/40">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
                        <h3 className="text-base font-bold text-white">Risk Trajectory</h3>
                        <div className="flex items-center gap-2 shrink-0">
                            {refreshing && <div className="animate-spin h-4 w-4 border-2 border-vortex-accent border-t-transparent rounded-full" />}
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

                    {/* Legend */}
                    <div className="flex items-center gap-5 mb-4">
                        <div className="flex items-center gap-1.5" title="Daily risk score mapped to 0–100%">
                            <div className="w-5 h-2.5 rounded-sm" style={{ background: 'linear-gradient(to bottom, rgba(239,68,68,0.55), rgba(239,68,68,0.05))' }} />
                            <span className="text-2xs text-gray-500 font-medium">Daily Risk %</span>
                        </div>
                        <div className="flex items-center gap-1.5" title="Cumulative threat load over time">
                            <div className="w-5 h-0" style={{ borderTop: '2px solid #8b5cf6' }} />
                            <span className="text-2xs text-gray-500 font-medium">Cumulative Load</span>
                        </div>
                        <div className="flex items-center gap-1.5" title="Org-wide median — identical across all users">
                            <div className="w-5 h-0" style={{ borderTop: '2px dashed #f59e0b' }} />
                            <span className="text-2xs text-gray-500 font-medium">Org Baseline</span>
                        </div>
                    </div>

                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData} margin={{ top: 10, right: 40, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorRiskPct" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0.03} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                                <XAxis dataKey="date" stroke="#4b5563" fontSize={10}
                                    tickFormatter={(val) => val.split('-').slice(1).join('/')}
                                    tickLine={false} axisLine={false} />
                                <YAxis yAxisId="left" stroke="#ef4444" fontSize={10} tickLine={false} axisLine={false}
                                    domain={[0, 100]} tickFormatter={(v) => `${v}%`} ticks={[0, 25, 50, 75, 100]} width={36} />
                                <YAxis yAxisId="right" orientation="right" stroke="#8b5cf6" fontSize={10}
                                    tickLine={false} axisLine={false} domain={[0, 100]}
                                    tickFormatter={(v) => `${v}%`} ticks={[0, 50, 100]} width={36} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '12px', fontSize: '12px' }}
                                    formatter={(value, name, props) => {
                                        if (name === 'riskPct') {
                                            const above = props.payload?.aboveBaseline;
                                            return [`${value}%  ${above ? '⚠ Above org baseline' : '✓ Within norm'}`, 'Daily Risk'];
                                        }
                                        if (name === 'cumulativePct') return [`${value}%`, 'Cumulative Load'];
                                        return [value, name];
                                    }}
                                    labelFormatter={(label) => `📅 ${label}`}
                                />
                                <ReferenceLine
                                    yAxisId="left"
                                    y={chartData[0]?.baselinePct ?? 30}
                                    stroke="#f59e0b" strokeDasharray="6 3" strokeWidth={1.5}
                                    label={{ value: `Org median ${chartData[0]?.baselinePct ?? 30}%`, position: 'insideTopRight', fill: '#f59e0b', fontSize: 10, fontWeight: 'bold' }}
                                />
                                <Area yAxisId="left" type="monotone" dataKey="riskPct"
                                    stroke="#ef4444" strokeWidth={2} fillOpacity={1} fill="url(#colorRiskPct)"
                                    name="riskPct" animationDuration={1000}
                                    dot={(dotProps) => {
                                        const { cx, cy, payload } = dotProps;
                                        if (!payload || cx == null || cy == null) return null;
                                        const r = payload.high > 0 ? 5 : 3;
                                        return (
                                            <circle key={`dot-${payload.date}`} cx={cx} cy={cy} r={r}
                                                fill={payload.aboveBaseline ? '#ef4444' : '#6b7280'}
                                                stroke={payload.aboveBaseline ? '#fca5a5' : '#374151'}
                                                strokeWidth={1} style={{ cursor: 'pointer' }}
                                                onClick={() => navigate(`/alerts?user=${encodeURIComponent(userId)}&date=${payload.date}`)}
                                            />
                                        );
                                    }}
                                    activeDot={(dotProps) => {
                                        const { cx, cy, payload } = dotProps;
                                        return (
                                            <circle key={`adot-${payload?.date}`} cx={cx} cy={cy} r={7}
                                                fill="#ef4444" stroke="#fca5a5" strokeWidth={2}
                                                style={{ cursor: 'pointer' }}
                                                onClick={() => navigate(`/alerts?user=${encodeURIComponent(userId)}&date=${payload.date}`)}
                                            />
                                        );
                                    }}
                                />
                                <Line yAxisId="right" type="monotone" dataKey="cumulativePct"
                                    stroke="#8b5cf6" strokeWidth={2} dot={false} name="cumulativePct" animationDuration={1000} />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Behavioral DNA */}
                <div className="lg:col-span-1 card">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-base font-bold text-white">Behavioral DNA</h3>
                        <BarChart2 className="w-4 h-4 text-gray-600" />
                    </div>
                    <div>
                        <BehaviorMetricPanel icon={Moon} label="Off-Hours Activity"
                            userVal={metrics?.off_hours?.user ?? baseline?.behavioral_fingerprint?.off_hours_rate ?? 0}
                            orgVal={metrics?.off_hours?.org ?? 0.08} color="purple" />
                        <BehaviorMetricPanel icon={Lock} label="Sensitive File Access"
                            userVal={metrics?.sensitive_file?.user ?? baseline?.behavioral_fingerprint?.sensitive_file_rate ?? 0}
                            orgVal={metrics?.sensitive_file?.org ?? 0.04} color="red" />
                        <BehaviorMetricPanel icon={Wifi} label="External Connections"
                            userVal={metrics?.external_ip?.user ?? baseline?.behavioral_fingerprint?.external_ip_rate ?? 0}
                            orgVal={metrics?.external_ip?.org ?? 0.05} color="orange" />
                        <BehaviorMetricPanel icon={Usb} label="USB Device Usage"
                            userVal={metrics?.usb?.user ?? baseline?.behavioral_fingerprint?.usb_rate ?? 0}
                            orgVal={metrics?.usb?.org ?? 0.03} color="yellow" />
                    </div>
                </div>
            </div>

            {/* ── Threat Chains ─────────────────────────────────────────── */}
            {(chainsSummary.total_chains > 0 || chains.length > 0) && (
                <div className="mb-6" id="chains-section">
                    <div className="flex items-center gap-3 mb-5">
                        <Shield className="w-4 h-4 text-orange-400" />
                        <h3 className="text-sm font-bold text-white">Detected Threat Chains</h3>
                        <span className="px-2 py-0.5 bg-orange-500/20 text-orange-400 text-2xs font-black rounded border border-orange-500/30 uppercase tracking-wider">
                            Critical Signal
                        </span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {Array.isArray(chains) && chains.slice(0, 4).map((chain, idx) => (
                            <ChainTimeline key={chain.chain_id || idx} chain={chain} />
                        ))}
                    </div>
                </div>
            )}

            {/* ── Activity Feed ─────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Activity Table */}
                <div className="lg:col-span-3 card p-0 overflow-hidden">
                    <div className="px-5 py-4 border-b border-gray-800/50 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Activity className="w-4 h-4 text-vortex-accent" />
                            <h3 className="text-sm font-bold text-white">Anomalous Activity Feed</h3>
                        </div>
                        <span className="text-2xs font-bold text-gray-500 uppercase tracking-wider">{recentEvents.length} events</span>
                    </div>
                    <div className="max-h-[420px] overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left">
                            <thead className="bg-gray-950/60 sticky top-0 z-10 backdrop-blur-md">
                                <tr>
                                    <th className="py-3 px-5 text-2xs font-black uppercase text-gray-500 tracking-widest">Event / Level</th>
                                    <th className="py-3 px-5 text-2xs font-black uppercase text-gray-500 tracking-widest">Timestamp</th>
                                    <th className="py-3 px-5 text-2xs font-black uppercase text-gray-500 tracking-widest">Explanation</th>
                                    <th className="py-3 px-5 text-2xs font-black uppercase text-gray-500 tracking-widest text-right">Score</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-800/50">
                                {recentEvents.map((event) => {
                                    const lvl = (event.risk_level || '').toLowerCase();
                                    const isCritical = event.anomaly_score > 0.7 || lvl === 'critical';
                                    const isHigh = !isCritical && (event.anomaly_score > 0.4 || lvl === 'high');
                                    const isMedium = !isCritical && !isHigh && (event.anomaly_score > 0.2 || lvl === 'medium');

                                    const rowAccent = isCritical ? 'border-l-2 border-l-red-500'
                                        : isHigh ? 'border-l-2 border-l-orange-500'
                                            : isMedium ? 'border-l-2 border-l-yellow-500'
                                                : 'border-l-2 border-l-gray-700/50';

                                    const iconColor = isCritical ? 'text-red-400' : isHigh ? 'text-orange-400' : isMedium ? 'text-yellow-400' : 'text-green-400';

                                    const iconBg = isCritical ? 'bg-red-500/10 border-red-500/30 group-hover:border-red-400'
                                        : isHigh ? 'bg-orange-500/10 border-orange-500/30 group-hover:border-orange-400'
                                            : isMedium ? 'bg-yellow-500/10 border-yellow-500/30 group-hover:border-yellow-400'
                                                : 'bg-gray-900 border-gray-700 group-hover:border-vortex-accent/40';

                                    const badgeStyle = isCritical ? 'bg-red-500/20 text-red-400 border-red-500/40'
                                        : isHigh ? 'bg-orange-500/20 text-orange-400 border-orange-500/40'
                                            : isMedium ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40'
                                                : 'bg-green-500/20 text-green-400 border-green-500/40';

                                    const badgeLabel = isCritical ? 'Critical' : isHigh ? 'High' : isMedium ? 'Medium' : 'Low';

                                    const isFP = event.explanation?.includes('False Positive');
                                    const fallback = isCritical ? 'Isolation Forest flagged severe multi-feature deviation from user norm'
                                        : isHigh ? 'Behavioural signature significantly outside established baseline'
                                            : isMedium ? 'Mild anomaly — pattern partially diverges from baseline'
                                                : 'Minor deviation within acceptable statistical tolerance';
                                    const explanation = event.explanation || fallback;

                                    const explColor = isFP ? 'text-green-400 font-medium'
                                        : isCritical ? 'text-red-300'
                                            : isHigh ? 'text-orange-300'
                                                : isMedium ? 'text-yellow-300'
                                                    : 'text-gray-500';

                                    return (
                                        <tr key={event.event_id}
                                            className={`group hover:bg-gray-800/40 transition-all cursor-pointer ${rowAccent}`}
                                            onClick={() => navigate(`/event/${event.event_id}`)}>
                                            <td className="py-3.5 px-5">
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-8 h-8 rounded flex items-center justify-center p-1.5 border transition-colors ${iconBg}`}>
                                                        {(isCritical || isHigh)
                                                            ? <AlertTriangle size={14} className={iconColor} />
                                                            : <HardDrive size={14} className={iconColor} />}
                                                    </div>
                                                    <div>
                                                        <div className="text-xs font-bold text-gray-200 group-hover:text-vortex-accent transition-colors">
                                                            Event {event.event_id.split('_').pop()}
                                                        </div>
                                                        <span className={`inline-block mt-0.5 px-1.5 py-px rounded text-2xs font-black border ${badgeStyle}`}>
                                                            {badgeLabel}
                                                        </span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-3.5 px-5">
                                                <div className="flex items-center gap-1.5 text-xs text-gray-400">
                                                    <Clock size={11} className="text-gray-600 shrink-0" />
                                                    {new Date(event.timestamp).toLocaleString('en-GB')}
                                                </div>
                                            </td>
                                            <td className="py-3.5 px-5 max-w-[220px]">
                                                <p className={`text-xs leading-snug ${explColor}`}>{explanation}</p>
                                            </td>
                                            <td className="py-3.5 px-5 text-right">
                                                <span className={`font-mono font-bold text-sm ${iconColor}`}>
                                                    {(event.anomaly_score || 0).toFixed(3)}
                                                </span>
                                            </td>
                                        </tr>
                                    );
                                })}
                                {recentEvents.length === 0 && (
                                    <tr>
                                        <td colSpan="4" className="py-16 text-center text-gray-600 text-xs italic">
                                            No anomalous events detected for this identity.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default UserProfile;
