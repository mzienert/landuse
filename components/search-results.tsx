'use client';

import React from 'react';
import { SearchResult } from '../lib/search-service';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  isLoading?: boolean;
  error?: string;
}

export function SearchResults({ results, query, isLoading = false, error }: SearchResultsProps) {
  if (isLoading) {
    return (
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="border-b pb-4">
                <div className="h-4 bg-gray-200 rounded w-1/6 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-full mb-1"></div>
                <div className="h-3 bg-gray-200 rounded w-3/4"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="text-red-600 bg-red-50 border border-red-200 rounded-md p-4">
          <h3 className="font-medium mb-2">Search Error</h3>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!results.length && query) {
    return (
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="text-gray-500 text-center py-8">
          <p className="text-lg mb-2">No results found</p>
          <p className="text-sm">Try a different search query or check if the API is running.</p>
        </div>
      </div>
    );
  }

  if (!query) {
    return null;
  }

  return (
    <div className="bg-white shadow-md rounded-lg p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Search Results for "{query}"
        </h2>
        <p className="text-sm text-gray-600">{results.length} result(s) found</p>
      </div>
      
      <div className="space-y-4">
        {results.map((result, index) => (
          <div key={index} className="border-b border-gray-200 pb-4 last:border-b-0">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-medium text-blue-600">
                Section {result.section}
              </h3>
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                Relevance: {parseFloat(result.relevance).toFixed(3)}
              </span>
            </div>
            <div className="text-gray-700 text-sm leading-relaxed">
              {result.text.length > 500 ? (
                <>
                  {result.text.substring(0, 500)}
                  <span className="text-gray-500">... </span>
                  <button className="text-blue-600 hover:text-blue-800 text-xs">
                    Read more
                  </button>
                </>
              ) : (
                result.text
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}