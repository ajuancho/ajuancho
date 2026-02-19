/** @type {import('tailwindcss').Config} */

/**
 * Bahoy - Configuración de Tailwind CSS
 * Colores de marca para la plataforma de eventos de Buenos Aires.
 */

module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],

  darkMode: 'class',

  theme: {
    extend: {
      colors: {
        // Primario: Rojo Buenos Aires
        primary: {
          50:  '#fef2f3',
          100: '#fde6e7',
          200: '#fcd0d3',
          300: '#f9a9ae',
          400: '#f4757d',
          500: '#e63946',
          600: '#d32536',
          700: '#b11a2a',
          800: '#941928',
          900: '#7c1a27',
          950: '#430b13',
        },
        // Secundario: Azul oscuro
        secondary: {
          50:  '#f0f4f9',
          100: '#dce7f1',
          200: '#c0d4e8',
          300: '#93b8d6',
          400: '#5f93bc',
          500: '#3d74a0',
          600: '#2e5a86',
          700: '#274a6e',
          800: '#1d3557',
          900: '#1a2f4c',
          950: '#111e30',
        },
        // Acento: Crema
        accent: {
          light:   '#f8fcf5',
          DEFAULT: '#f1faee',
          dark:    '#d9f0d0',
        },
        // Estados
        success: {
          light:   '#86efac',
          DEFAULT: '#22c55e',
          dark:    '#16a34a',
        },
        warning: {
          light:   '#fde047',
          DEFAULT: '#eab308',
          dark:    '#ca8a04',
        },
        error: {
          light:   '#fca5a5',
          DEFAULT: '#ef4444',
          dark:    '#dc2626',
        },
      },

      fontFamily: {
        sans:    ['var(--font-inter)', 'system-ui', 'sans-serif'],
        display: ['var(--font-playfair)', 'Georgia', 'serif'],
      },

      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '100': '25rem',
        '112': '28rem',
        '128': '32rem',
      },

      container: {
        center: true,
        padding: {
          DEFAULT: '1rem',
          sm: '2rem',
          lg: '4rem',
          xl: '5rem',
          '2xl': '6rem',
        },
      },

      animation: {
        'fade-in':    'fadeIn 0.4s ease-in-out',
        'slide-up':   'slideUp 0.4s ease-out',
        'slide-down': 'slideDown 0.4s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },

      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%':   { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',    opacity: '1' },
        },
        slideDown: {
          '0%':   { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)',      opacity: '1' },
        },
      },

      boxShadow: {
        soft: '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        card: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },

      borderRadius: {
        xl:  '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
    },
  },

  plugins: [],
}
