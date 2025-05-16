export interface Tool {
  id: string;
  name: string;
  description: string;
  category: string;
  icon?: string;
  version: string;
  status: 'active' | 'inactive' | 'deprecated';
  connectionUrl?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code: string;
  };
}

