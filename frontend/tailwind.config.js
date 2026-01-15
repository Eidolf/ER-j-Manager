/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                cyber: {
                    black: '#0a0a0f',
                    dark: '#12121a',
                    card: '#1b1b26',
                    neon: '#0088ff',     // Blue
                    pink: '#ff00ff',
                    purple: '#ff2244',   // Red
                    dim: 'rgba(0, 136, 255, 0.1)',
                }
            }
        },
        fontFamily: {
            mono: ['Fira Code', 'monospace'],
            sans: ['Inter', 'sans-serif'],
        },
        backgroundImage: {
            'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
            'cyber-grid': 'linear-gradient(to right, #1b1b26 1px, transparent 1px), linear-gradient(to bottom, #1b1b26 1px, transparent 1px)',
        }
    },
    plugins: [],
}
