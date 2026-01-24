import { commentsAPI } from '@/lib/api';

export const getComments = (symbol: string) => commentsAPI.getBySymbol(symbol);
export const addComment = (userId: string, symbol: string, content: string) => 
  commentsAPI.add(symbol, content);
export const deleteComment = (id: string) => commentsAPI.delete(id);
export const updateComment = (id: string, content: string) => 
  commentsAPI.update(id, content);