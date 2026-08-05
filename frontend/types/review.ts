/**
 * Architecture review contracts mirrored from the backend schemas.
 */

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type BoardVote =
  | "APPROVED"
  | "APPROVED WITH CONCERNS"
  | "REQUIRES CHANGES";

export interface ArchitectureReviewRequest {
  application_name: string;
  frontend: string;
  backend: string;
  llm: string;
  vector_db: string;
  embeddings: string;
  cache: string;
  monitoring: string;
  authentication: string;
  traffic: number;
}

export interface CategoryReview {
  category: string;
  score: number;
  confidence: number;
  severity: Severity;
  vote: BoardVote;
  summary: string;
  issues: string[];
  recommendations: string[];
  estimated_impact: string;
  engineering_reasoning: string;
}

export interface ReviewerVote {
  reviewer: string;
  score: number;
  vote: BoardVote;
}

export interface ArchitectureReviewResponse {
  overall_score: number;
  overall_status: string;
  overall_summary: string;
  final_decision: BoardVote;
  board_summary: string;
  reviewer_votes: ReviewerVote[];
  strengths: string[];
  critical_risks: string[];
  quick_wins: string[];
  categories: CategoryReview[];
}

export type ArchitectureReviewFormValues = {
  application_name: string;
  frontend: string;
  backend: string;
  llm: string;
  vector_db: string;
  embeddings: string;
  cache: string;
  monitoring: string;
  authentication: string;
  traffic: string;
};

export type ReviewerBoardStatus = "queued" | "reviewing" | "complete";
