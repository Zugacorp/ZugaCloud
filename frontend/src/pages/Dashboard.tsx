import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Loader2, FolderOpen } from 'lucide-react'
import { FileGrid } from '@/components/file/FileGrid'
import { BucketSelector } from '@/components/aws/BucketSelector'
import { SyncStatus } from '@/components/sync/SyncStatus'
import { useState } from 'react'
import { useConfig } from '@/hooks/useConfig'
import { useElectronFolder } from '@/hooks/useElectronFolder'

export function Dashboard() {
  const { user, isLoading: authLoading } = useAuth()
  const { config } = useConfig()
  const { selectFolder, isLoading: folderLoading } = useElectronFolder()
  const [currentPath, setCurrentPath] = useState('')

  const handleFolderSelect = async () => {
    try {
      const path = await selectFolder()
      if (path) {
        // Folder selected, you might want to trigger a sync or update UI
        window.location.reload()
      }
    } catch (error) {
      console.error('Failed to select folder:', error)
    }
  }

  if (authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#0a192f] text-white">
      {/* Top Navigation Bar */}
      <div className="sticky top-0 z-50 bg-[#112240] border-b border-[#233554]">
        <div className="container mx-auto px-4 py-4 pb-7">
          <div className="flex items-center justify-between space-x-4">
            {/* Logo */}
            <h1 className="text-xl font-bold text-white whitespace-nowrap">ZugaCloud</h1>

            {/* Bucket and Folder Selection */}
            <div className="flex-1 flex items-center space-x-4 max-w-4xl">
              <div className="flex-1 max-w-[240px]">
                <BucketSelector />
              </div>
              <div className="flex-[2] flex items-center space-x-2">
                <input
                  type="text"
                  value={config.sync_folder || ''}
                  readOnly
                  placeholder="Select a folder to sync..."
                  className="
                    flex-1 
                    h-9
                    px-3 
                    bg-[#0a192f] 
                    border border-[#233554] 
                    rounded-md 
                    text-gray-100 
                    text-sm
                    focus:outline-none 
                    placeholder:text-gray-500
                  "
                />
                <Button
                  onClick={handleFolderSelect}
                  disabled={folderLoading || !config.bucket_name}
                  variant="secondary"
                  className="
                    h-9
                    bg-[#233554] 
                    hover:bg-[#2a4065] 
                    text-white
                    border border-[#233554]
                    disabled:opacity-50
                    whitespace-nowrap
                  "
                >
                  {folderLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <FolderOpen className="h-4 w-4" />
                  )}
                  <span className="ml-2">Select Folder</span>
                </Button>
              </div>
            </div>

            {/* User Email */}
            <div className="flex items-center">
              <span className="text-sm text-gray-400 whitespace-nowrap">
                {user?.email}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 container mx-auto px-4 py-6">
        {/* File Grid */}
        <div className="bg-[#112240] rounded-lg border border-[#233554] p-4">
          <FileGrid 
            currentPath={currentPath}
            onPathChange={setCurrentPath}
          />
        </div>
      </div>

      {/* Bottom Sync Status */}
      <div className="sticky bottom-0 z-50">
        <SyncStatus />
      </div>
    </div>
  )
}
