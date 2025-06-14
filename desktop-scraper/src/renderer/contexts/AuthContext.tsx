import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface UserInfo {
  email: string;
  name: string;
  picture?: string;
}

interface AuthStatus {
  authenticated: boolean;
  userInfo?: UserInfo;
  scopes: string[];
  expiresAt?: Date;
}

interface AuthContextType {
  authStatus: AuthStatus;
  loading: boolean;
  error?: string;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  refreshStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [authStatus, setAuthStatus] = useState<AuthStatus>({
    authenticated: false,
    scopes: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>();

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      setLoading(true);
      setError(undefined);
      
      // For now, use localStorage to track auth state
      // In a full implementation, this would check with the backend
      const authData = localStorage.getItem('authStatus');
      if (authData) {
        try {
          const status = JSON.parse(authData);
          setAuthStatus(status);
        } catch {
          setAuthStatus({ authenticated: false, scopes: [] });
        }
      } else {
        setAuthStatus({ authenticated: false, scopes: [] });
      }
    } catch (err) {
      console.error('Failed to check auth status:', err);
      setError(err instanceof Error ? err.message : 'Failed to check authentication status');
      setAuthStatus({ authenticated: false, scopes: [] });
    } finally {
      setLoading(false);
    }
  };

  const login = async () => {
    try {
      setLoading(true);
      setError(undefined);
      
      // Mock login for local development (in a full implementation, 
      // this would redirect to Google OAuth or handle authentication)
      console.log('Simulating authentication...');
      
      const mockAuthStatus = {
        authenticated: true,
        userInfo: {
          email: 'user@example.com',
          name: 'Local User'
        },
        scopes: ['https://www.googleapis.com/auth/spreadsheets']
      };
      
      // Store in localStorage
      localStorage.setItem('authStatus', JSON.stringify(mockAuthStatus));
      setAuthStatus(mockAuthStatus);
    } catch (err) {
      console.error('Login failed:', err);
      setError(err instanceof Error ? err.message : 'Login failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      setLoading(true);
      setError(undefined);
      
      // Clear localStorage
      localStorage.removeItem('authStatus');
      console.log('User logged out');
      
      setAuthStatus({ authenticated: false, scopes: [] });
    } catch (err) {
      console.error('Logout failed:', err);
      setError(err instanceof Error ? err.message : 'Logout failed');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const refreshStatus = async () => {
    await checkAuthStatus();
  };

  return (
    <AuthContext.Provider value={{
      authStatus,
      loading,
      error,
      login,
      logout,
      refreshStatus
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};