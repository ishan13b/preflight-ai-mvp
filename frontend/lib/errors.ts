/**
 * Typed API error with optional validation detail from FastAPI.
 */

export class ApiError extends Error {
  readonly status: number;
  readonly details: string[];

  constructor(message: string, status: number, details: string[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

export async function parseApiError(response: Response): Promise<ApiError> {
  let message = `Request failed with status ${response.status}`;
  const details: string[] = [];

  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object") {
      const record = body as Record<string, unknown>;

      if (typeof record.detail === "string") {
        message = record.detail;
      } else if (Array.isArray(record.detail)) {
        for (const item of record.detail) {
          if (item && typeof item === "object") {
            const issue = item as { loc?: unknown[]; msg?: string };
            const path = Array.isArray(issue.loc)
              ? issue.loc.filter((part) => part !== "body").join(".")
              : "";
            const text = issue.msg ?? "Invalid value";
            details.push(path ? `${path}: ${text}` : text);
          }
        }
        if (details.length > 0) {
          message = "Validation failed. Please check the form fields.";
        }
      }
    }
  } catch {
    // Response body was not JSON; keep the default message.
  }

  return new ApiError(message, response.status, details);
}
