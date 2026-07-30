import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { resolveApiBaseUrl } from "@/lib/api/remoteConfig";
import { useAuthStore } from "@/lib/store/authStore";
import { useConnectivityStore } from "@/lib/store/connectivityStore";
import type { ApiErrorBody } from "@/lib/types";

const DEFAULT_API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: DEFAULT_API_URL,
  timeout: 30000,
});

let initPromise: Promise<string> | null = null;

/** Dipanggil sekali di awal (AuthGate) untuk resolve base URL API sebelum request lain berjalan. */
export function initApiClient(options?: { force?: boolean }): Promise<string> {
  if (options?.force || !initPromise) {
    initPromise = resolveApiBaseUrl().then((baseUrl) => {
      apiClient.defaults.baseURL = baseUrl;
      return baseUrl;
    });
  }
  return initPromise;
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshPromise: Promise<string | null> | null = null;

export async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, setTokens, clearSession } = useAuthStore.getState();
  if (!refreshToken) return null;

  try {
    const response = await axios.post(`${apiClient.defaults.baseURL}/auth/refresh`, {
      refresh_token: refreshToken,
    });
    const { access_token, refresh_token } = response.data;
    await setTokens(access_token, refresh_token);
    return access_token;
  } catch {
    await clearSession();
    return null;
  }
}

apiClient.interceptors.response.use(
  (response) => {
    useConnectivityStore.getState().setBackendReachable(true);
    return response;
  },
  async (error: AxiosError) => {
    // error.response ada => server sempat menjawab (walau statusnya error,
    // mis. 401/404/500) => backend tetap terjangkau. Kalau tidak ada sama
    // sekali => gagal jaringan/timeout => backend/tunnel kemungkinan mati.
    useConnectivityStore.getState().setBackendReachable(!!error.response);

    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      if (!refreshPromise) {
        refreshPromise = refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
      }
      const newToken = await refreshPromise;
      if (newToken) {
        originalRequest.headers = originalRequest.headers ?? {};
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return apiClient.request(originalRequest);
      }
    }
    return Promise.reject(error);
  },
);

export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const body = error.response?.data as ApiErrorBody | undefined;
    if (body?.error?.message) return body.error.message;
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Terjadi kesalahan yang tidak diketahui.";
}
