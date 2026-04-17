'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

export function withAuth(Component) {
  return function AuthenticatedComponent(props) {
    const { user, isLoading } = useAuth()
    const router = useRouter()

    useEffect(() => {
      if (!isLoading && !user) {
        router.push('/login')
      }
    }, [user, isLoading, router])

    if (isLoading) {
      return <div>Loading...</div>
    }

    if (!user) {
      return null
    }

    return <Component {...props} />
  }
}
