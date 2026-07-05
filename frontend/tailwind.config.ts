import type { Config } from 'tailwindcss';

/**
 * Colors are wired to CSS variables (see src/index.css) so a single token set
 * drives both light and dark themes. `<alpha-value>` lets Tailwind opacity
 * utilities work with the HSL channel variables.
 */
function token(variable: string) {
  return `hsl(var(${variable}) / <alpha-value>)`;
}

const config: Config = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    container: {
      center: true,
      padding: '1.5rem',
      screens: { '2xl': '1400px' },
    },
    extend: {
      colors: {
        background: token('--background'),
        surface: {
          DEFAULT: token('--surface'),
          foreground: token('--surface-foreground'),
        },
        foreground: token('--foreground'),
        muted: {
          DEFAULT: token('--muted'),
          foreground: token('--muted-foreground'),
        },
        border: token('--border'),
        input: token('--input'),
        ring: token('--ring'),
        primary: {
          DEFAULT: token('--primary'),
          foreground: token('--primary-foreground'),
        },
        positive: {
          DEFAULT: token('--positive'),
          foreground: token('--positive-foreground'),
        },
        negative: {
          DEFAULT: token('--negative'),
          foreground: token('--negative-foreground'),
        },
        warning: {
          DEFAULT: token('--warning'),
          foreground: token('--warning-foreground'),
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      keyframes: {
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.15s ease-out',
      },
    },
  },
  plugins: [],
};

export default config;
