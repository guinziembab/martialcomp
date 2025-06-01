// Theme configuration based on our design system
export const lightTheme = {
  colors: {
    // Primary colors
    primary: '#2E5BFF',
    primaryLight: '#6E8EFF',
    primaryDark: '#0039CB',
    
    // Secondary colors
    secondary: '#FF2E63',
    secondaryLight: '#FF6E91',
    secondaryDark: '#C5003A',
    
    // Accent colors
    accent: '#00C853',
    accentLight: '#5EFF82',
    accentDark: '#009624',
    
    // Neutral colors
    background: '#F5F7FA',
    surface: '#FFFFFF',
    text: '#212121',
    textSecondary: '#757575',
    border: '#E0E0E0',
    
    // Status colors
    error: '#D50000',
    warning: '#FFD600',
    success: '#00C853',
    info: '#2196F3',
    
    // Martial arts specific colors
    martial: {
      red: '#D32F2F',     // For combat or aggressive actions
      blue: '#1976D2',    // For technical scores
      yellow: '#FFC107',  // For warnings
      black: '#212121',   // For belts/grades references
      white: '#FFFFFF',   // For belts/grades references
      gold: '#FFD700',    // For achievements/medals
    }
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    xs: 2,
    sm: 4,
    md: 8,
    lg: 16,
    xl: 24,
    round: 9999,
  },
  typography: {
    fontFamily: {
      regular: 'System',
      medium: 'System-Medium',
      bold: 'System-Bold',
    },
    fontSize: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 30,
    },
    lineHeight: {
      xs: 16,
      sm: 20,
      md: 24,
      lg: 28,
      xl: 32,
      xxl: 36,
      xxxl: 42,
    },
  },
  elevation: {
    z1: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.18,
      shadowRadius: 1.0,
      elevation: 1,
    },
    z2: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.20,
      shadowRadius: 1.41,
      elevation: 2,
    },
    z3: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 3 },
      shadowOpacity: 0.22,
      shadowRadius: 2.22,
      elevation: 3,
    },
    z4: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.25,
      shadowRadius: 3.84,
      elevation: 4,
    },
    z5: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 5 },
      shadowOpacity: 0.30,
      shadowRadius: 4.65,
      elevation: 5,
    },
  },
};

// Dark theme extends light theme and overrides specific values
export const darkTheme = {
  ...lightTheme,
  colors: {
    ...lightTheme.colors,
    // Override neutral colors for dark theme
    background: '#121212',
    surface: '#1E1E1E',
    text: '#FFFFFF',
    textSecondary: '#B0B0B0',
    border: '#333333',
    
    // Dark theme specific overrides for primary and secondary
    primary: '#6E8EFF',
    secondary: '#FF6E91',
    accent: '#5EFF82',
  },
  elevation: {
    // Dark theme elevation needs different values
    z1: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.25,
      shadowRadius: 1.0,
      elevation: 1,
    },
    z2: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.3,
      shadowRadius: 1.41,
      elevation: 2,
    },
    z3: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 3 },
      shadowOpacity: 0.35,
      shadowRadius: 2.22,
      elevation: 3,
    },
    z4: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.4,
      shadowRadius: 3.84,
      elevation: 4,
    },
    z5: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 5 },
      shadowOpacity: 0.45,
      shadowRadius: 4.65,
      elevation: 5,
    },
  },
};

export type Theme = typeof lightTheme;
export type ThemeMode = 'light' | 'dark';