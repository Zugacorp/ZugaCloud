import { Settings, Cloud, Plus, FolderOpen } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Button } from '../common/Button';
import { useConfig } from '../../hooks/useConfig';
import { BucketSelector } from '../aws/BucketSelector';
import { api } from '../../api/client';
import { useElectronFolder } from '../../hooks/useElectronFolder';

const isElectron = Boolean(window.electronAPI);

export const Navbar = () => {
  const { selectFolder, isLoading } = useElectronFolder();
  const { config } = useConfig();

  const handleFolderSelect = async () => {
    try {
      console.log('Checking electronAPI initialization...');
      
      if (!window.electronAPI) {
        console.error('electronAPI is undefined');
        throw new Error('Electron API not properly initialized');
      }

      if (typeof window.electronAPI.selectFolder !== 'function') {
        console.error('selectFolder is not a function');
        throw new Error('Electron API methods not properly exposed');
      }

      console.log('Opening folder selector...');
      const result = await window.electronAPI.selectFolder();
      console.log('Folder selection result:', result);
      
      if (result.success && result.path) {
        const apiResult = await api.selectFolder(result.path);
        if (!apiResult.success) {
          throw new Error(apiResult.error);
        }
        window.location.reload();
      }
    } catch (error) {
      console.error('Folder selection failed:', error);
      alert(error instanceof Error ? error.message : 'Failed to select folder');
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <nav className="navbar">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center h-16 space-x-4">
          <Link to="/" className="flex items-center space-x-2">
            <Cloud className="h-8 w-8 text-blue-500" />
            <span className="text-xl font-bold text-white">ZugaCloud</span>
          </Link>
          
          <div className="flex-1 flex items-center space-x-2">
            <input
              type="text"
              value={config.sync_folder || 'Select a folder to sync...'}
              readOnly
              placeholder="Select a folder to sync..."
              className="flex-1 px-3 py-2 bg-[#112240] border border-[#233554] rounded-md text-gray-100"
            />
            <Button 
              variant="secondary" 
              size="icon" 
              onClick={handleFolderSelect}
              title="Select sync folder"
            >
              <FolderOpen className="h-5 w-5" />
            </Button>
          </div>

          <div className="flex items-center space-x-2">
            <div className="w-48">
              <BucketSelector />
            </div>
            <Button variant="secondary" size="icon">
              <Plus className="h-5 w-5" />
            </Button>
            <Link to="/settings">
              <Button variant="ghost" size="icon">
                <Settings className="h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};
