export interface SearchResult {
  section?: string;
  account?: string;
  id?: string;
  text: string;
  relevance: string;
  collection: string;
}

export interface SearchResponse {
  query: string;
  collection: string;
  collection_name: string;
  results: SearchResult[];
}

export interface SearchError {
  error: string;
}

export class SearchService {
  private static readonly BASE_URL = 'http://localhost:8000';

  static async search(
    query: string, 
    numResults: number = 5,
    collection: string = 'la_plata_county_code'
  ): Promise<SearchResponse> {
    if (!query.trim()) {
      throw new Error('Query cannot be empty');
    }

    const url = new URL(`${this.BASE_URL}/search/simple`);
    url.searchParams.set('query', query.trim());
    url.searchParams.set('num_results', numResults.toString());
    url.searchParams.set('collection', collection);

    try {
      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add timeout
        signal: AbortSignal.timeout(30000), // 30 second timeout
      });

      if (!response.ok) {
        const errorData: SearchError = await response.json().catch(() => ({
          error: `HTTP ${response.status}: ${response.statusText}`
        }));
        throw new Error(errorData.error || `Search request failed: ${response.statusText}`);
      }

      const data: SearchResponse = await response.json();
      
      // Validate response structure
      if (!data.query || !Array.isArray(data.results) || !data.collection) {
        throw new Error('Invalid response format from search API');
      }

      return data;
    } catch (error) {
      if (error instanceof Error) {
        // Handle specific error types
        if (error.name === 'TimeoutError') {
          throw new Error('Search request timed out. Please try again.');
        }
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
          throw new Error('Unable to connect to search service. Please ensure the API is running.');
        }
        throw error;
      }
      throw new Error('An unexpected error occurred during search');
    }
  }

  static async checkApiHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.BASE_URL}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000), // 5 second timeout for health check
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}