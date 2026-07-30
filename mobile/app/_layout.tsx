import AsyncStorage from "@react-native-async-storage/async-storage";
import { createAsyncStoragePersister } from "@tanstack/query-async-storage-persister";
import { QueryClient, useIsRestoring } from "@tanstack/react-query";
import { PersistQueryClientProvider } from "@tanstack/react-query-persist-client";
import { Slot, useRouter, useSegments } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { StyleSheet, View } from "react-native";

import { ErrorState } from "@/components/ui/ErrorState";
import { OfflineBanner } from "@/components/ui/OfflineBanner";
import { ToastHost } from "@/components/ui/ToastHost";
import { LoadingState } from "@/components/ui/LoadingState";
import { initApiClient } from "@/lib/api/client";
import { useLogin } from "@/lib/hooks/useAuth";
import { useAuthStore } from "@/lib/store/authStore";
import { useThemeColors } from "@/lib/hooks/useThemeColors";

// gcTime menentukan berapa lama data query disimpan di memori/disk sebelum
// dibuang -- harus >= maxAge persister di bawah, supaya data yang dipulihkan
// dari penyimpanan tidak langsung dianggap kedaluwarsa dan dibuang lagi.
const CACHE_MAX_AGE_MS = 1000 * 60 * 60 * 24 * 7; // 7 hari

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 15000, gcTime: CACHE_MAX_AGE_MS },
  },
});

const asyncStoragePersister = createAsyncStoragePersister({
  storage: AsyncStorage,
  key: "sentiken-query-cache",
});

// Jarak antar percobaan auto-reconnect diam-diam saat sedang mode offline
// (lihat-saja). Kalau backend hidup lagi, aplikasi otomatis kembali online
// tanpa pengguna perlu menekan apa pun.
const AUTO_RETRY_INTERVAL_MS = 30000;

const AUTO_LOGIN_EMAIL = process.env.EXPO_PUBLIC_AUTO_LOGIN_EMAIL;
const AUTO_LOGIN_PASSWORD = process.env.EXPO_PUBLIC_AUTO_LOGIN_PASSWORD;

// Aplikasi ini dipakai sendiri di jaringan lokal, jadi login dilakukan otomatis
// di background memakai kredensial bawaan alih-alih menampilkan layar login.
//
// PENTING: expo-router mewajibkan Root Layout merender <Slot /> (atau
// navigator lain) sejak render PERTAMA -- kalau tidak, navigasi apa pun
// (termasuk router.replace() di bawah) akan crash dengan error "Attempted
// to navigate before mounting the Root Layout component". Karena itu Slot
// di bawah SELALU dirender; status loading/offline ditampilkan sebagai
// overlay/banner di atasnya, bukan menggantikannya -- ini juga yang membuat
// mode "lihat-saja" (data tersimpan saat backend mati) memungkinkan: kalau
// login otomatis gagal tapi HP ini pernah berhasil login sebelumnya, kita
// tetap render Slot (dengan data query yang sudah dipulihkan dari cache
// tersimpan) alih-alih memblokir dengan layar error penuh.
function AuthGate({ children }: { children: React.ReactNode }) {
  const { colors } = useThemeColors();
  const { accessToken, isHydrated, hasEverAuthenticated, hydrate } = useAuthStore();
  const isRestoringCache = useIsRestoring();
  const segments = useSegments();
  const router = useRouter();
  const loginMutation = useLogin();
  const [autoLoginFailed, setAutoLoginFailed] = useState(false);
  const [isApiReady, setIsApiReady] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  // Resolve URL backend dari GitHub (bisa berubah kalau tunnel di-restart di
  // laptop) sebelum request lain (termasuk auto-login) dijalankan.
  useEffect(() => {
    initApiClient({ force: retryCount > 0 }).finally(() => setIsApiReady(true));
  }, [retryCount]);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!isApiReady || !isHydrated || accessToken) return;

    if (!AUTO_LOGIN_EMAIL || !AUTO_LOGIN_PASSWORD) {
      setAutoLoginFailed(true);
      return;
    }

    setAutoLoginFailed(false);
    loginMutation.mutate(
      { email: AUTO_LOGIN_EMAIL, password: AUTO_LOGIN_PASSWORD },
      { onError: () => setAutoLoginFailed(true) },
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isApiReady, isHydrated, accessToken, retryCount]);

  useEffect(() => {
    if (!isHydrated || !accessToken) return;
    if (segments[0] !== "(tabs)") {
      router.replace("/(tabs)/dashboard");
    }
  }, [accessToken, isHydrated, segments, router]);

  const isPreparing = !isApiReady || !isHydrated || isRestoringCache;
  const isConnecting = !isPreparing && !accessToken && !autoLoginFailed;
  // Backend tidak terjangkau, tapi HP ini pernah berhasil login sebelumnya --
  // masuk mode lihat-saja memakai data tersimpan alih-alih memblokir total.
  const isOfflineViewable = !isPreparing && !accessToken && autoLoginFailed && hasEverAuthenticated;
  // Belum pernah berhasil connect sama sekali (mis. HP baru pertama kali
  // dipakai) -- tidak ada data tersimpan apa pun untuk ditampilkan.
  const isBlockedNoData = !isPreparing && !accessToken && autoLoginFailed && !hasEverAuthenticated;

  // Auto-reconnect diam-diam selama mode offline, supaya begitu backend
  // hidup lagi aplikasi otomatis kembali online tanpa aksi pengguna.
  const retryCountRef = useRef(retryCount);
  retryCountRef.current = retryCount;
  useEffect(() => {
    if (!isOfflineViewable) return;
    const interval = setInterval(() => {
      setRetryCount(retryCountRef.current + 1);
    }, AUTO_RETRY_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [isOfflineViewable]);

  if (isBlockedNoData) {
    return (
      <View style={[StyleSheet.absoluteFill, { backgroundColor: colors.background }]}>
        <ErrorState
          message="Tidak bisa terhubung ke server. Pastikan backend & tunnel di laptop sedang menyala."
          onRetry={() => setRetryCount((count) => count + 1)}
        />
      </View>
    );
  }

  return (
    <View style={{ flex: 1 }}>
      {isOfflineViewable ? <OfflineBanner onRetry={() => setRetryCount((count) => count + 1)} /> : null}

      {children}

      {isPreparing || isConnecting ? (
        <View
          style={[
            StyleSheet.absoluteFill,
            { backgroundColor: colors.background, justifyContent: "center", alignItems: "center" },
          ]}
        >
          <LoadingState label={isPreparing ? "Menyiapkan aplikasi..." : "Menghubungkan..."} />
        </View>
      ) : null}
    </View>
  );
}

export default function RootLayout() {
  const { colors } = useThemeColors();

  return (
    <PersistQueryClientProvider
      client={queryClient}
      persistOptions={{ persister: asyncStoragePersister, maxAge: CACHE_MAX_AGE_MS }}
    >
      <AuthGate>
        <View style={{ flex: 1, backgroundColor: colors.background }}>
          <Slot />
          <ToastHost />
        </View>
      </AuthGate>
    </PersistQueryClientProvider>
  );
}
