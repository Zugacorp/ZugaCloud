import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { toast } from 'react-toastify'

export function AuthCallback() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const { refreshToken, clearAuth } = useAuth()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        console.log('Starting auth callback flow...')
        const code = searchParams.get('code')
        console.log('Auth code present:', !!code)
        
        if (!code) {
          throw new Error('No authorization code received')
        }

        // Clear any existing auth state before proceeding
        clearAuth()

        console.log('Exchanging code for tokens...')
        // Exchange the code for tokens
        const response = await fetch('/api/auth/callback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ code }),
        })

        console.log('Token exchange response status:', response.status)
        if (!response.ok) {
          const data = await response.json()
          console.error('Token exchange error:', data)
          throw new Error(data.error || 'Failed to exchange authorization code')
        }

        const tokens = await response.json()
        console.log('Received tokens:', {
          hasAccessToken: !!tokens.access_token,
          hasIdToken: !!tokens.id_token,
          hasRefreshToken: !!tokens.refresh_token
        })
        
        // Store the tokens
        localStorage.setItem('access_token', tokens.access_token)
        localStorage.setItem('id_token', tokens.id_token)
        if (tokens.refresh_token) {
          localStorage.setItem('refresh_token', tokens.refresh_token)
        }

        console.log('Stored tokens in localStorage')
        console.log('Refreshing auth context...')
        // Update auth context with new tokens
        await refreshToken()
        
        console.log('Successfully logged in, redirecting to dashboard...')
        toast.success('Successfully logged in!')
        
        // Use replace to prevent going back to the callback page
        navigate('/dashboard', { replace: true })
      } catch (err) {
        console.error('Auth callback error:', err)
        const errorMessage = err instanceof Error ? err.message : 'Authentication failed'
        setError(errorMessage)
        toast.error(errorMessage)
        clearAuth()
        navigate('/login', { replace: true })
      }
    }

    handleCallback()
  }, [searchParams, navigate, refreshToken, clearAuth])

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-500 mb-4">Authentication Error</h1>
          <p className="text-gray-600">{error}</p>
          <button 
            onClick={() => navigate('/login', { replace: true })}
            className="mt-4 text-blue-500 hover:underline"
          >
            Return to Login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Logging you in...</h1>
        <p className="text-gray-600">Please wait while we complete the authentication process.</p>
      </div>
    </div>
  )
} 