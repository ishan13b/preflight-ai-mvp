"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  FORM_SECTION_ID,
} from "@/lib/load-example-architecture";
import {
  DEFAULT_REVIEW_FORM_VALUES,
  REVIEW_FORM_FIELDS,
} from "@/lib/review-form";
import { cn } from "@/lib/utils";
import type { ArchitectureReviewFormValues } from "@/types/review";

type ArchitectureReviewFormProps = {
  values: ArchitectureReviewFormValues;
  isSubmitting: boolean;
  isHighlighted?: boolean;
  loadedExampleName?: string | null;
  onChange: (field: keyof ArchitectureReviewFormValues, value: string) => void;
  onSubmit: () => void;
  onReset?: () => void;
};

export function ArchitectureReviewForm({
  values,
  isSubmitting,
  isHighlighted = false,
  loadedExampleName = null,
  onChange,
  onSubmit,
  onReset,
}: ArchitectureReviewFormProps) {
  return (
    <div id={FORM_SECTION_ID} className="scroll-mt-8">
      <Card
        className={cn(
          "h-full transition-[box-shadow,background-color] duration-500",
          isHighlighted &&
            "bg-muted/45 ring-2 ring-foreground/25 ring-offset-2 ring-offset-background",
        )}
      >
        <CardHeader className="border-b">
          <CardTitle>Architecture Input</CardTitle>
          <CardDescription>
            {loadedExampleName
              ? `Loaded example: ${loadedExampleName}. Review the stack, then convene the board.`
              : "Describe your AI system stack. Review logic is deterministic and rule-based."}
          </CardDescription>
        </CardHeader>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            onSubmit();
          }}
        >
          <CardContent className="grid gap-4 pt-4">
            {REVIEW_FORM_FIELDS.map((field) => (
              <div key={field.name} className="grid gap-2">
                <Label htmlFor={field.name}>{field.label}</Label>
                <Input
                  id={field.name}
                  name={field.name}
                  type={field.type === "number" ? "number" : "text"}
                  inputMode={field.type === "number" ? "numeric" : undefined}
                  min={field.type === "number" ? 0 : undefined}
                  step={field.type === "number" ? 1 : undefined}
                  value={values[field.name]}
                  disabled={isSubmitting}
                  onChange={(event) => onChange(field.name, event.target.value)}
                  placeholder={DEFAULT_REVIEW_FORM_VALUES[field.name]}
                  required
                />
              </div>
            ))}
          </CardContent>
          <CardFooter className="gap-2">
            <Button type="submit" disabled={isSubmitting} className="px-4">
              {isSubmitting ? "Convening Board…" : "Convene Review Board"}
            </Button>
            {onReset ? (
              <Button
                type="button"
                variant="outline"
                disabled={isSubmitting}
                onClick={onReset}
                className="px-4"
              >
                Reset
              </Button>
            ) : null}
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
