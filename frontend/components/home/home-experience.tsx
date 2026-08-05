"use client";

import { useCallback, useState } from "react";

import { ExampleArchitecturesSection } from "@/components/examples/example-architectures-section";
import { ArchitectureReviewWorkspace } from "@/components/review/architecture-review-workspace";
import type { ExampleArchitecture } from "@/lib/exampleArchitectures";

export function HomeExperience() {
  const [pendingExample, setPendingExample] =
    useState<ExampleArchitecture | null>(null);
  const [exampleLoadToken, setExampleLoadToken] = useState(0);
  const [isBoardBusy, setIsBoardBusy] = useState(false);

  const handleAnalyze = useCallback((example: ExampleArchitecture) => {
    setPendingExample(example);
    setExampleLoadToken((token) => token + 1);
  }, []);

  return (
    <>
      <ExampleArchitecturesSection
        onAnalyze={handleAnalyze}
        disabled={isBoardBusy}
      />

      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 flex-col px-6 py-10 sm:py-14">
        <header className="mb-8 max-w-2xl">
          <p className="text-sm font-medium tracking-wide text-muted-foreground">
            AI Design Review Board
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            AI Engineering Lab
          </h1>
          <p className="mt-3 text-base text-muted-foreground">
            Convene a deterministic multi-reviewer board, collect votes, then
            reveal a structured engineering report — still without LLMs.
          </p>
        </header>

        <ArchitectureReviewWorkspace
          pendingExample={pendingExample}
          exampleLoadToken={exampleLoadToken}
          onBusyChange={setIsBoardBusy}
        />
      </div>
    </>
  );
}
