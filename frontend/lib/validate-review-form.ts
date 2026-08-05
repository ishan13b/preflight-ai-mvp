import type {
  ArchitectureReviewFormValues,
  ArchitectureReviewRequest,
} from "@/types/review";

export type FormValidationResult =
  | { ok: true; value: ArchitectureReviewRequest }
  | { ok: false; errors: string[] };

/**
 * Validate and normalize form values into a backend-ready payload.
 */
export function validateReviewForm(
  values: ArchitectureReviewFormValues,
): FormValidationResult {
  const errors: string[] = [];

  const application_name = values.application_name.trim();
  const frontend = values.frontend.trim();
  const backend = values.backend.trim();
  const llm = values.llm.trim();
  const vector_db = values.vector_db.trim();
  const embeddings = values.embeddings.trim();
  const cache = values.cache.trim();
  const monitoring = values.monitoring.trim();
  const authentication = values.authentication.trim();
  const trafficRaw = values.traffic.trim();

  if (!application_name) errors.push("Application Name is required.");
  if (!frontend) errors.push("Frontend is required.");
  if (!backend) errors.push("Backend is required.");
  if (!llm) errors.push("LLM is required.");
  if (!vector_db) errors.push("Vector DB is required.");
  if (!embeddings) errors.push("Embeddings is required.");
  if (!cache) errors.push("Cache is required.");
  if (!monitoring) errors.push("Monitoring is required.");
  if (!authentication) errors.push("Authentication is required.");
  if (!trafficRaw) {
    errors.push("Traffic is required.");
  }

  const traffic = Number(trafficRaw);
  if (trafficRaw && (!Number.isInteger(traffic) || traffic < 0)) {
    errors.push("Traffic must be a non-negative integer.");
  }

  if (errors.length > 0) {
    return { ok: false, errors };
  }

  return {
    ok: true,
    value: {
      application_name,
      frontend,
      backend,
      llm,
      vector_db,
      embeddings,
      cache,
      monitoring,
      authentication,
      traffic,
    },
  };
}
