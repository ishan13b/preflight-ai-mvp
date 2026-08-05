/**
 * API client configuration.
 *
 * Keep backend base URL and fetch defaults in one place so services
 * stay consistent as new modules are added.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
