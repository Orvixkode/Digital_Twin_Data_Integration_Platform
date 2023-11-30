import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens (if needed)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
      throw new Error(error.response.data.message || 'API request failed');
    } else if (error.request) {
      // Network error
      console.error('Network Error:', error.message);
      throw new Error('Network connection failed');
    } else {
      // Other error
      console.error('Error:', error.message);
      throw error;
    }
  }
);

export const apiService = {
  // Dashboard endpoints
  getDashboardOverview: () => apiClient.get('/monitoring/dashboard'),
  getRealtimeData: (params = {}) => apiClient.get('/monitoring/realtime-data', { params }),
  getPerformanceMetrics: (params = {}) => apiClient.get('/monitoring/performance-metrics', { params }),
  getActiveAlerts: (params = {}) => apiClient.get('/monitoring/alerts', { params }),
  acknowledgeAlert: (alertId, acknowledgedBy) => 
    apiClient.post(`/monitoring/alerts/${alertId}/acknowledge`, { acknowledged_by: acknowledgedBy }),

  // Equipment endpoints
  getEquipment: (params = {}) => apiClient.get('/equipment', { params }),
  createEquipment: (equipment) => apiClient.post('/equipment', equipment),
  getEquipmentById: (equipmentId) => apiClient.get(`/equipment/${equipmentId}`),
  updateEquipment: (equipmentId, updates) => apiClient.put(`/equipment/${equipmentId}`, updates),
  deleteEquipment: (equipmentId) => apiClient.delete(`/equipment/${equipmentId}`),
  getEquipmentStatus: (equipmentId) => apiClient.get(`/equipment/${equipmentId}/status`),
  connectEquipment: (equipmentId) => apiClient.post(`/equipment/${equipmentId}/connect`),
  getEquipmentHealth: () => apiClient.get('/monitoring/equipment-health'),

  // Sensor endpoints
  getSensors: (params = {}) => apiClient.get('/sensors', { params }),
  createSensor: (sensor) => apiClient.post('/sensors', sensor),
  getSensorById: (sensorId) => apiClient.get(`/sensors/${sensorId}`),

  // Data processing endpoints
  queryData: (query) => apiClient.post('/data/query', query),
  exportData: (request) => apiClient.post('/data/export', request),
  getDataStatistics: (params = {}) => apiClient.get('/data/statistics', { params }),
  detectAnomalies: (request) => apiClient.post('/data/anomaly-detection', request),
  getProcessingJob: (jobId) => apiClient.get(`/data/jobs/${jobId}`),

  // Integration endpoints
  getSupportedProtocols: () => apiClient.get('/integration/protocols'),
  testConnection: (request) => apiClient.post('/integration/test-connection', request),
  getConnectionStatus: () => apiClient.get('/integration/connection-status'),
  browseOpcuaNodes: (params = {}) => apiClient.get('/integration/opc-ua/browse', { params }),
  publishMqttCommand: (equipmentId, command, payload) => 
    apiClient.post(`/integration/mqtt/publish?equipment_id=${equipmentId}&command=${command}`, payload),
  getMiddlewareStats: () => apiClient.get('/integration/middleware/stats'),
};

export default apiService;