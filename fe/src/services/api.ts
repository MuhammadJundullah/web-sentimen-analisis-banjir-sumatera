export interface SentimentResult {
  label: string;
  score: number;
}

export interface CategoryResult {
  label: string;
  score: number;
}

export interface PredictionResponse {
  text: string;
  sentiment: SentimentResult;
  categories: CategoryResult[];
  all_predictions?: any;
}

export interface CsvUploadResponse {
  total: number;
  skipped: number;
  sentiment_percentages: Record<string, number>;
  category_percentages: Record<string, number>;
}

export interface FetchTweetsResponse {
  total: number;
  inserted: number;
  query: string;
  fetched_at: string;
}

export interface FetchStatusResponse {
  last_run: string | null;
  last_error: string | null;
  last_count: number;
  last_inserted: number;
}

export interface AnalysisRequest {
  text: string;
}

export class DisasterAPI {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setBaseUrl(url: string) {
    this.baseUrl = url;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.ok) {
      return response.json();
    }

    try {
      const data = await response.json();
      if (data?.detail) {
        throw new Error(data.detail);
      }
    } catch (_err) {
      // ignore parsing error and fall back to status text
    }

    throw new Error(`API Error: ${response.statusText}`);
  }

  async predict(text: string): Promise<PredictionResponse> {
    const response = await fetch(`${this.baseUrl}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    });

    return this.handleResponse<PredictionResponse>(response);
  }

  async uploadCsv(file: File): Promise<CsvUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/upload-csv`, {
      method: 'POST',
      body: formData,
    });

    return this.handleResponse<CsvUploadResponse>(response);
  }

  async fetchTweets(query?: string): Promise<FetchTweetsResponse> {
    const response = await fetch(`${this.baseUrl}/fetch-tweets`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query ? { query } : {}),
    });

    return this.handleResponse<FetchTweetsResponse>(response);
  }

  async fetchStatus(): Promise<FetchStatusResponse> {
    const response = await fetch(`${this.baseUrl}/fetch-status`, {
      method: 'GET',
    });

    return this.handleResponse<FetchStatusResponse>(response);
  }

  async setToken(token: string): Promise<{ status: string }> {
    const response = await fetch(`${this.baseUrl}/set-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token }),
    });

    return this.handleResponse<{ status: string }>(response);
  }
}

export const apiClient = new DisasterAPI('');
