import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>('dark');
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('dark');

  useEffect(() => {
    // Load saved theme
    loadSavedTheme();
    
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleSystemThemeChange = () => {
      if (theme === 'system') {
        updateResolvedTheme(theme);
      }
    };

    mediaQuery.addEventListener('change', handleSystemThemeChange);
    return () => mediaQuery.removeEventListener('change', handleSystemThemeChange);
  }, [theme]);

  const loadSavedTheme = async () => {
    try {
      const savedTheme = await window.electronAPI.settings.get('theme') as Theme;
      if (savedTheme) {
        setTheme(savedTheme);
        updateResolvedTheme(savedTheme);
      } else {
        updateResolvedTheme('dark');
      }
    } catch (error) {
      console.error('Failed to load theme:', error);
      updateResolvedTheme('dark');
    }
  };

  const updateResolvedTheme = (newTheme: Theme) => {
    let resolved: 'light' | 'dark';

    if (newTheme === 'system') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } else {
      resolved = newTheme;
    }

    setResolvedTheme(resolved);
    
    // Apply theme to document
    if (resolved === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleSetTheme = async (newTheme: Theme) => {
    setTheme(newTheme);
    updateResolvedTheme(newTheme);
    
    try {
      await window.electronAPI.settings.set('theme', newTheme);
    } catch (error) {
      console.error('Failed to save theme:', error);
    }
  };

  return (
    <ThemeContext.Provider value={{
      theme,
      resolvedTheme,
      setTheme: handleSetTheme
    }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};