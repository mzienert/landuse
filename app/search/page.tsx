'use client';

import React, { useState } from 'react';
import { SearchForm } from '../../components/search-form';
import { SearchResults } from '../../components/search-results';
import { SearchService, SearchResponse } from '../../lib/search-service';

export default function SearchPage() {
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (query: string, numResults: number, collection: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const results = await SearchService.search(query, numResults, collection);
      setSearchResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setSearchResults(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              La Plata County Search
            </h1>
            <p className="text-gray-600">
              Search across Land Use Code regulations and Property Assessor data
            </p>
          </div>
          
          <SearchForm 
            onSearch={handleSearch} 
            isLoading={isLoading} 
          />
          
          <SearchResults 
            results={searchResults?.results || []} 
            query={searchResults?.query || ''} 
            isLoading={isLoading}
            error={error}
            collectionName={searchResults?.collection_name}
          />
        </div>
      </div>
    </div>
  );
}