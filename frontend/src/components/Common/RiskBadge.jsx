import React from 'react';

const getRiskBadgeClass = (riskLevel) => {
    const level = riskLevel?.toLowerCase();
    if (level === 'critical') return 'badge-critical';
    if (level === 'high') return 'badge-high';
    if (level === 'medium') return 'badge-medium';
    if (level === 'low') return 'badge-low';
    return 'bg-gray-600 text-white';
};

const RiskBadge = ({ level, className = '' }) => {
    return (
        <span className={`badge ${getRiskBadgeClass(level)} ${className}`}>
            {level?.toUpperCase() || 'UNKNOWN'}
        </span>
    );
};

export default RiskBadge;
