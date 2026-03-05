import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

const StatsCard = ({ title, value, change, changeType, icon: Icon, color = 'vortex-accent' }) => {
    const getTrendIcon = () => {
        if (changeType === 'increase') return <TrendingUp size={16} className="text-risk-critical" />;
        if (changeType === 'decrease') return <TrendingDown size={16} className="text-risk-low" />;
        return <Minus size={16} className="text-gray-400" />;
    };

    return (
        <div className="card hover:shadow-xl transition-shadow duration-200 animate-fade-in">
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <p className="text-sm text-gray-400 mb-2">{title}</p>
                    <h3 className="text-3xl font-bold text-white mb-2">{value}</h3>
                    {change && (
                        <div className="flex items-center space-x-1">
                            {getTrendIcon()}
                            <span className={`text-sm ${changeType === 'increase' ? 'text-risk-critical' :
                                    changeType === 'decrease' ? 'text-risk-low' :
                                        'text-gray-400'
                                }`}>
                                {change}
                            </span>
                            <span className="text-xs text-gray-500">vs last week</span>
                        </div>
                    )}
                </div>
                <div className={`p-3 rounded-lg bg-${color} bg-opacity-20`}>
                    <Icon size={24} className={`text-${color}`} />
                </div>
            </div>
        </div>
    );
};

export default StatsCard;
