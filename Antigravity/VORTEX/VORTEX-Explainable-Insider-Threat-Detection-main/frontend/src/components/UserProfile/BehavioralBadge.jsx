import { Moon, FileText, Usb, Mail, Lock, Clock, HardDrive, Download } from 'lucide-react';

const BehavioralBadge = ({ type, value, threshold, label }) => {
    // Determine if badge should be shown based on threshold
    const isActive = value > threshold;

    // Badge configurations
    const badgeConfig = {
        'off-hours': {
            icon: Moon,
            label: 'Off-Hours Worker',
            color: 'purple',
            description: `${(value * 100).toFixed(0)}% activity after hours`,
        },
        'high-file-access': {
            icon: FileText,
            label: 'High File Access',
            color: 'blue',
            description: `${Math.round(value)} files/day avg`,
        },
        'usb-user': {
            icon: Usb,
            label: 'USB User',
            color: 'yellow',
            description: `${Math.round(value)} USB events`,
        },
        'email-heavy': {
            icon: Mail,
            label: 'Email Heavy',
            color: 'green',
            description: `${Math.round(value)} emails/day`,
        },
        'sensitive-access': {
            icon: Lock,
            label: 'Sensitive File Access',
            color: 'red',
            description: `${Math.round(value)} sensitive files`,
        },
        'long-sessions': {
            icon: Clock,
            label: 'Long Sessions',
            color: 'indigo',
            description: `${value.toFixed(1)}h avg session`,
        },
        'large-uploads': {
            icon: HardDrive,
            label: 'Large Uploads',
            color: 'orange',
            description: `${value.toFixed(1)}MB avg upload`,
        },
        'frequent-downloads': {
            icon: Download,
            label: 'Frequent Downloads',
            color: 'cyan',
            description: `${Math.round(value)} downloads/day`,
        },
    };

    const config = badgeConfig[type] || badgeConfig['high-file-access'];
    const Icon = config.icon;

    if (!isActive) return null;

    const colorClasses = {
        purple: 'bg-purple-500/20 text-purple-300 border-purple-500/50',
        blue: 'bg-blue-500/20 text-blue-300 border-blue-500/50',
        yellow: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
        green: 'bg-green-500/20 text-green-300 border-green-500/50',
        red: 'bg-red-500/20 text-red-300 border-red-500/50',
        indigo: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/50',
        orange: 'bg-orange-500/20 text-orange-300 border-orange-500/50',
        cyan: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/50',
    };

    return (
        <div
            className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${colorClasses[config.color]
                } transition-all hover:scale-105`}
            title={config.description}
        >
            <Icon className="w-4 h-4" />
            <div className="flex flex-col">
                <span className="text-xs font-semibold">{label || config.label}</span>
                <span className="text-xs opacity-75">{config.description}</span>
            </div>
        </div>
    );
};

export default BehavioralBadge;
