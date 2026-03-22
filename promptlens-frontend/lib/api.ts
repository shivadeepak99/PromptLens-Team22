const BASE_URL = "https://promptlens-backend.onrender.com";

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${BASE_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch {
    throw new Error(
      "Failed to reach the backend. Confirm the backend is reachable at https://promptlens-backend.onrender.com/.",
    );
  }

  if (!response.ok) {
    let errorMessage = `Request failed with status ${response.status}`;

    try {
      const errorBody = (await response.json()) as { detail?: string; message?: string };
      errorMessage = errorBody.detail ?? errorBody.message ?? errorMessage;
    } catch {
      // Keep the fallback message if the response body is not JSON.
    }

    throw new Error(errorMessage);
  }

  return (await response.json()) as T;
}

export async function getModelPerformance<T = unknown>(): Promise<T> {
  return apiRequest<T>("/analytics/model-performance");
}

export async function getLanguagePerformance<T = unknown>(): Promise<T> {
  return apiRequest<T>("/analytics/language-performance");
}

export async function getPromptFeatures<T = unknown>(): Promise<T> {
  return apiRequest<T>("/analytics/prompt-features");
}

export async function getTopPrompts<T = unknown>(): Promise<T> {
  return apiRequest<T>("/analytics/top-prompts");
}

export async function getTimeline<T = unknown>(): Promise<T> {
  return apiRequest<T>("/analytics/model-performance-timeline");
}

export async function getClusters<T = unknown>(): Promise<T> {
  return apiRequest<T>("/analytics/clusters");
}

export async function sendChatMessage<T = unknown>(query: string): Promise<T> {
  return apiRequest<T>("/insights/chat", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
}

export async function analyzePrompt<T = unknown>(prompt_text: string): Promise<T> {
  return apiRequest<T>("/insights/recommend", {
    method: "POST",
    body: JSON.stringify({ prompt_text }),
  });
}
