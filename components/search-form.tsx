'use client';

import React, { useState } from 'react';

interface SearchFormProps {
  onSearch: (query: string, numResults: number) => void;
  isLoading?: boolean;
}

export function SearchForm({ onSearch, isLoading = false }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [numResults, setNumResults] = useState(5);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), numResults);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-6 mb-6">
      <div className="mb-4">
        <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
          Search Query
        </label>
        <input
          type="text"
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your search query (e.g., 'building permits', 'zoning requirements')"
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        />
      </div>
      
      <div className="mb-4">
        <label htmlFor="numResults" className="block text-sm font-medium text-gray-700 mb-2">
          Number of Results
        </label>
        <select
          id="numResults"
          value={numResults}
          onChange={(e) => setNumResults(parseInt(e.target.value))}
          className="px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        >
          <option value={3}>3 results</option>
          <option value={5}>5 results</option>
          <option value={10}>10 results</option>
          <option value={15}>15 results</option>
        </select>
      </div>
      
      <button
        type="submit"
        disabled={!query.trim() || isLoading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Searching...' : 'Search Land Use Code'}
      </button>
    </form>
  );
}