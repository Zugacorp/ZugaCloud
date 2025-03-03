import React, { createContext, useContext, useState, useEffect } from 'react'
import { toast } from 'react-toastify'
import { CognitoUserPool, CognitoUser, CognitoRefreshToken, CognitoUserSession } from 'amazon-cognito-identity-js'

// Error types
export class AuthError extends Error {
  constructor(message: string, public code: string) {
    super(message)
    this.name = 'AuthError'
  }
}

export class TokenError extends AuthError {
  constructor(message: string) {
    super(message, 'TOKEN_ERROR')
  }
}

export class NetworkError extends AuthError {
  constructor(message: string) {
    super(message, 'NETWORK_ERROR')
  }
}

// Unified User interface
export interface User {
  sub: string
  email: string
  email_verified: boolean
  tier?: string
  tierFeatures?: {
    max_requests: number
    max_storage: string
    features: string[]
  }
  [key: string]: any
}

interface AuthContextType {
  isAuthenticated: boolean
  user: User | null
  isLoading: boolean
  error: AuthError | null
  setUser: (user: User | null) => void
  setIsAuthenticated: (value: boolean) => void
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  clearAuth: () => void
  clearError: () => void
  refreshTierInfo: () => Promise<void>
}

export const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<AuthError | null>(null)

  const clearError = () => setError(null)

  const clearAuth = () => {
    console.log('\n=== Clearing Auth State ===')
    console.log('Previous state:', {
      isAuthenticated,
      hasUser: !!user,
      tokens: {
        hasAccessToken: !!localStorage.getItem('access_token'),
        hasIdToken: !!localStorage.getItem('id_token'),
        hasRefreshToken: !!localStorage.getItem('refresh_token')
      }
    })
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('id_token')
    localStorage.removeItem('refresh_token')
    setIsAuthenticated(false)
    setUser(null)
    setIsLoading(false)
    setError(null)
    
    console.log('Auth state cleared')
  }

  const handleAuthError = (error: unknown, customMessage?: string) => {
    console.error('Auth error:', error)
    
    let authError: AuthError
    
    if (error instanceof AuthError) {
      authError = error
    } else if (error instanceof Error) {
      authError = new AuthError(error.message, 'UNKNOWN_ERROR')
    } else {
      authError = new AuthError(customMessage || 'An unknown error occurred', 'UNKNOWN_ERROR')
    }
    
    setError(authError)
    toast.error(authError.message)
    return authError
  }

  // Check authentication status on mount and token changes
  useEffect(() => {
    const checkAuth = async () => {
      try {
        clearError()
        console.log('\n=== Checking Auth State ===')
        const accessToken = localStorage.getItem('access_token')
        const idToken = localStorage.getItem('id_token')
        console.log('Initial state:', {
          hasAccessToken: !!accessToken,
          hasIdToken: !!idToken,
          isAuthenticated,
          hasUser: !!user
        })
        
        if (!accessToken || !idToken) {
          console.log('No tokens found, clearing auth state')
          clearAuth()
          return
        }

        // Parse the JWT token to check expiration
        try {
          const tokenPayload = JSON.parse(atob(idToken.split('.')[1]))
          const expirationTime = tokenPayload.exp * 1000 // Convert to milliseconds
          
          if (Date.now() >= expirationTime) {
            console.log('Token expired, attempting refresh')
            await refreshToken()
            return
          }

          // Token is valid, set the user data from the ID token
          console.log('Token valid, setting user data')
          setIsAuthenticated(true)
          setUser({
            sub: tokenPayload.sub,
            email: tokenPayload.email,
            email_verified: tokenPayload.email_verified === 'true',
            tier: tokenPayload['custom:tier'] || 'free'
          })
        } catch (error) {
          console.error('Error parsing token:', error)
          throw new TokenError('Invalid token format')
        }
      } catch (error) {
        console.error('Auth check failed:', error)
        handleAuthError(error, 'Authentication check failed')
        clearAuth()
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const refreshToken = async () => {
    try {
      clearError()
      console.log('Starting token refresh...')
      const refresh_token = localStorage.getItem('refresh_token')
      if (!refresh_token) {
        throw new TokenError('No refresh token available')
      }

      // Get Cognito configuration
      const userPoolId = import.meta.env.VITE_COGNITO_USER_POOL_ID
      const clientId = import.meta.env.VITE_COGNITO_CLIENT_ID

      if (!userPoolId || !clientId) {
        throw new Error('Missing Cognito configuration')
      }

      // Create Cognito refresh token object
      const token = new CognitoRefreshToken({ RefreshToken: refresh_token })

      // Create user pool
      const userPool = new CognitoUserPool({
        UserPoolId: userPoolId,
        ClientId: clientId
      })

      // Get the last user email from local storage or ID token
      const idToken = localStorage.getItem('id_token')
      let email = ''
      try {
        const payload = JSON.parse(atob(idToken!.split('.')[1]))
        email = payload.email
      } catch (error) {
        throw new TokenError('Could not get user email from token')
      }

      // Create Cognito user object
      const cognitoUser = new CognitoUser({
        Username: email,
        Pool: userPool
      })

      // Refresh the session
      await new Promise<void>((resolve, reject) => {
        cognitoUser.refreshSession(token, (err: Error | null, session: CognitoUserSession | null) => {
          if (err || !session) {
            console.error('Token refresh failed:', err)
            reject(new TokenError(err?.message || 'Token refresh failed'))
            return
          }

          // Store the new tokens
          const accessToken = session.getAccessToken().getJwtToken()
          const idToken = session.getIdToken().getJwtToken()
          const newRefreshToken = session.getRefreshToken().getToken()

          localStorage.setItem('access_token', accessToken)
          localStorage.setItem('id_token', idToken)
          localStorage.setItem('refresh_token', newRefreshToken)

          // Get user data from ID token
          const payload = session.getIdToken().decodePayload()
          
          // Update auth state
          setIsAuthenticated(true)
          setUser({
            sub: payload.sub,
            email: payload.email,
            email_verified: payload.email_verified === 'true',
            tier: payload['custom:tier'] || 'free'
          })

          resolve()
        })
      })
    } catch (error) {
      const authError = handleAuthError(error, 'Token refresh failed')
      clearAuth()
      
      // Only redirect to login if we're not already there or in the callback
      const currentPath = window.location.hash.slice(1)
      if (!currentPath.includes('/login') && !currentPath.includes('/auth/callback')) {
        console.log('Redirecting to login...')
        window.location.href = '/#/login'
      }
      throw authError
    }
  }

  const logout = async () => {
    try {
      clearError()
      console.log('Logging out...')
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
      }).catch(() => {
        throw new NetworkError('Failed to connect to authentication server during logout')
      })

      if (!response.ok) {
        throw new AuthError('Logout request failed', 'LOGOUT_ERROR')
      }
    } catch (error) {
      handleAuthError(error, 'Logout failed')
    } finally {
      clearAuth()
      window.location.href = '/#/login'
    }
  }

  const refreshTierInfo = async () => {
    try {
      if (!user || !isAuthenticated) return

      const accessToken = localStorage.getItem('access_token')
      if (!accessToken) return

      const response = await fetch('/api/auth/user/tier', {
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch tier information')
      }

      const tierData = await response.json()
      setUser(prev => prev ? {
        ...prev,
        tier: tierData.tier,
        tierFeatures: tierData.features
      } : null)
    } catch (error) {
      console.error('Failed to refresh tier info:', error)
    }
  }

  const value = {
    isAuthenticated,
    user,
    isLoading,
    error,
    setUser,
    setIsAuthenticated,
    logout,
    refreshToken,
    clearAuth,
    clearError,
    refreshTierInfo
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