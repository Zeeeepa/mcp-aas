import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

export interface User {
  id: string;
  email: string;
  name: string;
}

export interface AuthResponse {
  token: string;
  user: User;
}

export const register = async (email: string, password: string, name: string): Promise<AuthResponse> => {
  const response = await axios.post(`${API_URL}/auth/register`, {
    email,
    password,
    name,
  });
  const { token, user } = response.data;
  localStorage.setItem('token', token);
  return { token, user };
};

export const login = async (email: string, password: string): Promise<AuthResponse> => {
  const response = await axios.post(`${API_URL}/auth/login`, {
    email,
    password,
  });
  const { token, user } = response.data;
  localStorage.setItem('token', token);
  return { token, user };
};

export const logout = () => {
  localStorage.removeItem('token');
};

export const getCurrentUser = (): User | null => {
  const token = localStorage.getItem('token');
  if (!token) return null;

  try {
    const decoded = jwtDecode<{ id: string }>(token);
    if (!decoded.id) return null;
    return decoded as unknown as User;
  } catch {
    return null;
  }
};

export const getAuthHeader = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};
