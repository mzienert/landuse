'use client';

import React, { useState } from 'react';
import { SearchResult } from '../lib/search-service';
import { parseAndFormatText, formatTextForDisplay, FormattedTextSection } from '../lib/text-formatter';

interface SearchResultsProps {
  results: SearchResult[];
  query: string;
  isLoading?: boolean;
  error?: string;
}

function FormattedTextDisplay({ sections }: { sections: FormattedTextSection[] }) {
  return (
    <div className="space-y-1">
      {sections.map((section, idx) => {
        switch (section.type) {
          case 'heading':
            return (
              <div 
                key={idx} 
                className={`font-bold text-gray-900 ${
                  section.level === 1 ? 'text-base' : 'text-sm'
                } ${idx > 0 ? 'mt-4 mb-2' : 'mb-2'}`}
              >
                {section.content}
              </div>
            );
          case 'section':
            return (
              <div key={idx} className="font-semibold text-blue-700 text-sm mt-3 mb-1">
                {section.content}
              </div>
            );
          case 'metadata':
            return (
              <div key={idx} className="text-xs text-gray-500 italic mt-2">
                {section.content}
              </div>
            );
          case 'list-item':
            return (
              <div key={idx} className="text-sm text-gray-700 ml-4 my-1">
                {section.content}
              </div>
            );
          default:
            return (
              <div key={idx} className="text-sm text-gray-700 leading-relaxed mb-2">
                {section.content}
              </div>
            );
        }
      })}
    </div>
  );
}

export function SearchResults({ results, query, isLoading = false, error }: SearchResultsProps) {
  const [expandedResults, setExpandedResults] = useState<Set<number>>(new Set());

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedResults);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedResults(newExpanded);
  };
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
            <div>
              {result.text.length > 500 ? (
                <div>
                  <FormattedTextDisplay 
                    sections={parseAndFormatText(
                      expandedResults.has(index) 
                        ? result.text 
                        : formatTextForDisplay(result.text, 500)
                    )}
                  />
                  {!expandedResults.has(index) && (
                    <span className="text-gray-500 text-sm">... </span>
                  )}
                  <button 
                    onClick={() => toggleExpanded(index)}
                    className="text-blue-600 hover:text-blue-800 text-xs ml-1 inline-block mt-2"
                  >
                    {expandedResults.has(index) ? 'Show less' : 'Read more'}
                  </button>
                </div>
              ) : (
                <FormattedTextDisplay sections={parseAndFormatText(result.text)} />
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}