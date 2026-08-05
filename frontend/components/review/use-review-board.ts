"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import {
  BOARD_REVIEWERS,
  BOARD_SUMMARY_DELAY_MS,
  REVIEWER_STEP_MS,
} from "@/lib/board";
import type {
  ArchitectureReviewResponse,
  ReviewerBoardStatus,
} from "@/types/review";
import type { BoardMemberState } from "@/components/review/review-board";

type BoardPhase = "idle" | "reviewing" | "awaiting_result" | "complete" | "error";

type UseReviewBoardOptions = {
  sessionId: number;
  review: ArchitectureReviewResponse | null;
  errorMessage: string | null;
};

type UseReviewBoardResult = {
  phase: BoardPhase;
  members: BoardMemberState[];
  showBoardSummary: boolean;
  showDetailedReport: boolean;
  isBoardActive: boolean;
};

function buildMembers(
  statuses: ReviewerBoardStatus[],
  review: ArchitectureReviewResponse | null,
): BoardMemberState[] {
  return BOARD_REVIEWERS.map((name, index) => {
    const status = statuses[index] ?? "queued";
    const vote =
      status === "complete"
        ? review?.reviewer_votes.find((item) => item.reviewer === name)
        : undefined;

    return {
      name,
      status,
      vote: vote?.vote,
      score: vote?.score,
    };
  });
}

export function useReviewBoard({
  sessionId,
  review,
  errorMessage,
}: UseReviewBoardOptions): UseReviewBoardResult {
  const [phase, setPhase] = useState<BoardPhase>("idle");
  const [statuses, setStatuses] = useState<ReviewerBoardStatus[]>(
    BOARD_REVIEWERS.map(() => "queued"),
  );
  const [animationDone, setAnimationDone] = useState(false);
  const [showDetailedReport, setShowDetailedReport] = useState(false);
  const timersRef = useRef<number[]>([]);

  const clearTimers = () => {
    for (const timer of timersRef.current) {
      window.clearTimeout(timer);
    }
    timersRef.current = [];
  };

  useEffect(() => {
    if (sessionId === 0) {
      clearTimers();
      setPhase(errorMessage ? "error" : "idle");
      setStatuses(BOARD_REVIEWERS.map(() => "queued"));
      setAnimationDone(false);
      setShowDetailedReport(false);
      return;
    }

    clearTimers();
    setPhase("reviewing");
    setStatuses(BOARD_REVIEWERS.map(() => "queued"));
    setAnimationDone(false);
    setShowDetailedReport(false);

    BOARD_REVIEWERS.forEach((_, index) => {
      const reviewingAt = index * REVIEWER_STEP_MS;
      const completeAt = reviewingAt + REVIEWER_STEP_MS;

      timersRef.current.push(
        window.setTimeout(() => {
          setStatuses((current) =>
            current.map((status, memberIndex) => {
              if (memberIndex < index) return "complete";
              if (memberIndex === index) return "reviewing";
              return "queued";
            }),
          );
        }, reviewingAt),
      );

      timersRef.current.push(
        window.setTimeout(() => {
          setStatuses((current) =>
            current.map((status, memberIndex) =>
              memberIndex <= index ? "complete" : status,
            ),
          );
        }, completeAt),
      );
    });

    const doneAt =
      BOARD_REVIEWERS.length * REVIEWER_STEP_MS + BOARD_SUMMARY_DELAY_MS;

    timersRef.current.push(
      window.setTimeout(() => {
        setAnimationDone(true);
        setStatuses(BOARD_REVIEWERS.map(() => "complete"));
      }, doneAt),
    );

    return clearTimers;
  }, [sessionId]);

  useEffect(() => {
    if (errorMessage && sessionId > 0) {
      clearTimers();
      setPhase("error");
      setAnimationDone(false);
      setShowDetailedReport(false);
    }
  }, [errorMessage, sessionId]);

  useEffect(() => {
    if (!animationDone || errorMessage) {
      return;
    }

    if (!review) {
      setPhase("awaiting_result");
      return;
    }

    setPhase("complete");
    const revealTimer = window.setTimeout(() => {
      setShowDetailedReport(true);
    }, 350);
    timersRef.current.push(revealTimer);

    return () => {
      window.clearTimeout(revealTimer);
    };
  }, [animationDone, review, errorMessage]);

  const members = useMemo(
    () => buildMembers(statuses, review),
    [statuses, review],
  );

  const showBoardSummary = phase === "complete" && Boolean(review);
  const isBoardActive =
    sessionId > 0 &&
    (phase === "reviewing" ||
      phase === "awaiting_result" ||
      phase === "complete");

  return {
    phase,
    members,
    showBoardSummary,
    showDetailedReport,
    isBoardActive,
  };
}
