/**
 * Production-inspired example architectures for first-run demos.
 *
 * Data only — UI and form population live elsewhere.
 */

import type { ArchitectureReviewFormValues } from "@/types/review";

export type ExampleArchitectureId =
  | "customer-support-rag"
  | "ai-coding-assistant"
  | "financial-copilot"
  | "enterprise-search"
  | "multi-agent-research";

export type ExampleArchitecture = {
  id: ExampleArchitectureId;
  name: string;
  description: string;
  /** Display-only technology labels shown on example cards. */
  stack: readonly string[];
  /** Values applied to the architecture review form. */
  formValues: ArchitectureReviewFormValues;
};

export const EXAMPLE_ARCHITECTURES: readonly ExampleArchitecture[] = [
  {
    id: "customer-support-rag",
    name: "Customer Support RAG",
    description:
      "Enterprise customer support assistant using Retrieval-Augmented Generation.",
    stack: [
      "React",
      "FastAPI",
      "GPT-5.5",
      "Pinecone",
      "Redis",
      "Langfuse",
      "JWT",
    ],
    formValues: {
      application_name: "Customer Support RAG",
      frontend: "React",
      backend: "FastAPI",
      llm: "GPT-5.5",
      vector_db: "Pinecone",
      embeddings: "BGE Large",
      cache: "Redis",
      monitoring: "Langfuse",
      authentication: "JWT",
      traffic: "5000",
    },
  },
  {
    id: "ai-coding-assistant",
    name: "AI Coding Assistant",
    description: "Cursor-style coding assistant for repositories.",
    stack: ["Next.js", "FastAPI", "Claude", "PostgreSQL", "Redis", "JWT"],
    formValues: {
      application_name: "AI Coding Assistant",
      frontend: "Next.js",
      backend: "FastAPI",
      llm: "Claude",
      vector_db: "PostgreSQL",
      embeddings: "Code Embeddings",
      cache: "Redis",
      monitoring: "None",
      authentication: "JWT",
      traffic: "2500",
    },
  },
  {
    id: "financial-copilot",
    name: "Financial Copilot",
    description:
      "AI assistant for investment research and financial analysis.",
    stack: ["React", "FastAPI", "GPT-5.5", "Pinecone", "AWS", "JWT"],
    formValues: {
      application_name: "Financial Copilot",
      frontend: "React",
      backend: "FastAPI",
      llm: "GPT-5.5",
      vector_db: "Pinecone",
      embeddings: "text-embedding-3-large",
      cache: "None",
      monitoring: "AWS",
      authentication: "JWT",
      traffic: "3000",
    },
  },
  {
    id: "enterprise-search",
    name: "Enterprise Search",
    description: "Company-wide knowledge search with hybrid retrieval.",
    stack: [
      "React",
      "FastAPI",
      "OpenAI",
      "Elasticsearch",
      "Redis",
      "Hybrid Search",
    ],
    formValues: {
      application_name: "Enterprise Search",
      frontend: "React",
      backend: "FastAPI",
      llm: "OpenAI",
      vector_db: "Elasticsearch",
      embeddings: "Hybrid Search",
      cache: "Redis",
      monitoring: "None",
      authentication: "None",
      traffic: "12000",
    },
  },
  {
    id: "multi-agent-research",
    name: "Multi-Agent Research System",
    description:
      "Multiple specialized AI agents collaborating on research tasks.",
    stack: [
      "Next.js",
      "FastAPI",
      "Multiple LLMs",
      "Redis",
      "PostgreSQL",
      "LangGraph",
    ],
    formValues: {
      application_name: "Multi-Agent Research System",
      frontend: "Next.js",
      backend: "FastAPI",
      llm: "Multiple LLMs via LangGraph",
      vector_db: "PostgreSQL",
      embeddings: "OpenAI Embeddings",
      cache: "Redis",
      monitoring: "None",
      authentication: "JWT",
      traffic: "8000",
    },
  },
] as const;

export function getExampleArchitecture(
  id: ExampleArchitectureId,
): ExampleArchitecture | undefined {
  return EXAMPLE_ARCHITECTURES.find((example) => example.id === id);
}
