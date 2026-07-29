import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { AppSource, PaginatedResponse } from "@/lib/types";

export interface AppSourceInput {
  app_name: string;
  package_id: string;
  play_store_url?: string;
  description?: string;
  language?: string;
  country?: string;
  is_active?: boolean;
}

export function useAppSources(params?: { search?: string; is_active?: boolean }) {
  return useQuery({
    queryKey: ["app-sources", params],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<AppSource>>("/app-sources", {
        params: { ...params, page_size: 100 },
      });
      return data;
    },
  });
}

export function useCreateAppSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: AppSourceInput) => {
      const { data } = await apiClient.post<AppSource>("/app-sources", payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["app-sources"] }),
  });
}

export function useUpdateAppSource(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<AppSourceInput>) => {
      const { data } = await apiClient.put<AppSource>(`/app-sources/${id}`, payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["app-sources"] }),
  });
}

export function useDeleteAppSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/app-sources/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["app-sources"] }),
  });
}

export function useValidateAppSource() {
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post(`/app-sources/${id}/validate`);
      return data as {
        package_id: string;
        is_valid: boolean;
        exists_on_play_store: boolean;
        detail: string;
        play_store_app_name: string | null;
      };
    },
  });
}
