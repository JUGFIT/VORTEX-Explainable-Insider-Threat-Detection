import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const StatsCard = ({ title, value, change, changeType, icon: Icon, color = 'vortex-accent' }) => {
    const getTrendIcon = () => {
        if (changeType === 'increase') return <TrendingUp size={16} className="text-risk-critical" />;
        if (changeType === 'decrease') return <TrendingDown size={16} className="text-risk-low" />;
        return <Minus size={16} className="text-gray-400" />;
    };

    return (
        <div className="card card-glass p-5 hover:shadow-2xl transition-all duration-300 animate-fade-in group hover:-translate-y-1">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-[11px] text-gray-500 uppercase font-black tracking-widest mb-1">{title}</p>
                    <h3 className="text-2xl font-black text-white leading-tight">{value}</h3>
                    {change && (
                        <div className="flex items-center space-x-1 mt-1.5">
                            {getTrendIcon()}
                            <span className={`text-xs font-bold ${changeType === 'increase' ? 'text-risk-critical' :
                                changeType === 'decrease' ? 'text-risk-low' :
                                    'text-gray-400'
                                }`}>
                                {change}
                            </span>
                            <span className="text-[10px] text-gray-500 font-medium">vs last week</span>
                        </div>
                    )}
                </div>
                <div className="flex items-center justify-center p-1.5 bg-white/5 rounded-xl group-hover:bg-vortex-accent/10 transition-colors">
                    <Icon
                        size={24}
                        className={`text-${color} opacity-90`}
                    />
                </div>
            </div>
        </div>
    );
};

export default StatsCard;
