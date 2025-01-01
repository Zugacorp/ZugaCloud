import React, { createContext, useContext, useState, useEffect } from 'react'
import { toast } from 'react-toastify'

interface User {
  sub: string
  email: string
  email_verified: boolean
  [key: string]: any
}

interface AuthContextType {
  isAuthenticated: boolean
  user: User | null
  isLoading: boolean
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  clearAuth: () => void
}

export const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const clearAuth = () => {
    console.log('Clearing auth state...')
    localStorage.removeItem('access_token')
    localStorage.removeItem('id_token')
    localStorage.removeItem('refresh_token')
    setIsAuthenticated(false)
    setUser(null)
    setIsLoading(false)
  }

  // Check authentication status on mount and token changes
  useEffect(() => {
    const checkAuth = async () => {
      try {
        console.log('Checking auth state...')
        const accessToken = localStorage.getItem('access_token')
        console.log('Access token present:', !!accessToken)
        
        if (!accessToken) {
          console.log('No access token, clearing auth state')
          clearAuth()
          return
        }

        console.log('Validating access token...')
        const response = await fetch('/api/auth/status', {
          headers: {
            'Authorization': `Bearer ${accessToken}`
          }
        })

        const data = await response.json()
        console.log('Auth status response:', data)

        if (response.ok && data.isAuthenticated) {
          console.log('Token valid, setting auth state')
          setIsAuthenticated(true)
          if (data.user) {
            setUser(data.user)
          }
        } else {
          console.log('Token invalid, attempting refresh')
          try {
            await refreshToken()
            console.log('Token refresh successful')
          } catch (refreshError) {
            console.error('Token refresh failed:', refreshError)
            clearAuth()
            
            // Only redirect to login if we're not already there or in the callback
            const currentPath = window.location.hash.slice(1) // Remove the #
            if (!currentPath.includes('/login') && !currentPath.includes('/auth/callback')) {
              console.log('Redirecting to login...')
              window.location.href = '/#/login'
            }
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        clearAuth()
        
        // Only redirect to login if we're not already there or in the callback
        const currentPath = window.location.hash.slice(1) // Remove the #
        if (!currentPath.includes('/login') && !currentPath.includes('/auth/callback')) {
          console.log('Redirecting to login...')
          window.location.href = '/#/login'
        }
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const refreshToken = async () => {
    try {
      console.log('Starting token refresh...')
      const refresh_token = localStorage.getItem('refresh_token')
      if (!refresh_token) {
        throw new Error('No refresh token available')
      }

      const response = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const tokens = await response.json()
      console.log('Refresh successful, storing new tokens')
      
      localStorage.setItem('access_token', tokens.access_token)
      if (tokens.refresh_token) {
        localStorage.setItem('refresh_token', tokens.refresh_token)
      }

      setIsAuthenticated(true)
      
      // Fetch user info with new token
      console.log('Fetching user info with new token')
      const userResponse = await fetch('/api/auth/status', {
        headers: {
          'Authorization': `Bearer ${tokens.access_token}`
        }
      })

      if (userResponse.ok) {
        const data = await userResponse.json()
        if (data.user) {
          console.log('User info updated')
          setUser(data.user)
        }
      }
    } catch (error) {
      console.error('Token refresh failed:', error)
      clearAuth()
      
      // Only redirect to login if we're not already there or in the callback
      const currentPath = window.location.hash.slice(1) // Remove the #
      if (!currentPath.includes('/login') && !currentPath.includes('/auth/callback')) {
        console.log('Redirecting to login...')
        window.location.href = '/#/login'
      }
      throw error
    }
  }

  const logout = async () => {
    try {
      console.log('Logging out...')
      await fetch('/api/auth/logout', {
        method: 'POST',
      })
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuth()
      window.location.href = '/#/login'
    }
  }

  const value = {
    isAuthenticated,
    user,
    isLoading,
    logout,
    refreshToken,
    clearAuth,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
} 