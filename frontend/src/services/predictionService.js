
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 120000,
});

// Kiểm tra trạng thái Backend
export const checkBackendHealth = async () => {
  const response = await api.get("/api/health");
  return response.data;
};

// Lấy danh sách mô hình AI
export const getModels = async () => {
  const response = await api.get("/api/models");
  return response.data;
};

// Nhận diện một ảnh
export const predictSingle = async (file, model) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("model", model);

  const response = await api.post("/api/predict", formData);
  return response.data;
};

// Nhận diện nhiều ảnh cùng lúc
export const predictBatch = async (files, model) => {
  const formData = new FormData();

  files.forEach((file) => {
    formData.append("files", file);
  });

  formData.append("model", model);

  const response = await api.post("/api/predict/batch", formData);
  return response.data;
};

export default api;
