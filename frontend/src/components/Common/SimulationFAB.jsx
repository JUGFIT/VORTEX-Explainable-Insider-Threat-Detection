import { useState } from 'react';
import { Zap } from 'lucide-react';

const SimulationFAB = ({ onClick }) => {
    const [isHovered, setIsHovered] = useState(false);

    return (
        <button
            onClick={onClick}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className="fixed bottom-8 right-8 z-50 group"
            aria-label="Open Event Log Generator"
        >
            {/* Main Button */}
            <div className="relative">
                <div className="w-16 h-16 bg-gradient-to-br from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 rounded-full shadow-lg hover:shadow-2xl transition-all flex items-center justify-center transform hover:scale-110 active:scale-95">
                    <Zap className="w-8 h-8 text-white" />
                </div>

                {/* Pulsing Ring */}
                <div className="absolute inset-0 w-16 h-16 bg-purple-500 rounded-full animate-ping opacity-20"></div>
            </div>

            {/* Tooltip */}
            {isHovered && (
                <div className="absolute bottom-full right-0 mb-3 whitespace-nowrap">
                    <div className="bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg border border-purple-500/50 animate-fade-in">
                        <div className="font-semibold">Event Log Generator</div>
                        <div className="text-xs text-gray-400">Demo Mode</div>
                    </div>
                    {/* Arrow */}
                    <div className="absolute top-full right-6 w-3 h-3 bg-gray-900 border-r border-b border-purple-500/50 transform rotate-45 -mt-1.5"></div>
                </div>
            )}
        </button>
    );
};

export default SimulationFAB;
