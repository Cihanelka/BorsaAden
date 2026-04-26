/**
 * Created by: Aden Borsa Team
 * Created At: 2025
 * Subject: Kullanıcı oturum durumunu yöneten React Context
 */
import { createContext, useContext, useEffect, useState } from 'react';
import { authAPI } from '@/lib/api';

interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  profession?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (email: string, password: string, fullName: string, username: string, profession: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

/**
 * Uygulama genelinde kimlik doğrulama durumunu sağlayan provider.
 * Sayfa yenilemesinde token varsa otomatik oturum açar.
 */
export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    /** Uygulama başlarken mevcut token'ı doğrulayıp kullanıcıyı yükler */
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const currentUser = await authAPI.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          console.error('Auth check failed:', error);
          localStorage.removeItem('token');
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  /** Yeni kullanıcı kaydı oluşturur ve oturum açar */
  const signUp = async (email: string, password: string, fullName: string, username: string, profession: string) => {
    const newUser = await authAPI.register(email, password, fullName, username, profession);
    setUser(newUser);
  };

  /** Kullanıcı girişi yapar */
  const signIn = async (email: string, password: string) => {
    const loggedInUser = await authAPI.login(email, password);
    setUser(loggedInUser);
  };

  /** Oturumu kapatır ve kullanıcı state'ini sıfırlar */
  const signOut = async () => {
    authAPI.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * AuthContext'e erişim hook'u.
 * AuthProvider dışında kullanılırsa hata fırlatır.
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
