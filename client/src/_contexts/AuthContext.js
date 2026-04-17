'use client'

import { createContext, useContext, useState, useEffect } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    // Check if user is already logged in
    verifySession()
  }, [])

  const verifySession = async () => {
    try {
      setIsLoading(true)
      const response = await fetch(`${process.env.NEXT_PUBLIC_SERVER_URL || ''}/backend/auth/verify`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      })
      
      const data = await response.json()
      if (data.authenticated && data.data) {
        setUser({
          sub: data.data.user_id,
          user_id: data.data.user_id,
          username: data.data.username,
          email: data.data.email,
          name: data.data.username,
          nickname: data.data.username,
          role: data.data.role,
          affiliation: data.data.affiliation
        })
        setError(null)
      } else {
        setUser(null)
      }
    } catch (err) {
      console.error('Session verification error:', err)
      setUser(null)
      setError(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await fetch(`${process.env.NEXT_PUBLIC_SERVER_URL || ''}/backend/auth/login`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      
      const data = await response.json()
      if (data.status === '200' && data.data) {
        setUser({
          sub: data.data.user_id,
          user_id: data.data.user_id,
          username: data.data.username,
          email: data.data.email,
          name: data.data.username,
          nickname: data.data.username
        })
        return { success: true }
      } else {
        setError(data.error || 'Login failed')
        return { success: false, error: data.error || 'Login failed' }
      }
    } catch (err) {
      const errorMsg = 'Failed to connect to server'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (username, email, password) => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await fetch(`${process.env.NEXT_PUBLIC_SERVER_URL || ''}/backend/auth/register`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      })
      
      const data = await response.json()
      if (data.status === '200' && data.data) {
        setUser({
          sub: data.data.user_id,
          user_id: data.data.user_id,
          username: data.data.username,
          email: data.data.email,
          name: data.data.username,
          nickname: data.data.username
        })
        return { success: true }
      } else {
        setError(data.error || 'Registration failed')
        return { success: false, error: data.error || 'Registration failed' }
      }
    } catch (err) {
      const errorMsg = 'Failed to connect to server'
      setError(errorMsg)
      return { success: false, error: errorMsg }
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await fetch(`${process.env.NEXT_PUBLIC_SERVER_URL || ''}/backend/auth/logout`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      })
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      setUser(null)
      setError(null)
    }
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
