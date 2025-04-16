export interface User {
  id: string;
  username: string;
}

export interface AuthService {
  isAuthenticated: boolean;
  user: User | null;
  login: () => Promise<void>;
  logout: () => Promise<void>;
}

class LocalAuthService implements AuthService {
  private _isAuthenticated: boolean = false;
  private _user: User | null = null;

  get isAuthenticated(): boolean {
    return this._isAuthenticated;
  }

  get user(): User | null {
    return this._user;
  }

  async login(): Promise<void> {
    // For local development, auto-login with test user
    this._isAuthenticated = true;
    this._user = {
      id: 'local-user',
      username: 'test-user'
    };
  }

  async logout(): Promise<void> {
    this._isAuthenticated = false;
    this._user = null;
  }
}

export const authService = new LocalAuthService();
