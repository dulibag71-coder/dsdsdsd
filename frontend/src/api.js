import axios from 'axios';

// 로컬 환경에서 테스트 시 자신의 컴퓨터 로컬 IP 주소로 변경하세요.
// 예: "http://192.168.0.x:8000" (안드로이드/iOS 에뮬레이터 또는 실기기용)
const API_BASE_URL = 'http://127.0.0.1:8000';

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
