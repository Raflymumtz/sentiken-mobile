import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { CollectionJob, PaginatedResponse } from "@/lib/types";

export interface CollectionJobInput {
  app_source_id: string;
  dataset_id: string;
  period_start?: string;
  period_end?: string;
  max_reviews: number;
  language: string;
  country: string;
  sort_order: "newest" | "rating" | "relevance";
  method?: string;
}

export function useCollectionJobs(datasetId?: string) {
  return useQuery({
    queryKey: ["collection-jobs", datasetId],
    queryFn: async () => {
      const { data } = await apiClient.get<PaginatedResponse<CollectionJob>>("/collection-jobs", {
        params: { dataset_id: datasetId, page_size: 50 },
      });
      return data;
    },
    enabled: !!datasetId,
  });
}

export function useCollectionJob(id: string | undefined) {
  return useQuery({
    queryKey: ["collection-jobs", "detail", id],
    queryFn: async () => {
      const { data } = await apiClient.get<CollectionJob>(`/collection-jobs/${id}`);
      return data;
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "queued" || status === "running" ? 1500 : false;
    },
  });
}

export function useCreateCollectionJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CollectionJobInput) => {
      const { data } = await apiClient.post<CollectionJob>("/collection-jobs", payload);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["collection-jobs"] }),
  });
}

export function useCancelCollectionJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await apiClient.post<CollectionJob>(`/collection-jobs/${id}/cancel`);
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["collection-jobs"] }),
  });
}
