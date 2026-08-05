/**
 * Frontend service layer for backend API calls.
 *
 * Components should call these helpers instead of fetching directly,
 * so transport concerns stay isolated from the UI.
 */

import { API_BASE_URL } from "@/lib/api";
import type { HealthResponse } from "@/types/health";

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}
