import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { LabelSummary } from "@/lib/types";

export function useLabelSummary(datasetId: string | undefined) {
  return useQuery({
    queryKey: ["label-summary", datasetId],
    queryFn: async () => {
      const { data } = await apiClient.get<LabelSummary>(`/datasets/${datasetId}/label-summary`);
      return data;
    },
    enabled: !!datasetId,
    refetchInterval: (query) => (query.state.data?.status === "running" ? 1500 : false),
  });
}

export function useStartLabeling(datasetId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (labelMode: "binary" | "ternary") => {
      const { data } = await apiClient.post(`/datasets/${datasetId}/label`, { label_mode: labelMode });
      return data;
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["label-summary", datasetId] }),
  });
}
