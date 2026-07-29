import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Slot, useRouter, useSegments } from "expo-router";
import { useEffect, useState } from "react";
import { View } from "react-native";

import { ErrorState } from "@/components/ui/ErrorState";
import { ToastHost } from "@/components/ui/ToastHost";
import { LoadingState } from "@/components/ui/LoadingState";
import { useLogin } from "@/lib/hooks/useAuth";
import { useAuthStore } from "@/lib/store/authStore";
import { useThemeColors } from "@/lib/hooks/useThemeColors";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 15000 },
  },
});

const AUTO_LOGIN_EMAIL = process.env.EXPO_PUBLIC_AUTO_LOGIN_EMAIL;
const AUTO_LOGIN_PASSWORD = process.env.EXPO_PUBLIC_AUTO_LOGIN_PASSWORD;

// Aplikasi ini dipakai sendiri di jaringan lokal, jadi login dilakukan otomatis
// di background memakai kredensial bawaan alih-alih menampilkan layar login.
function AuthGate({ children }: { children: React.ReactNode }) {
  const { accessToken, isHydrated, hydrate } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();
  const loginMutation = useLogin();
  const [autoLoginFailed, setAutoLoginFailed] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!isHydrated || accessToken) return;

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
  }, [isHydrated, accessToken, retryCount]);

  useEffect(() => {
    if (!isHydrated || !accessToken) return;
    if (segments[0] !== "(tabs)") {
      router.replace("/(tabs)/dashboard");
    }
  }, [accessToken, isHydrated, segments, router]);

  if (!isHydrated) {
    return <LoadingState label="Menyiapkan aplikasi..." />;
  }

  if (!accessToken) {
    if (autoLoginFailed) {
      return (
        <ErrorState
          message="Tidak bisa terhubung ke server. Pastikan backend jalan dan HP satu jaringan dengan PC."
          onRetry={() => setRetryCount((count) => count + 1)}
        />
      );
    }
    return <LoadingState label="Menghubungkan..." />;
  }

  return <>{children}</>;
}

export default function RootLayout() {
  const { colors } = useThemeColors();

  return (
    <QueryClientProvider client={queryClient}>
      <AuthGate>
        <View style={{ flex: 1, backgroundColor: colors.background }}>
          <Slot />
          <ToastHost />
        </View>
      </AuthGate>
    </QueryClientProvider>
  );
}
