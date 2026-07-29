import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { DictionaryEntry, DictionaryType, PaginatedResponse } from "@/lib/types";

export function useDictionaryEntries(type: DictionaryType, search: string, page = 1) {
  return useQuery({
    queryKey: ["dictionaries", type, search, page],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<DictionaryEntry>>(
        `/dictionaries/${type}`,
        { params: { search: search || undefined, page, page_size: 20 } },
      );
      return data;
    },
  });
}

export function useCreateDictionaryEntry(type: DictionaryType) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Record<string, string | number>) => {
      const { data } = await apiClient.post<DictionaryEntry>(`/dictionaries/${type}`, payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dictionaries", type] }),
  });
}

export function useUpdateDictionaryEntry(type: DictionaryType, id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Record<string, string | number>) => {
      const { data } = await apiClient.put<DictionaryEntry>(`/dictionaries/${type}/${id}`, payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dictionaries", type] }),
  });
}

export function useDeleteDictionaryEntry(type: DictionaryType) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.delete(`/dictionaries/${type}/${id}`);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dictionaries", type] }),
  });
}

export function useImportDictionary(type: DictionaryType) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: { uri: string; name: string; mimeType?: string | null }) => {
      const formData = new FormData();
      formData.append(
        "file",
        { uri: file.uri, name: file.name, type: file.mimeType ?? "text/csv" } as unknown as Blob,
      );
      const { data } = await apiClient.post(`/dictionaries/${type}/import`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data as {
        total_rows: number;
        valid_rows: number;
        invalid_rows: number;
        inserted: number;
        duplicates_skipped: number;
        errors: string[];
      };
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dictionaries", type] }),
  });
}

export function dictionaryExportUrl(type: DictionaryType) {
  return `/dictionaries/${type}/export`;
}
