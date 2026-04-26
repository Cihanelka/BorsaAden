/**
 * Created by: Aden Borsa Team
 * Created At: 2025
 * Subject: Favori hisse API işlemleri için servis sarıcısı
 */
import { favoritesAPI } from '@/lib/api';

export const getFavorites = () => favoritesAPI.getAll();
export const addFavorite = (userId: string, symbol: string, stockName: string) => 
  favoritesAPI.add(symbol, stockName);
export const removeFavorite = (userId: string, symbol: string) => 
  favoritesAPI.remove(symbol);
export const isFavorite = (userId: string, symbol: string) => 
  favoritesAPI.check(symbol);