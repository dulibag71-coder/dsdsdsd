import axios from 'axios';

// 로컬 환경에서 테스트 시 .env 파일에 EXPO_PUBLIC_API_URL=http://나의아이피:8000 을 설정하세요.
// 클라우드 출시 후에는 Render.com에서 받은 주소(예: https://golf-ai-backend.onrender.com)를 넣으시면 됩니다.
const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const getOrCreateUser = async (email) => {
  const response = await api.post('/users', { email });
  return response.data;
};

export const uploadVideo = async (userId, uri, filename, type) => {
  const formData = new FormData();
  formData.append('file', { uri, name: filename, type });
  
  const response = await api.post(`/upload?user_id=${userId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const getPose = async (swingId) => {
  const response = await api.get(`/pose/${swingId}`);
  return response.data;
};

export const analyzeSwing = async (swingId) => {
  const response = await api.post(`/analyze?swing_id=${swingId}`);
  return response.data;
};

export const getLesson = async (swingId) => {
  const response = await api.post(`/lesson?swing_id=${swingId}`);
  return response.data;
};

export default api;
