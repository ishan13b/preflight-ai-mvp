"use client";

import { ExampleArchitectureCard } from "@/components/examples/example-architecture-card";
import { EXAMPLE_ARCHITECTURES } from "@/lib/exampleArchitectures";
import type { ExampleArchitecture } from "@/lib/exampleArchitectures";

type ExampleArchitecturesSectionProps = {
  onAnalyze: (example: ExampleArchitecture) => void;
  disabled?: boolean;
};

export function ExampleArchitecturesSection({
  onAnalyze,
  disabled = false,
}: ExampleArchitecturesSectionProps) {
  return (
    <section
      aria-labelledby="example-architectures-heading"
      className="border-b border-border/70 bg-background/70"
    >
      <div className="mx-auto w-full max-w-7xl px-6 py-10 sm:py-12">
        <div className="max-w-3xl">
          <h2
            id="example-architectures-heading"
            className="text-2xl font-semibold tracking-tight text-foreground sm:text-3xl"
          >
            Example Architectures
          </h2>
          <p className="mt-3 text-base leading-relaxed text-muted-foreground">
            Explore production-inspired AI system designs and see how the Design
            Review Board evaluates them.
          </p>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
          {EXAMPLE_ARCHITECTURES.map((example) => (
            <ExampleArchitectureCard
              key={example.id}
              example={example}
              onAnalyze={onAnalyze}
              disabled={disabled}
            />
          ))}
        </div>
      </div>
    </section>
  );
}
