import type { ArchitectureReviewFormValues } from "@/types/review";

export const DEFAULT_REVIEW_FORM_VALUES: ArchitectureReviewFormValues = {
  application_name: "Customer Support Bot",
  frontend: "React",
  backend: "FastAPI",
  llm: "GPT-5.5",
  vector_db: "Pinecone",
  embeddings: "BGE Large",
  cache: "None",
  monitoring: "None",
  authentication: "JWT",
  traffic: "1000",
};

export const REVIEW_FORM_FIELDS = [
  { name: "application_name", label: "Application Name", type: "text" },
  { name: "frontend", label: "Frontend", type: "text" },
  { name: "backend", label: "Backend", type: "text" },
  { name: "llm", label: "LLM", type: "text" },
  { name: "vector_db", label: "Vector DB", type: "text" },
  { name: "embeddings", label: "Embeddings", type: "text" },
  { name: "cache", label: "Cache", type: "text" },
  { name: "monitoring", label: "Monitoring", type: "text" },
  { name: "authentication", label: "Authentication", type: "text" },
  { name: "traffic", label: "Traffic", type: "number" },
] as const satisfies ReadonlyArray<{
  name: keyof ArchitectureReviewFormValues;
  label: string;
  type: "text" | "number";
}>;
