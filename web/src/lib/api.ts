/**
 * API client for Personal Finance Analyst backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

/**
 * Check if the API server is healthy
 * @returns Promise resolving to health status object
 * @throws Error if request fails
 */
export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/health`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Health check failed: ${response.status} ${response.statusText} - ${errorText}`);
  }

  return response.json();
}

/**
 * Ingest a CSV file to the backend
 * @param file - CSV file to upload
 * @returns Promise resolving to ingest response
 * @throws Error if request fails
 */
export async function ingestCsv(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/ingest?replace=true`, {
    method: "POST",
    body: formData,
    // Don't set Content-Type header - browser will set it with boundary for multipart/form-data
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`CSV ingestion failed: ${response.status} ${response.statusText} - ${errorText}`);
  }

  return response.json();
}

/**
 * Query the finance assistant
 * @param payload - Query request payload
 * @param payload.question - The question to ask
 * @param payload.month - Optional month in YYYY-MM format
 * @param payload.limit_evidence - Optional limit for evidence rows (default: 20)
 * @returns Promise resolving to query response
 * @throws Error if request fails
 */
export async function queryFinance(payload: {
  question: string;
  month?: string;
  limit_evidence?: number;
}): Promise<any> {
  const response = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "Unknown error");
    throw new Error(`Query failed: ${response.status} ${response.statusText} - ${errorText}`);
  }

  return response.json();
}
