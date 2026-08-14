import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "/api";

export const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

const TOKEN_KEY = "lexora_access_token";

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

api.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Centralized 401 handling: any authenticated request that comes back
// unauthorized (expired/invalid token) clears the stale token so the UI
// can fall back to the signed-out state instead of looping on retries.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      setStoredToken(null);
    }
    return Promise.reject(error);
  }
);

export const authApi = {
  loginWithGoogle: (idToken) => api.post("/auth/google", { id_token: idToken }),
  getMe: () => api.get("/auth/me"),
  logout: () => api.post("/auth/logout"),
};

export const booksApi = {
  search: (q, searchType = "keyword", limit = 20) =>
    api.get("/books/search", { params: { q, search_type: searchType, limit } }),
  getById: (id) => api.get(`/books/${id}`),
  getSimilar: (id, limit = 10) => api.get(`/books/similar/${id}`, { params: { limit } }),
  getRecommendations: (limit = 20) => api.get("/books/recommendations", { params: { limit } }),
};

export const aiApi = {
  chat: (message) => api.post("/ai/chat", { message }),
  getChatHistory: () => api.get("/ai/chat/history"),
  getSummary: (bookId) => api.get(`/ai/summary/${bookId}`),
  getWhy: (bookId) => api.get(`/ai/why/${bookId}`),
};

export const scannerApi = {
  upload: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/scanner/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
