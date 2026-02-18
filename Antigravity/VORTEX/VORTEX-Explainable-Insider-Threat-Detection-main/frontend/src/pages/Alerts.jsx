import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout/Layout';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import RiskBadge from '../components/Common/RiskBadge';
import { Filter, Eye, RefreshCw, ArrowUpDown, ArrowUp, ArrowDown, ChevronLeft, ChevronRight, X } from 'lucide-react';
import { getRiskEvents, getRiskCounts } from '../services/api';
import { useNavigate, useSearchParams } from 'react-router-dom';

const SORT_OPTIONS = [
    { value: 'anomaly_score', label: 'Anomaly Score' },
    { value: 'timestamp', label: 'Timestamp' },
    { value: 'user_id', label: 'User ID' },
    { value: 'risk_level', label: 'Risk Level' },
];

const PAGE_SIZE_OPTIONS = [50, 100, 200];

const SortIcon = ({ field, currentSort, currentOrder }) => {
    if (currentSort !== field) return <ArrowUpDown size={13} className="text-gray-600 ml-1 inline" />;
    return currentOrder === 'desc'
        ? <ArrowDown size={13} className="text-vortex-accent ml-1 inline" />
        : <ArrowUp size={13} className="text-vortex-accent ml-1 inline" />;
};

const Alerts = () => {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();

    // Deep-link context from chart dots
    const urlUser = searchParams.get('user') || '';
    const urlDate = searchParams.get('date') || '';
    const urlSearch = searchParams.get('search') || '';

    const [loading, setLoading] = useState(true);
    const [events, setEvents] = useState([]);
    const [counts, setCounts] = useState(null);
    const [filters, setFilters] = useState({ riskLevel: 'all', search: urlSearch || urlUser });
    const [sortBy, setSortBy] = useState('anomaly_score');
    const [sortOrder, setSortOrder] = useState('desc');
    const [page, setPage] = useState(0);
    const [pageSize, setPageSize] = useState(100);
    const [filteredEvents, setFilteredEvents] = useState([]);

    // Fetch one page from the server
    const fetchEvents = useCallback(async ({
        sb = sortBy, so = sortOrder, pg = page, ps = pageSize,
        rl = filters.riskLevel, uid = urlUser, dt = urlDate
    } = {}) => {
        try {
            setLoading(true);
            const params = {
                sort_by: sb,
                sort_order: so,
                limit: ps,
                offset: pg * ps,
            };
            if (rl !== 'all') params.risk_level = rl.charAt(0).toUpperCase() + rl.slice(1);
            if (uid) params.user_id = uid;
            if (dt) params.date = dt;

            const [data, countData] = await Promise.all([
                getRiskEvents(params),
                getRiskCounts(),
            ]);
            setEvents(data);
            setCounts(countData);
        } catch (error) {
            console.error('Error fetching events:', error);
        } finally {
            setLoading(false);
        }
    }, [sortBy, sortOrder, page, pageSize, filters.riskLevel, urlUser, urlDate]);

    // Initial load — respects URL params for deep-linking from chart
    useEffect(() => { fetchEvents(); }, []);

    // Client-side search filter only (risk level & sort handled server-side)
    useEffect(() => {
        if (!filters.search) {
            setFilteredEvents(events);
            return;
        }
        const s = filters.search.toLowerCase();
        setFilteredEvents(events.filter(e =>
            e.event_id.toLowerCase().includes(s) || e.user_id.toLowerCase().includes(s)
        ));
    }, [events, filters.search]);

    // Helpers that also reset to page 0 when filters/sort change
    const handleSortHeader = (field) => {
        const newOrder = sortBy === field && sortOrder === 'desc' ? 'asc' : 'desc';
        setSortBy(field);
        setSortOrder(newOrder);
        setPage(0);
        fetchEvents({ sb: field, so: newOrder, pg: 0 });
    };

    const handleSortDropdown = (field) => {
        setSortBy(field);
        setPage(0);
        fetchEvents({ sb: field, pg: 0 });
    };

    const handleOrderToggle = () => {
        const newOrder = sortOrder === 'desc' ? 'asc' : 'desc';
        setSortOrder(newOrder);
        setPage(0);
        fetchEvents({ so: newOrder, pg: 0 });
    };

    const handleRiskFilter = (rl) => {
        setFilters(prev => ({ ...prev, riskLevel: rl }));
        setPage(0);
        fetchEvents({ rl, pg: 0 });
    };

    const handlePageSize = (ps) => {
        setPageSize(ps);
        setPage(0);
        fetchEvents({ ps: Number(ps), pg: 0 });
    };

    const handlePrev = () => {
        const newPage = Math.max(0, page - 1);
        setPage(newPage);
        fetchEvents({ pg: newPage });
    };

    const handleNext = () => {
        const newPage = page + 1;
        setPage(newPage);
        fetchEvents({ pg: newPage });
    };

    const ThSortable = ({ field, children }) => (
        <th
            className="text-left py-3 px-4 text-sm font-medium text-gray-400 cursor-pointer select-none hover:text-white transition-colors whitespace-nowrap"
            onClick={() => handleSortHeader(field)}
        >
            {children}
            <SortIcon field={field} currentSort={sortBy} currentOrder={sortOrder} />
        </th>
    );

    // Total count for the current filter (for pagination math)
    const totalFiltered = filters.riskLevel === 'all'
        ? (counts?.total_events ?? 0)
        : (counts?.by_risk_level?.[filters.riskLevel.charAt(0).toUpperCase() + filters.riskLevel.slice(1)] ?? 0);

    const totalPages = Math.max(1, Math.ceil(totalFiltered / pageSize));
    const startRow = page * pageSize + 1;
    const endRow = Math.min((page + 1) * pageSize, totalFiltered);

    if (loading && events.length === 0) {
        return (
            <Layout title="Security Alerts" subtitle="Monitor and investigate risk events">
                <LoadingSpinner size={48} className="h-96" />
            </Layout>
        );
    }

    const clearDeepLink = () => {
        setSearchParams({});
        window.location.reload();
    };

    return (
        <Layout title="Security Alerts" subtitle="Monitor and investigate risk events">

            {/* Deep-link context banner */}
            {(urlUser || urlDate) && (
                <div className="flex items-center justify-between gap-3 mb-4 px-4 py-3 rounded-xl bg-vortex-accent/10 border border-vortex-accent/30 text-sm">
                    <span className="text-gray-300">
                        📅 Showing events for
                        {urlUser && <span className="font-bold text-white mx-1">{urlUser}</span>}
                        {urlDate && <span className="text-gray-400">on <span className="font-mono text-white">{urlDate}</span></span>}
                    </span>
                    <button onClick={clearDeepLink} className="flex items-center gap-1 text-gray-500 hover:text-white transition-colors text-xs">
                        <X size={13} /> Clear filter
                    </button>
                </div>
            )}

            {/* Stats Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {[
                    { label: 'Total Events', value: counts?.total_events ?? 0, color: 'text-white' },
                    { label: 'High Risk', value: counts?.by_risk_level?.High ?? 0, color: 'text-red-400' },
                    { label: 'Medium Risk', value: counts?.by_risk_level?.Medium ?? 0, color: 'text-yellow-400' },
                    { label: 'Low Risk', value: counts?.by_risk_level?.Low ?? 0, color: 'text-green-400' },
                ].map(({ label, value, color }) => (
                    <div key={label} className="card py-3 px-4 flex flex-col">
                        <span className="text-xs text-gray-500 uppercase font-bold">{label}</span>
                        <span className={`text-2xl font-black mt-1 ${color}`}>{value.toLocaleString()}</span>
                    </div>
                ))}
            </div>

            {/* Filters */}
            <div className="card mb-6">
                <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex items-center space-x-3 flex-1 flex-wrap gap-3">
                        <Filter size={20} className="text-gray-400 shrink-0" />

                        {/* Risk Level Filter */}
                        <select
                            value={filters.riskLevel}
                            onChange={(e) => handleRiskFilter(e.target.value)}
                            className="input-field"
                        >
                            <option value="all">All Risk Levels</option>
                            <option value="high">High</option>
                            <option value="medium">Medium</option>
                            <option value="low">Low</option>
                        </select>

                        {/* Sort By */}
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 font-bold uppercase shrink-0">Sort by</span>
                            <select
                                value={sortBy}
                                onChange={(e) => handleSortDropdown(e.target.value)}
                                className="input-field"
                            >
                                {SORT_OPTIONS.map(o => (
                                    <option key={o.value} value={o.value}>{o.label}</option>
                                ))}
                            </select>
                            <button
                                onClick={handleOrderToggle}
                                className="btn-secondary p-2 flex items-center gap-1 text-xs"
                                title={sortOrder === 'desc' ? 'Descending' : 'Ascending'}
                            >
                                {sortOrder === 'desc' ? <ArrowDown size={14} /> : <ArrowUp size={14} />}
                                {sortOrder === 'desc' ? 'DESC' : 'ASC'}
                            </button>
                        </div>

                        {/* Page Size */}
                        <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500 font-bold uppercase shrink-0">Per page</span>
                            <select
                                value={pageSize}
                                onChange={(e) => handlePageSize(e.target.value)}
                                className="input-field"
                            >
                                {PAGE_SIZE_OPTIONS.map(n => (
                                    <option key={n} value={n}>{n}</option>
                                ))}
                            </select>
                        </div>

                        {/* Search (client-side within current page) */}
                        <input
                            type="text"
                            placeholder="Search by Event ID or User ID..."
                            value={filters.search}
                            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                            className="input-field flex-1 min-w-[180px] max-w-md"
                        />
                    </div>

                    <button
                        onClick={() => fetchEvents()}
                        className="btn-secondary flex items-center space-x-2"
                        disabled={loading}
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                        <span>Refresh</span>
                    </button>
                </div>

                {/* Pagination info + controls */}
                <div className="mt-4 flex items-center justify-between flex-wrap gap-3">
                    <span className="text-sm text-gray-400">
                        Showing <strong className="text-white">{startRow.toLocaleString()}–{endRow.toLocaleString()}</strong> of{' '}
                        <strong className="text-white">{totalFiltered.toLocaleString()}</strong> events
                        {' '}· Sorted by <strong className="text-vortex-accent">{SORT_OPTIONS.find(o => o.value === sortBy)?.label}</strong> ({sortOrder.toUpperCase()})
                    </span>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={handlePrev}
                            disabled={page === 0 || loading}
                            className="btn-secondary p-2 disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            <ChevronLeft size={16} />
                        </button>
                        <span className="text-sm text-gray-400 px-2">
                            Page <strong className="text-white">{page + 1}</strong> of <strong className="text-white">{totalPages.toLocaleString()}</strong>
                        </span>
                        <button
                            onClick={handleNext}
                            disabled={page >= totalPages - 1 || loading || events.length < pageSize}
                            className="btn-secondary p-2 disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                            <ChevronRight size={16} />
                        </button>
                    </div>
                </div>
            </div>

            {/* Events Table */}
            <div className="card">
                {loading && (
                    <div className="flex items-center justify-center py-6 gap-3 text-gray-500 text-sm">
                        <RefreshCw size={16} className="animate-spin" /> Loading events…
                    </div>
                )}
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-gray-800">
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Event ID</th>
                                <ThSortable field="user_id">User ID</ThSortable>
                                <ThSortable field="timestamp">Timestamp</ThSortable>
                                <ThSortable field="risk_level">Risk Level</ThSortable>
                                <ThSortable field="anomaly_score">Anomaly Score</ThSortable>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Ground Truth</th>
                                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredEvents.map((event) => (
                                <tr
                                    key={event.event_id}
                                    className="border-b border-gray-800 hover:bg-gray-800 transition-colors cursor-pointer"
                                    onClick={() => navigate(`/event/${event.event_id}`)}
                                >
                                    <td className="py-3 px-4 text-sm font-mono">
                                        <span className="truncate max-w-[160px] block" title={event.event_id}>
                                            {event.event_id}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-sm">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); navigate(`/user/${event.user_id}`); }}
                                            className="text-vortex-accent hover:text-vortex-accent-hover"
                                        >
                                            {event.user_id}
                                        </button>
                                    </td>
                                    <td className="py-3 px-4 text-sm text-gray-400 whitespace-nowrap">
                                        {new Date(event.timestamp).toLocaleString()}
                                    </td>
                                    <td className="py-3 px-4">
                                        <RiskBadge level={event.risk_level} />
                                    </td>
                                    <td className="py-3 px-4 text-sm font-semibold">
                                        <span className={
                                            event.anomaly_score > 0.8 ? 'text-risk-critical' :
                                                event.anomaly_score > 0.5 ? 'text-risk-high' :
                                                    event.anomaly_score > 0.3 ? 'text-risk-medium' :
                                                        'text-risk-low'
                                        }>
                                            {event.anomaly_score.toFixed(3)}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4">
                                        <span className={`text-xs px-2 py-1 rounded ${event.anomaly_flag_truth === 1
                                            ? 'bg-red-900 text-red-200'
                                            : 'bg-green-900 text-green-200'
                                            }`}>
                                            {event.anomaly_flag_truth === 1 ? 'Anomaly' : 'Normal'}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); navigate(`/event/${event.event_id}`); }}
                                            className="flex items-center space-x-1 text-vortex-accent hover:text-vortex-accent-hover"
                                        >
                                            <Eye size={16} />
                                            <span className="text-sm">Investigate</span>
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>

                    {!loading && filteredEvents.length === 0 && (
                        <div className="text-center py-12 text-gray-400">
                            No events found matching your filters
                        </div>
                    )}
                </div>

                {/* Bottom pagination */}
                {totalPages > 1 && (
                    <div className="flex items-center justify-between pt-4 border-t border-gray-800 mt-2 px-2">
                        <span className="text-sm text-gray-500">
                            {startRow.toLocaleString()}–{endRow.toLocaleString()} / {totalFiltered.toLocaleString()}
                        </span>
                        <div className="flex items-center gap-2">
                            <button onClick={handlePrev} disabled={page === 0 || loading}
                                className="btn-secondary p-2 disabled:opacity-30 disabled:cursor-not-allowed">
                                <ChevronLeft size={16} />
                            </button>
                            <span className="text-sm text-gray-400">
                                {page + 1} / {totalPages.toLocaleString()}
                            </span>
                            <button onClick={handleNext}
                                disabled={page >= totalPages - 1 || loading || events.length < pageSize}
                                className="btn-secondary p-2 disabled:opacity-30 disabled:cursor-not-allowed">
                                <ChevronRight size={16} />
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default Alerts;
