import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import { useAuthStore } from "@/lib/store/authStore";
import type { User } from "@/lib/types";

interface LoginPayload {
  email: string;
  password: string;
}

export function useLogin() {
  const setSession = useAuthStore((s) => s.setSession);

  return useMutation({
    mutationFn: async (payload: LoginPayload) => {
      const { data } = await apiClient.post("/auth/login", payload);
      return data as { access_token: string; refresh_token: string };
    },
    onSuccess: async (data) => {
      // Simpan token dulu agar request /auth/me berikutnya membawa Authorization header.
      await setSession(data.access_token, data.refresh_token, {} as User);
      const me = await apiClient.get<User>("/auth/me");
      await setSession(data.access_token, data.refresh_token, me.data);
    },
  });
}

export function useLogout() {
  const { refreshToken, clearSession } = useAuthStore();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      if (refreshToken) {
        await apiClient.post("/auth/logout", { refresh_token: refreshToken }).catch(() => undefined);
      }
    },
    onSettled: async () => {
      await clearSession();
      queryClient.clear();
    },
  });
}

export function useCurrentUser() {
  const accessToken = useAuthStore((s) => s.accessToken);
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const { data } = await apiClient.get<User>("/auth/me");
      return data;
    },
    enabled: !!accessToken,
    retry: false,
  });
}
