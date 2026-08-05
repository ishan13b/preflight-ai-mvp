/**
 * Design Review Board constants and presentation helpers.
 */

import type { BoardVote } from "@/types/review";

export const BOARD_REVIEWERS = [
  "Scalability",
  "Observability",
  "Security",
  "Cost",
  "Reliability",
] as const;

export type BoardReviewerName = (typeof BOARD_REVIEWERS)[number];

/** Per-reviewer dwell time while status is "Reviewing...". */
export const REVIEWER_STEP_MS = 750;

/** Short pause after the last reviewer completes before the board summary. */
export const BOARD_SUMMARY_DELAY_MS = 450;

export function formatBoardVote(vote: BoardVote): string {
  return vote;
}

export function boardVoteTone(vote: BoardVote): "positive" | "warning" | "negative" {
  switch (vote) {
    case "APPROVED":
      return "positive";
    case "APPROVED WITH CONCERNS":
      return "warning";
    case "REQUIRES CHANGES":
      return "negative";
  }
}
