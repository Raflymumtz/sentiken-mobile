import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { ImportJob, ImportPreviewResponse } from "@/lib/types";

export interface PickedCsvFile {
  uri: string;
  name: string;
  mimeType?: string | null;
}

export function usePreviewImport(datasetId: string) {
  return useMutation({
    mutationFn: async (file: PickedCsvFile) => {
      const formData = new FormData();
      // React Native FormData menerima objek { uri, name, type } untuk file.
      formData.append(
        "file",
        {
          uri: file.uri,
          name: file.name,
          type: file.mimeType ?? "text/csv",
        } as unknown as Blob,
      );
      const { data } = await apiClient.post<ImportPreviewResponse>(
        `/datasets/${datasetId}/imports/preview`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      return data;
    },
  });
}

export function useExecuteImport(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (uploadToken: string) => {
      const { data } = await apiClient.post<ImportJob>(`/datasets/${datasetId}/imports/execute`, {
        upload_token: uploadToken,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["datasets", "reviews", datasetId] });
      queryClient.invalidateQueries({ queryKey: ["datasets", "summary", datasetId] });
    },
  });
}

export function useImportJob(id: string | undefined) {
  return useQuery({
    queryKey: ["import-jobs", id],
    queryFn: async () => {
      const { data } = await apiClient.get<ImportJob>(`/import-jobs/${id}`);
      return data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 1500 : false;
    },
  });
}
