import { Suspense } from 'react'
import ExplorarClient from './ExplorarClient'

interface PageProps {
  params?: Record<string, string>
  searchParams?: Record<string, string | string[] | undefined>
}

export default function ExplorarPage(_props: PageProps) {
  return (
    <Suspense>
      <ExplorarClient />
    </Suspense>
  )
}
