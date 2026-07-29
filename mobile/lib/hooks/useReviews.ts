import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api/client";
import type { ReviewDetail } from "@/lib/types";

export function useReviewDetail(reviewId: string | undefined) {
  return useQuery({
    queryKey: ["review-detail", reviewId],
    queryFn: async () => {
      const { data } = await apiClient.get<ReviewDetail>(`/reviews/${reviewId}`);
      return data;
    },
    enabled: !!reviewId,
  });
}
