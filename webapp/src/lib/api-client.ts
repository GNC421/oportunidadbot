export async function parseErrorDetail(response: Response, fallback: string): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: string };
    return body?.detail ?? fallback;
  } catch {
    return fallback;
  }
}
