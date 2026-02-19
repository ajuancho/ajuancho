import { cn } from '@/lib/utils'

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-[3px]',
  }

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-primary-200 border-t-primary-500',
        sizeClasses[size],
        className,
      )}
    />
  )
}

interface LoadingProps {
  text?: string
  fullPage?: boolean
}

export default function Loading({ text = 'Cargando...', fullPage = false }: LoadingProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center gap-3',
        fullPage && 'min-h-screen',
        !fullPage && 'py-16',
      )}
    >
      <Spinner size="lg" />
      {text && (
        <p className="text-gray-500 font-sans text-sm">{text}</p>
      )}
    </div>
  )
}

export function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl shadow-card overflow-hidden animate-pulse">
      <div className="h-48 bg-gray-200" />
      <div className="p-5 space-y-3">
        <div className="h-4 bg-gray-200 rounded w-1/3" />
        <div className="h-5 bg-gray-200 rounded w-4/5" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
        <div className="flex justify-between items-center pt-2">
          <div className="h-5 bg-gray-200 rounded w-1/4" />
          <div className="h-8 bg-gray-200 rounded w-1/4" />
        </div>
      </div>
    </div>
  )
}
