const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

// Get token from localStorage
const getToken = () => localStorage.getItem('token');

// API request helper
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = getToken();
  
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'API request failed');
  }

  return data;
}

// Auth API
export const authAPI = {
  register: async (email: string, password: string, fullName: string, username: string, profession: string) => {
    const data = await apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, fullName, username, profession }),
    });
    localStorage.setItem('token', data.token);
    return data.user;
  },

  login: async (email: string, password: string) => {
    const data = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('token', data.token);
    return data.user;
  },

  logout: () => {
    localStorage.removeItem('token');
  },

  getCurrentUser: async () => {
    const data = await apiRequest('/auth/me');
    return data.user;
  },

  deleteAccount: async () => {
    await apiRequest('/auth/delete', {
      method: 'DELETE',
    });
  },
};

// Favorites API
export const favoritesAPI = {
  getAll: async () => {
    const data = await apiRequest('/favorites');
    return data.favorites;
  },

  add: async (symbol: string, stockName: string) => {
    const data = await apiRequest('/favorites', {
      method: 'POST',
      body: JSON.stringify({ symbol, stockName }),
    });
    return data.favorite;
  },

  remove: async (symbol: string) => {
    await apiRequest(`/favorites/${symbol}`, {
      method: 'DELETE',
    });
  },

  check: async (symbol: string) => {
    const data = await apiRequest(`/favorites/check/${symbol}`);
    return data.isFavorite;
  },
};

// Comments API
export const commentsAPI = {
  getBySymbol: async (symbol: string) => {
    const data = await apiRequest(`/comments/${symbol}`);
    return data.comments;
  },

  add: async (symbol: string, content: string) => {
    const data = await apiRequest('/comments', {
      method: 'POST',
      body: JSON.stringify({ symbol, content }),
    });
    return data.comment;
  },

  update: async (id: string, content: string) => {
    const data = await apiRequest(`/comments/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
    return data.comment;
  },

  delete: async (id: string) => {
    await apiRequest(`/comments/${id}`, {
      method: 'DELETE',
    });
  },
};
