import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 60000, // Increased timeout to 60 seconds
    headers: {
        'Content-Type': 'application/json',
    },
});


// Health Check
// Risk Events
export const getRiskEvents = async (params = {}) => {
    const response = await api.get('/risks', { params });
    return response.data;
};

export const getRiskCounts = async (params = {}) => {
    try {
        const response = await api.get('/risks/count', { params });
        console.log('getRiskCounts response:', response.data);
        return response.data;
    } catch (error) {
        console.error('getRiskCounts failed:', error);
        throw error;
    }
};

export const getUserRisks = async (userId) => {
    const response = await api.get(`/risks/user/${userId}`);
    return response.data;
};

// Explanations
export const getExplanation = async (eventId) => {
    const response = await api.get(`/explain/${eventId}`);
    return response.data;
};

// User Baselines
export const getAllUsers = async () => {
    const response = await api.get('/users');
    return response.data;
};

export const getUserBaseline = async (userId) => {
    const response = await api.get(`/users/${userId}/baseline`);
    return response.data;
};

export const getEventDivergence = async (eventId) => {
    const response = await api.get(`/baselines/divergence/${eventId}`);
    return response.data;
};

// Risk Trajectories
export const getUserTrajectory = async (userId, lookbackDays = null) => {
    const params = lookbackDays ? { lookback_days: lookbackDays } : {};
    const response = await api.get(`/users/${userId}/trajectory`, { params });
    return response.data;
};

export const getUserEscalation = async (userId) => {
    const response = await api.get(`/users/${userId}/escalation`);
    return response.data;
};

export const getUserPatterns = async (userId) => {
    const response = await api.get(`/users/${userId}/patterns`);
    return response.data;
};

export const getTrajectoryStatistics = async () => {
    const response = await api.get('/analytics/chain-statistics');
    return response.data;
};

// Attack Chains
export const getUserChains = async (userId) => {
    const response = await api.get(`/users/${userId}/chains/summary`);
    return response.data;
};

export const getUserChainsList = async (userId) => {
    const response = await api.get(`/users/${userId}/chains`);
    return response.data;
};

export const getHighRiskChains = async (params = {}) => {
    const response = await api.get('/chains/high-risk', { params });
    return response.data;
};

// Analytics
export const getTrendingUsers = async (params = {}) => {
    const response = await api.get('/analytics/trending-users', { params });
    return response.data;
};

export const getChainPatterns = async (params = {}) => {
    const response = await api.get('/analytics/chains', { params });
    return response.data;
};

// Alias for backward compatibility
export const getAttackPatterns = getChainPatterns;

// Pipeline
export const runPipeline = async () => {
    const response = await api.post('/pipeline/run-all');
    return response.data;
};

export const getModelMetrics = async () => {
    const response = await api.get('/metrics');
    return response.data;
};

// Simulation
export const getSimulationOptions = async () => {
    const response = await api.get('/simulation/options');
    return response.data;
};

export const injectThreat = async (data) => {
    const response = await api.post('/simulation/inject', data);
    return response.data;
};

export const getSimulationStatus = async (userId = null) => {
    const params = userId ? { user_id: userId } : {};
    const response = await api.get('/simulation/status', { params });
    return response.data;
};

export const purgeSimulatedEvents = async () => {
    const response = await api.post('/simulation/purge');
    return response.data;
};

export default api;
