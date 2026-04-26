/**
 * Created by: Aden Borsa Team
 * Created At: 2025
 * Subject: Backend API istek yardımcıları - auth, favoriler ve yorumlar
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

/** localStorage'dan JWT token'ı okur */
const getToken = () => localStorage.getItem('token');

/**
 * Merkezi API istek fonksiyonu.
 * Token varsa Authorization header'ına ekler; hata durumunda exception fırlatır.
 */
async function apiRequest(endpoint: string, options: RequestInit = {}) {
  const token = getToken();

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, { ...options, headers });
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'API request failed');
  }

  return data;
}

/** Kimlik doğrulama işlemleri (kayıt, giriş, çıkış, profil) */
export const authAPI = {
  /** Yeni kullanıcı kaydı yapar ve token'ı localStorage'a yazar */
  register: async (email: string, password: string, fullName: string, username: string, profession: string) => {
    const data = await apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, fullName, username, profession }),
    });
    localStorage.setItem('token', data.token);
    return data.user;
  },

  /** Kullanıcı girişi yapar ve token'ı localStorage'a yazar */
  login: async (email: string, password: string) => {
    const data = await apiRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    localStorage.setItem('token', data.token);
    return data.user;
  },

  /** Token'ı silerek çıkış yapar */
  logout: () => {
    localStorage.removeItem('token');
  },

  /** Mevcut oturum açmış kullanıcı bilgilerini getirir */
  getCurrentUser: async () => {
    const data = await apiRequest('/auth/me');
    return data.user;
  },

  /** Kullanıcı adı ve meslek bilgisini günceller */
  updateProfile: async (username: string, profession?: string | null) => {
    const data = await apiRequest('/auth/update-profile', {
      method: 'PUT',
      body: JSON.stringify({ username, profession }),
    });
    return data.user;
  },

  /** Şifre değiştirme isteği gönderir */
  changePassword: async (currentPassword: string, newPassword: string) => {
    return apiRequest('/auth/change-password', {
      method: 'PUT',
      body: JSON.stringify({ currentPassword, newPassword }),
    });
  },
};

/** Favori hisse senedi işlemleri */
export const favoritesAPI = {
  /** Kullanıcının tüm favori hisselerini getirir */
  getAll: async () => {
    const data = await apiRequest('/favorites');
    return data.favorites;
  },

  /** Favorilere yeni hisse ekler */
  add: async (symbol: string, stockName: string) => {
    const data = await apiRequest('/favorites', {
      method: 'POST',
      body: JSON.stringify({ symbol, stockName }),
    });
    return data.favorite;
  },

  /** Favorilerden hisse kaldırır */
  remove: async (symbol: string) => {
    await apiRequest(`/favorites/${symbol}`, { method: 'DELETE' });
  },

  /** Hissenin favorilerde olup olmadığını kontrol eder */
  check: async (symbol: string) => {
    const data = await apiRequest(`/favorites/check/${symbol}`);
    return data.isFavorite;
  },
};

/** Hisse senedi yorum işlemleri */
export const commentsAPI = {
  /** Belirli bir hisseye ait tüm yorumları getirir */
  getBySymbol: async (symbol: string) => {
    const data = await apiRequest(`/comments/${symbol}`);
    return data.comments;
  },

  /** Yeni yorum ekler */
  add: async (symbol: string, content: string) => {
    const data = await apiRequest('/comments', {
      method: 'POST',
      body: JSON.stringify({ symbol, content }),
    });
    return data.comment;
  },

  /** Mevcut yorumu günceller */
  update: async (id: string, content: string) => {
    const data = await apiRequest(`/comments/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
    return data.comment;
  },

  /** Yorumu siler */
  delete: async (id: string) => {
    await apiRequest(`/comments/${id}`, { method: 'DELETE' });
  },
};
