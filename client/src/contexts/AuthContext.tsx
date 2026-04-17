'use client'

import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import type { AuthResult, User } from '@/types'

type LocalUserSeed = Partial<User> & {
  username?: string
  name?: string
  email?: string
  user_id?: string
  sub?: string
  nickname?: string
  role?: string
  affiliation?: string
}

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<AuthResult>
  register: (username: string, email: string, password: string) => Promise<AuthResult>
  logout: () => Promise<void>
  verifySession: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)
const LOCAL_AUTH_KEY = 'collections-transformer-local-user'

const normalizeLocalUser = (data: LocalUserSeed = {}): User => {
  const username = data?.username || data?.name || 'local-user'
  const email = data?.email || `${username}@local`
  const userId = data?.user_id || data?.sub || username

  return {
    sub: userId,
    user_id: userId,
    username,
    email,
    name: data?.name || username,
    nickname: data?.nickname || username,
    role: data?.role || 'local-user',
    affiliation: data?.affiliation || 'local'
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Restore local session from browser storage.
    verifySession()
  }, [])

  const verifySession = async () => {
    try {
      setIsLoading(true)
      const raw = typeof window !== 'undefined' ? window.localStorage.getItem(LOCAL_AUTH_KEY) : null
      if (raw) {
        const parsed = JSON.parse(raw)
        setUser(normalizeLocalUser(parsed))
        setError(null)
      } else {
        setUser(null)
      }
    } catch (err) {
      console.error('Local session verification error:', err)
      setUser(null)
      setError(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username: string, password: string): Promise<AuthResult> => {
    try {
      setIsLoading(true)
      setError(null)
      const trimmedUsername = (username || '').trim()
      const trimmedPassword = (password || '').trim()

      if (!trimmedUsername || !trimmedPassword) {
        const loginError = 'Please enter both username and password'
        setError(loginError)
        return { success: false, error: loginError }
      }

      const nextUser = normalizeLocalUser({ username: trimmedUsername })
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(LOCAL_AUTH_KEY, JSON.stringify(nextUser))
      }

      setUser(nextUser)
      return { success: true }
    } catch (err) {
      const errorMsg = 'Failed to create local session'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (username: string, email: string, password: string): Promise<AuthResult> => {
    try {
      setIsLoading(true)
      setError(null)
      const trimmedUsername = (username || '').trim()
      const trimmedEmail = (email || '').trim()
      const trimmedPassword = (password || '').trim()

      if (!trimmedUsername || !trimmedEmail || !trimmedPassword) {
        const registerError = 'Please complete username, email, and password'
        setError(registerError)
        return { success: false, error: registerError }
      }

      const nextUser = normalizeLocalUser({ username: trimmedUsername, email: trimmedEmail })
      if (typeof window !== 'undefined') {
        window.localStorage.setItem(LOCAL_AUTH_KEY, JSON.stringify(nextUser))
      }

      setUser(nextUser)
      return { success: true }
    } catch (err) {
      const errorMsg = 'Failed to create local account'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async (): Promise<void> => {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem(LOCAL_AUTH_KEY)
    }

    setUser(null)
    setError(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, error, login, register, logout, verifySession }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
