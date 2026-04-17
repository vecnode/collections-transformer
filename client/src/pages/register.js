'use client'

import Head from 'next/head'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/_contexts/AuthContext'

const Register = () => {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const { register, user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (user) {
      router.push('/')
    }
  }, [user, router])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    
    if (!username || !email || !password) {
      setError('Please fill in all fields')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    const result = await register(username, email, password)
    if (result.success) {
      router.push('/')
    } else {
      setError(result.error || 'Registration failed')
    }
  }

  if (user) {
    return null
  }

  return (
    <>
      <Head>
        <title>Register - Collections Transformer</title>
      </Head>
      <main style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', padding: '20px' }}>
        <div style={{ width: '100%', maxWidth: '400px' }}>
          <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>Collections Transformer</h1>
          <h2 style={{ textAlign: 'center', marginBottom: '20px' }}>Register</h2>
          
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label htmlFor="username" style={{ display: 'block', marginBottom: '5px' }}>Username:</label>
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
              <label htmlFor="email" style={{ display: 'block', marginBottom: '5px' }}>Email:</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                minLength={6}
                style={{ width: '100%', padding: '8px', fontSize: '1rem', boxSizing: 'border-box' }}
                disabled={isLoading}
              />
            </div>
            
            <div>
              <label htmlFor="confirmPassword" style={{ display: 'block', marginBottom: '5px' }}>Confirm Password:</label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={6}
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
              {isLoading ? 'Registering...' : 'Register'}
            </button>
          </form>
          
          <div style={{ marginTop: '20px', textAlign: 'center' }}>
            <p>Already have an account? <a href="/login">Login here</a></p>
          </div>
        </div>
      </main>
    </>
  )
}

export default Register
