import { useAuth } from '@/contexts/AuthContext'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2 } from 'lucide-react'

export function Dashboard() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="grid gap-6">
        {/* Welcome Card */}
        <Card>
          <CardHeader>
            <CardTitle>Welcome to ZugaCloud</CardTitle>
            <CardDescription>
              {user?.email_verified 
                ? 'Your email is verified and your account is ready to use.'
                : 'Please verify your email to access all features.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <h3 className="font-medium">Account Details</h3>
                <p className="text-sm text-muted-foreground">Email: {user?.email}</p>
              </div>
              
              {!user?.email_verified && (
                <div>
                  <Button variant="secondary">
                    Resend Verification Email
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Upload Files</CardTitle>
              <CardDescription>
                Securely store and manage your files
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">
                Start Upload
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Storage Usage</CardTitle>
              <CardDescription>
                Monitor your storage space
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">0 GB</div>
              <p className="text-sm text-muted-foreground">of 10 GB used</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Recent Activity</CardTitle>
              <CardDescription>
                View your recent actions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">No recent activity</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
