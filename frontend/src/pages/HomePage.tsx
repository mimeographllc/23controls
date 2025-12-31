import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const HomePage = () => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await axios.get('/api/v1/health')
      return response.data
    },
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center">
      <div className="card max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          SynthetIQ Signals CDP
        </h1>
        <p className="text-xl text-gray-600 mb-6">
          Software Licensing Marketplace Platform
        </p>
        
        <div className="bg-gray-100 rounded-lg p-4 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            API Status
          </h2>
          {isLoading && (
            <p className="text-gray-600">Checking connection...</p>
          )}
          {error && (
            <p className="text-red-600">
              ❌ API connection failed. Make sure the backend is running.
            </p>
          )}
          {data && (
            <div className="text-left">
              <p className="text-green-600 font-semibold mb-2">
                ✅ Connected to API
              </p>
              <pre className="bg-white p-3 rounded text-sm overflow-auto">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">
              🛠 Phase 1: Foundation
            </h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>✅ Docker Compose setup</li>
              <li>✅ FastAPI backend</li>
              <li>✅ React + Vite frontend</li>
              <li>✅ PostgreSQL database</li>
              <li>✅ Redis cache</li>
            </ul>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">
              📋 Next Steps
            </h3>
            <ul className="text-sm text-gray-600 space-y-1">
              <li>🔜 EAV database schema</li>
              <li>🔜 Authentication system</li>
              <li>🔜 User hierarchy</li>
              <li>🔜 Product catalog</li>
              <li>🔜 Developer portal</li>
            </ul>
          </div>
        </div>

        <div className="mt-6">
          <p className="text-sm text-gray-500">
            🚀 Ready to build! Phase 1 complete.
          </p>
        </div>
      </div>
    </div>
  )
}

export default HomePage
