'use client';

import React, { useState } from 'react';

interface SearchFormProps {
  onSearch: (query: string, numResults: number, collection: string) => void;
  isLoading?: boolean;
}

export function SearchForm({ onSearch, isLoading = false }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [numResults, setNumResults] = useState(5);
  const [collection, setCollection] = useState('la_plata_county_code');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), numResults, collection);
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
          placeholder={
            collection === 'la_plata_county_code' 
              ? "Enter your search query (e.g., 'building permits', 'zoning requirements')"
              : "Enter your search query (e.g., 'Smith family property', 'commercial buildings')"
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label htmlFor="collection" className="block text-sm font-medium text-gray-700 mb-2">
            Search Collection
          </label>
          <select
            id="collection"
            value={collection}
            onChange={(e) => setCollection(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
          >
            <option value="la_plata_county_code">Land Use Code</option>
            <option value="la_plata_assessor">Property Assessor Data</option>
          </select>
        </div>
        
        <div>
          <label htmlFor="numResults" className="block text-sm font-medium text-gray-700 mb-2">
            Number of Results
          </label>
          <select
            id="numResults"
            value={numResults}
            onChange={(e) => setNumResults(parseInt(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
          >
            <option value={3}>3 results</option>
            <option value={5}>5 results</option>
            <option value={10}>10 results</option>
            <option value={15}>15 results</option>
          </select>
        </div>
      </div>
      
      <button
        type="submit"
        disabled={!query.trim() || isLoading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Searching...' : `Search ${collection === 'la_plata_county_code' ? 'Land Use Code' : 'Property Data'}`}
      </button>
    </form>
  );
}