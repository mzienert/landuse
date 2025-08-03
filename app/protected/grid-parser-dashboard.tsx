'use client';
import React, { useState } from 'react';
import { SearchForm } from '../../components/search-form';
import { SearchResults } from '../../components/search-results';
import { SearchService, SearchResult } from '../../lib/search-service';

interface LandUseCodeDashboardProps {
  userId: string;
}

export function LandUseCodeDashboard({ userId }: LandUseCodeDashboardProps) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (searchQuery: string, numResults: number) => {
    setIsLoading(true);
    setError(null);
    setQuery(searchQuery);
    
    try {
      const response = await SearchService.searchLandUseCode(searchQuery, numResults);
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred during search');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          La Plata County Land Use Code Search
        </h2>
        <p className="text-gray-600">
          Search through county regulations using natural language queries. 
          Try searches like "building permits", "zoning requirements", or "subdivision regulations".
        </p>
      </div>
      
      <SearchForm onSearch={handleSearch} isLoading={isLoading} />
      
      <SearchResults 
        results={results} 
        query={query} 
        isLoading={isLoading} 
        error={error} 
      />
    </div>
  );
}