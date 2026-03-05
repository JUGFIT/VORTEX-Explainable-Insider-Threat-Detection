import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout/Layout';
import LoadingSpinner from '../components/Common/LoadingSpinner';
import { Shield, Activity, Clock, AlertTriangle, Layers, Filter } from 'lucide-react';
import { getChainPatterns, getTrajectoryStatistics } from '../services/api';
import ChainTimeline from '../components/UserProfile/ChainTimeline';
import RiskBadge from '../components/Common/RiskBadge';

const Chains = () => {
    const [loading, setLoading] = useState(true);
    const [chains, setChains] = useState([]);
    const [stats, setStats] = useState(null);
    const [filter, setFilter] = useState('Critical');

    useEffect(() => {
        fetchData();
    }, [filter]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [chainsData, statsData] = await Promise.all([
                getChainPatterns({ min_severity: filter, limit: 20 }),
                getTrajectoryStatistics()
            ]);

            setChains(Array.isArray(chainsData) ? chainsData : []);
            setStats(statsData);
        } catch (error) {
            console.error('Error fetching chain data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading && !stats) {
        return (
            <Layout title="Attack Chains" subtitle="Correlating multi-stage behavior patterns">
                <LoadingSpinner size={48} className="h-96" />
            </Layout>
        );
    }

    return (
        <Layout title="Attack Chain Analysis" subtitle="Correlated behavioral sequences across the organizational fabric">
            {/* Global Stats Bar */}
            {stats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                    <div className="card bg-gray-900/50 border-gray-800">
                        <div className="text-[10px] font-black text-gray-500 uppercase mb-1">Total Chains</div>
                        <div className="text-2xl font-bold">{stats.total_chains}</div>
                    </div>
                    <div className="card bg-red-900/10 border-red-500/20">
                        <div className="text-[10px] font-black text-red-400 uppercase mb-1">Critical Signals</div>
                        <div className="text-2xl font-bold text-red-500">{stats.critical_chains}</div>
                    </div>
                    <div className="card bg-purple-900/10 border-purple-500/20">
                        <div className="text-[10px] font-black text-purple-400 uppercase mb-1">Avg Chain Depth</div>
                        <div className="text-2xl font-bold text-purple-400">{(stats.average_chain_length || 0).toFixed(1)}</div>
                    </div>
                    <div className="card bg-gray-900/50 border-gray-800">
                        <div className="text-[10px] font-black text-gray-500 uppercase mb-1">Unique Users In Chains</div>
                        <div className="text-2xl font-bold text-white">{stats.unique_users_with_chains}</div>
                    </div>
                </div>
            )}

            {/* Filter Bar */}
            <div className="card mb-8 border-dashed border-gray-700 bg-transparent flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Filter className="w-5 h-5 text-gray-500" />
                    <span className="text-sm font-bold uppercase tracking-widest text-gray-400">Filter Severity:</span>
                    <div className="flex gap-2">
                        {['All', 'Critical', 'High', 'Medium'].map(s => (
                            <button
                                key={s}
                                onClick={() => setFilter(s === 'All' ? null : s)}
                                className={`px-4 py-1.5 rounded-full text-xs font-black uppercase transition-all ${(filter === s || (s === 'All' && filter === null))
                                        ? 'bg-vortex-accent text-white shadow-[0_0_15px_rgba(124,58,237,0.4)]'
                                        : 'bg-gray-800 text-gray-500 hover:text-gray-300'
                                    }`}
                            >
                                {s}
                            </button>
                        ))}
                    </div>
                </div>
                <div className="text-[10px] font-black text-gray-600 uppercase">
                    Real-time Correlation Engine: Active
                </div>
            </div>

            {/* Chains Grid */}
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                {chains.map((chain, idx) => (
                    <div key={chain.chain_id || idx} className="relative group">
                        {/* Target User Badge */}
                        <div className="absolute -top-3 left-6 z-10 px-3 py-1 bg-gray-900 border border-vortex-accent/50 rounded-full text-[10px] font-black text-vortex-accent shadow-xl group-hover:scale-110 transition-transform">
                            TARGET: {chain.user_id}
                        </div>
                        <ChainTimeline chain={chain} />
                    </div>
                ))}

                {chains.length === 0 && !loading && (
                    <div className="col-span-full card py-20 text-center border-dashed border-gray-700 bg-transparent">
                        <Layers className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                        <h3 className="text-xl font-bold text-gray-400 uppercase">No correlating chains found</h3>
                        <p className="text-sm text-gray-500 mt-2 max-w-md mx-auto">
                            Adjust your severity filter or wait for the detection engine to correlate more behavioral events.
                        </p>
                    </div>
                )}
            </div>

            {loading && chains.length > 0 && (
                <div className="mt-8 flex justify-center">
                    <LoadingSpinner size={24} />
                    <span className="text-xs text-gray-500 ml-3 animate-pulse uppercase font-bold">Refreshing signals...</span>
                </div>
            )}
        </Layout>
    );
};

export default Chains;
