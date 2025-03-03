import React, { useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Icons } from '../ui/icons'
import { toast } from 'react-toastify'
import { Loader2 } from 'lucide-react'
import { useConfig } from '@/hooks/useConfig'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import * as AmazonCognitoIdentity from 'amazon-cognito-identity-js'

interface CognitoError extends Error {
  code: string;
  name: string;
  message: string;
}

interface AuthCallbacks {
  onSuccess: (session: AmazonCognitoIdentity.CognitoUserSession) => void;
  onFailure: (err: CognitoError) => void;
}

export function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { config, loading: configLoading, error: configError } = useConfig()
  const { isAuthenticated, user, isLoading: authLoading, clearAuth, setIsAuthenticated, setUser } = useAuth()
  const navigate = useNavigate()

  // Clear auth state on mount
  useEffect(() => {
    clearAuth()
  }, [clearAuth])

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated && user) {
      console.log('User already authenticated, redirecting to dashboard...')
      navigate('/dashboard', { replace: true })
    }
  }, [isAuthenticated, user, authLoading, navigate])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      if (!config.user_pool_id || !config.client_id) {
        throw new Error('Missing Cognito configuration')
      }

      const userPool = new AmazonCognitoIdentity.CognitoUserPool({
        UserPoolId: config.user_pool_id,
        ClientId: config.client_id
      })

      const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
        Username: email,
        Pool: userPool
      })

      const authDetails = new AmazonCognitoIdentity.AuthenticationDetails({
        Username: email,
        Password: password
      })

      const callbacks: AuthCallbacks = {
        onSuccess: async (session: AmazonCognitoIdentity.CognitoUserSession) => {
          const idToken = session.getIdToken().getJwtToken()
          const accessToken = session.getAccessToken().getJwtToken()
          const refreshToken = session.getRefreshToken().getToken()

          // Store tokens
          localStorage.setItem('access_token', accessToken)
          localStorage.setItem('id_token', idToken)
          localStorage.setItem('refresh_token', refreshToken)

          // Get user attributes from the ID token
          const payload = session.getIdToken().decodePayload()
          
          // Set user and authentication state
          setUser({
            sub: payload.sub,
            email: payload.email,
            email_verified: payload.email_verified === 'true',
            tier: payload['custom:tier'] || 'free'
          })
          setIsAuthenticated(true)
          setIsLoading(false)

          // Show success message and redirect
          toast.success('Successfully logged in!')
          navigate('/dashboard', { replace: true })
        },
        onFailure: (err: CognitoError) => {
          console.error('Login error:', err)
          let errorMessage = 'Failed to login. Please try again.'
          
          if (err.code === 'UserNotConfirmedException') {
            errorMessage = 'Please verify your email address before logging in.'
          } else if (err.code === 'NotAuthorizedException') {
            errorMessage = 'Incorrect email or password.'
          } else if (err.code === 'UserNotFoundException') {
            errorMessage = 'No account found with this email.'
          }
          
          toast.error(errorMessage)
          setIsLoading(false)
        }
      }

      cognitoUser.authenticateUser(authDetails, callbacks)
    } catch (error) {
      console.error('Login error:', error)
      toast.error(error instanceof Error ? error.message : 'An unexpected error occurred. Please try again.')
      setIsLoading(false)
    }
  }

  // Show loading state while configuration or auth is loading
  if (configLoading || authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  // Show error state if configuration failed to load
  if (configError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-background">
        <Card className="w-[380px]">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center text-red-500">Configuration Error</CardTitle>
            <CardDescription className="text-center">
              {configError.message}
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <Card className="w-[380px]">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Welcome to ZugaCloud</CardTitle>
          <CardDescription className="text-center">
            Sign in to your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button 
              type="submit"
              disabled={isLoading} 
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
          <div className="mt-4 text-center">
            <span className="text-sm text-muted-foreground">
              Don't have an account?{' '}
              <a 
                onClick={() => navigate('/register')} 
                className="text-primary hover:underline cursor-pointer"
              >
                Create Account
              </a>
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 