'use client'

import Head from 'next/head'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

const Login = () => {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login, user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user) {
      router.push('/')
    }
  }, [user, router])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    if (!username || !password) {
      setError('Please enter both username and password')
      return
    }

    const result = await login(username, password)
    if (result.success) {
      router.push('/')
    } else {
      setError(result.error || 'Login failed')
    }
  }

  if (user) {
    return null
  }

  return (
    <>
      <Head>
        <title>Login - Collections Transformer</title>
      </Head>
      <main>
        <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100%' }}>
          <div style={{ width: '45%', maxWidth: '500px', padding: '30px' }}>
            <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>Collections Transformer</h1>
            <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>Login</h2>
            <p style={{ textAlign: 'center', marginBottom: '20px', color: '#555' }}>Local session only (no cloud login)</p>
            
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              <div>
                <label htmlFor="username" style={{ display: 'block', marginBottom: '5px' }}>Username or Email:</label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  style={{ width: '100%', padding: '8px', fontSize: '1rem', boxSizing: 'border-box' }}
                  disabled={isLoading}
                />
              </div>
              
              <div>
                <label htmlFor="password" style={{ display: 'block', marginBottom: '5px' }}>Password:</label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  style={{ width: '100%', padding: '8px', fontSize: '1rem', boxSizing: 'border-box' }}
                  disabled={isLoading}
                />
              </div>
              
              {error && (
                <div style={{ color: 'red', padding: '10px', backgroundColor: '#ffe6e6', borderRadius: '4px' }}>
                  {error}
                </div>
              )}
              
              <button
                type="submit"
                disabled={isLoading}
                style={{ padding: '10px', fontSize: '1rem', cursor: isLoading ? 'not-allowed' : 'pointer' }}
              >
                {isLoading ? 'Logging in...' : 'Login'}
              </button>
            </form>
            
            <div style={{ marginTop: '20px', textAlign: 'center', color: '#666' }}>
              <p>Use any username/password to start a local session.</p>
            </div>
          </div>
        </div>
      </main>
    </>
  )
}

export default Login
