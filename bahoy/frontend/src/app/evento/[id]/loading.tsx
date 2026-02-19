// Skeleton shown by Next.js App Router while the server fetches event data.
export default function Loading() {
  return (
    <div className="container-custom py-8 animate-pulse">
      {/* Breadcrumb skeleton */}
      <div className="mb-6 flex items-center gap-2">
        <div className="h-4 w-12 bg-gray-200 rounded" />
        <div className="h-4 w-3 bg-gray-100 rounded" />
        <div className="h-4 w-20 bg-gray-200 rounded" />
        <div className="h-4 w-3 bg-gray-100 rounded" />
        <div className="h-4 w-44 bg-gray-200 rounded" />
      </div>

      <div className="max-w-5xl mx-auto">
        {/* Hero image */}
        <div className="h-72 sm:h-96 md:h-[28rem] bg-gray-200 rounded-2xl mb-8" />

        {/* Title & meta */}
        <div className="mb-8 space-y-4">
          <div className="h-10 bg-gray-200 rounded-lg w-3/4" />
          <div className="flex gap-5 flex-wrap">
            <div className="h-5 w-24 bg-gray-100 rounded-full" />
            <div className="h-5 w-36 bg-gray-100 rounded-full" />
            <div className="h-5 w-40 bg-gray-100 rounded-full" />
          </div>
          <div className="flex gap-3">
            <div className="h-9 w-28 bg-gray-100 rounded-lg" />
            <div className="h-9 w-28 bg-gray-100 rounded-lg" />
          </div>
        </div>

        {/* Content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left column */}
          <div className="lg:col-span-2 space-y-3">
            <div className="h-6 bg-gray-200 rounded w-1/4 mb-4" />
            <div className="h-4 bg-gray-100 rounded w-full" />
            <div className="h-4 bg-gray-100 rounded w-full" />
            <div className="h-4 bg-gray-100 rounded w-5/6" />
            <div className="h-4 bg-gray-100 rounded w-4/5" />
            <div className="h-4 bg-gray-100 rounded w-full" />
            <div className="h-4 bg-gray-100 rounded w-3/4" />
          </div>

          {/* Right column (sidebar) */}
          <div className="space-y-5">
            <div className="bg-white rounded-xl shadow-card p-5 space-y-5">
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-2" />
              <div className="space-y-2">
                <div className="h-4 bg-gray-100 rounded w-2/3" />
                <div className="h-4 bg-gray-100 rounded w-1/2" />
              </div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-100 rounded w-3/4" />
                <div className="h-4 bg-gray-100 rounded w-1/2" />
              </div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-100 rounded w-1/3" />
                <div className="h-6 bg-gray-200 rounded w-1/2" />
              </div>
              <div className="h-10 bg-gray-200 rounded-lg w-full mt-2" />
            </div>
            <div className="h-52 bg-gray-200 rounded-xl" />
          </div>
        </div>

        {/* Eventos similares */}
        <div className="border-t border-gray-100 pt-8 mt-12">
          <div className="h-8 bg-gray-200 rounded w-48 mb-6" />
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-xl overflow-hidden bg-white shadow-card">
                <div className="h-36 bg-gray-200" />
                <div className="p-4 space-y-2">
                  <div className="h-4 bg-gray-100 rounded w-full" />
                  <div className="h-4 bg-gray-100 rounded w-3/4" />
                  <div className="h-3 bg-gray-100 rounded w-1/2 mt-3" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
