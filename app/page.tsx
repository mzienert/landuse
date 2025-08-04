import Link from 'next/link';

export default function Page() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            La Plata County Search
          </h1>
          <p className="text-xl text-gray-600 mb-8 leading-relaxed">
            Semantic search across Land Use Code regulations and Property Assessor data
          </p>
          
          <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
            <div className="grid md:grid-cols-2 gap-8">
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  🏛️ Land Use Code
                </h3>
                <p className="text-gray-600 mb-4">
                  Search through 1,298 sections of La Plata County Land Use regulations
                </p>
                <ul className="text-sm text-gray-500 space-y-1">
                  <li>• Building permits & zoning</li>
                  <li>• Subdivision regulations</li>
                  <li>• Environmental requirements</li>
                </ul>
              </div>
              
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  🏠 Property Assessor Data
                </h3>
                <p className="text-gray-600 mb-4">
                  Search through 46,230 property records with detailed information
                </p>
                <ul className="text-sm text-gray-500 space-y-1">
                  <li>• Property ownership & values</li>
                  <li>• Building details & history</li>
                  <li>• Legal descriptions & parcels</li>
                </ul>
              </div>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/search"
              className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
            >
              Start Searching
            </Link>
            <a
              href="http://localhost:8000"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-gray-100 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
            >
              API Documentation
            </a>
          </div>
          
          <div className="mt-12 text-sm text-gray-500">
            <p>Powered by semantic search with sentence transformers and ChromaDB</p>
          </div>
        </div>
      </div>
    </div>
  );
}
