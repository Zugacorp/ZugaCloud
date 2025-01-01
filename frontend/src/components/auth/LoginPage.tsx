import React, { useState, useEffect } from 'react'
import { Button } from '../ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Icons } from '../ui/icons'
import { toast } from 'react-toastify'
import { Loader2 } from 'lucide-react'
import { useConfig } from '@/hooks/useConfig'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { Input } from '../ui/input'
import { Label } from '../ui/label'

export function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const { config, loading: configLoading, error: configError } = useConfig()
  const { isAuthenticated, user, isLoading: authLoading, clearAuth } = useAuth()
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

  const handleCognitoLogin = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/auth/login')
      
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Failed to initiate login')
      }

      // Get the redirect URL from the response
      const data = await response.json()
      if (data.login_url) {
        window.location.href = data.login_url
      } else {
        throw new Error('No login URL provided')
      }
    } catch (error) {
      console.error('Login error:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to initiate login')
    } finally {
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
          <div className="grid gap-4">
            <Button
              variant="outline"
              onClick={handleCognitoLogin}
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Icons.aws className="mr-2 h-4 w-4" />
                  Continue with AWS Cognito
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 