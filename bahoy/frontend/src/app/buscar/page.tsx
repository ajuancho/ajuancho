import { Suspense } from 'react'
import BuscarClient from './BuscarClient'

interface PageProps {
  params?: Record<string, string>
  searchParams?: Record<string, string | string[] | undefined>
}

export default function BuscarPage(_props: PageProps) {
  return (
    <Suspense>
      <BuscarClient />
    </Suspense>
  )
}
