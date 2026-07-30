import * as SecureStore from "expo-secure-store";
import { create } from "zustand";

import type { User } from "@/lib/types";

const ACCESS_TOKEN_KEY = "sentiken_access_token";
const REFRESH_TOKEN_KEY = "sentiken_refresh_token";
// Penanda permanen "pernah berhasil login setidaknya sekali", terpisah dari
// accessToken yang bisa kedaluwarsa/hilang. Dipakai AuthGate untuk membedakan
// "backend sedang mati tapi HP ini pernah dipakai sebelumnya" (boleh masuk
// mode lihat-saja dengan data tersimpan) vs "belum pernah berhasil connect
// sama sekali" (tidak ada apa pun untuk ditampilkan). Dihapus hanya saat
// logout eksplisit.
const HAS_EVER_AUTHENTICATED_KEY = "sentiken_has_ever_authenticated";

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isHydrated: boolean;
  hasEverAuthenticated: boolean;
  hydrate: () => Promise<void>;
  setSession: (accessToken: string, refreshToken: string, user: User) => Promise<void>;
  setTokens: (accessToken: string, refreshToken: string) => Promise<void>;
  clearSession: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  isHydrated: false,
  hasEverAuthenticated: false,

  hydrate: async () => {
    const [accessToken, refreshToken, hasEverAuthenticated] = await Promise.all([
      SecureStore.getItemAsync(ACCESS_TOKEN_KEY),
      SecureStore.getItemAsync(REFRESH_TOKEN_KEY),
      SecureStore.getItemAsync(HAS_EVER_AUTHENTICATED_KEY),
    ]);
    set({ accessToken, refreshToken, hasEverAuthenticated: hasEverAuthenticated === "1", isHydrated: true });
  },

  setSession: async (accessToken, refreshToken, user) => {
    await Promise.all([
      SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken),
      SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken),
      SecureStore.setItemAsync(HAS_EVER_AUTHENTICATED_KEY, "1"),
    ]);
    set({ accessToken, refreshToken, user, hasEverAuthenticated: true });
  },

  setTokens: async (accessToken, refreshToken) => {
    await Promise.all([
      SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken),
      SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken),
    ]);
    set({ accessToken, refreshToken });
  },

  clearSession: async () => {
    await Promise.all([
      SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY),
      SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY),
      SecureStore.deleteItemAsync(HAS_EVER_AUTHENTICATED_KEY),
    ]);
    set({ accessToken: null, refreshToken: null, user: null, hasEverAuthenticated: false });
  },
}));
