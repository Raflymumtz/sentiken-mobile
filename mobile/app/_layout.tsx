import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Slot, useRouter, useSegments } from "expo-router";
import { useEffect } from "react";
import { View } from "react-native";

import { ToastHost } from "@/components/ui/ToastHost";
import { LoadingState } from "@/components/ui/LoadingState";
import { useAuthStore } from "@/lib/store/authStore";
import { useThemeColors } from "@/lib/hooks/useThemeColors";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 15000 },
  },
});

function AuthGate({ children }: { children: React.ReactNode }) {
  const { accessToken, isHydrated, hydrate } = useAuthStore();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!isHydrated) return;
    const inAuthGroup = segments[0] === "(auth)";

    if (!accessToken && !inAuthGroup) {
      router.replace("/(auth)/login");
    } else if (accessToken && inAuthGroup) {
      router.replace("/(tabs)/dashboard");
    }
  }, [accessToken, isHydrated, segments, router]);

  if (!isHydrated) {
    return <LoadingState label="Menyiapkan aplikasi..." />;
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
