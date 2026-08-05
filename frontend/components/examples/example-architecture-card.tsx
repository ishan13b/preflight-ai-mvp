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
import type { ExampleArchitecture } from "@/lib/exampleArchitectures";

type ExampleArchitectureCardProps = {
  example: ExampleArchitecture;
  onAnalyze: (example: ExampleArchitecture) => void;
  disabled?: boolean;
};

export function ExampleArchitectureCard({
  example,
  onAnalyze,
  disabled = false,
}: ExampleArchitectureCardProps) {
  return (
    <Card className="h-full transition-transform duration-200 hover:-translate-y-0.5 hover:bg-muted/20">
      <CardHeader className="border-b">
        <CardTitle className="text-base">{example.name}</CardTitle>
        <CardDescription className="leading-relaxed">
          {example.description}
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
          Technology Stack
        </p>
        <ul className="mt-2 flex flex-wrap gap-1.5">
          {example.stack.map((item) => (
            <li
              key={item}
              className="rounded-md border border-border/80 px-2 py-0.5 text-xs text-foreground/90"
            >
              {item}
            </li>
          ))}
        </ul>
      </CardContent>
      <CardFooter>
        <Button
          type="button"
          variant="outline"
          className="w-full px-4"
          disabled={disabled}
          onClick={() => onAnalyze(example)}
        >
          Analyze Architecture
        </Button>
      </CardFooter>
    </Card>
  );
}
