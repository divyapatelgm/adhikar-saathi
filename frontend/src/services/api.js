import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

export const getStats = async () => {
  const res = await api.get('/stats');
  return res.data;
};

export const getSchemes = async (params = {}) => {
  const res = await api.get('/schemes', { params });
  return res.data;
};

export const evaluateEligibility = async (profile, language = 'kn', categoryFilter = null) => {
  const res = await api.post('/eligibility', {
    profile,
    language,
    category_filter: categoryFilter,
  });
  return res.data;
};

export const sendChat = async (message, language = 'kn', profile = null) => {
  const res = await api.post('/chat', {
    message,
    language,
    profile,
  });
  return res.data;
};

export const scanNotice = async (formData) => {
  const res = await api.post('/notice/scan', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
};

export default api;
