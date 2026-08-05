/**
 * Form population helpers for example architectures.
 *
 * Keeps loading / reset / highlight orchestration out of presentational UI.
 */

import type { ExampleArchitecture } from "@/lib/exampleArchitectures";
import type { ArchitectureReviewFormValues } from "@/types/review";

export const FORM_SECTION_ID = "architecture-review-form";

export const EXAMPLE_HIGHLIGHT_DURATION_MS = 1800;

/** Clone example form values so React state cannot mutate catalog data. */
export function toFormValuesFromExample(
  example: ExampleArchitecture,
): ArchitectureReviewFormValues {
  return { ...example.formValues };
}

export function scrollToArchitectureForm(): void {
  const target = document.getElementById(FORM_SECTION_ID);
  if (!target) {
    return;
  }

  target.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}
