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

export interface Package {
    uuid: string;
    name: string;
    links: Link[];
    total_bytes: number;
    loaded_bytes: number;
    status: string;
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
