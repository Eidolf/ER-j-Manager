import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const api = axios.create({
    baseURL: API_URL,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Add response interceptor to handle 401s (Token Expiry)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('token');
            // If we are not already on the login page, redirect
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export interface Package {
    uuid: string;
    name: string;
    links: Link[];
    total_bytes: number;
    loaded_bytes: number;
    status: string;
    speed?: number;  // Current download speed in bytes/sec
    status_text?: string; // Raw status text from JD API
}

export interface Link {
    uuid: string;
    name: string;
    url: string;
    status: string;
    bytes_total: number;
    bytes_loaded: number;
    speed: number;
}

export interface SystemStatus {
    jd_online: boolean;
    buffer_count: number;
}
