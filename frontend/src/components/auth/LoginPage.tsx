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
import { z } from 'zod'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters')
})

type LoginFormData = z.infer<typeof loginSchema>

export function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const { config, loading: configLoading, error: configError } = useConfig()
  const { isAuthenticated, user, isLoading: authLoading, clearAuth } = useAuth()
  const navigate = useNavigate()

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: ''
    }
  })

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

  const handleLogin = async (data: LoginFormData) => {
    try {
      setIsLoading(true)
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: data.email,
          password: data.password
        })
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Login failed')
      }

      const responseData = await response.json()
      if (responseData.success) {
        navigate('/dashboard', { replace: true })
      } else {
        throw new Error('Login failed')
      }
    } catch (error) {
      console.error('Login error:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to login')
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
          <form onSubmit={form.handleSubmit(handleLogin)} className="grid gap-4">
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                {...form.register('email')}
                disabled={isLoading}
              />
              {form.formState.errors.email && (
                <p className="text-sm text-red-500">{form.formState.errors.email.message}</p>
              )}
            </div>
            <div className="grid gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                {...form.register('password')}
                disabled={isLoading}
              />
              {form.formState.errors.password && (
                <p className="text-sm text-red-500">{form.formState.errors.password.message}</p>
              )}
            </div>
            <Button type="submit" disabled={isLoading} className="w-full">
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
        </CardContent>
      </Card>
    </div>
  )
} 