/**
 * Architecture review API client.
 */

import { API_BASE_URL } from "@/lib/api";
import { parseApiError } from "@/lib/errors";
import type {
  ArchitectureReviewRequest,
  ArchitectureReviewResponse,
} from "@/types/review";

export async function submitArchitectureReview(
  payload: ArchitectureReviewRequest,
): Promise<ArchitectureReviewResponse> {
  const response = await fetch(`${API_BASE_URL}/review`, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });

  if (!response.ok) {
    throw await parseApiError(response);
  }

  return response.json() as Promise<ArchitectureReviewResponse>;
}
