import { ArchitectureReviewWorkspace } from "@/components/review/architecture-review-workspace";

export default function HomePage() {
  return (
    <main className="relative flex flex-1 flex-col">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_bottom,oklch(0.99_0.002_250),oklch(0.965_0.01_240))]"
      />

      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-1 flex-col px-6 py-10 sm:py-14">
        <header className="mb-8 max-w-2xl">
          <p className="text-sm font-medium tracking-wide text-muted-foreground">
            Architecture Critic
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            AI Engineering Lab
          </h1>
          <p className="mt-3 text-base text-muted-foreground">
            Submit an AI system architecture and receive structured, rule-based
            engineering feedback.
          </p>
        </header>

        <ArchitectureReviewWorkspace />
      </div>
    </main>
  );
}
