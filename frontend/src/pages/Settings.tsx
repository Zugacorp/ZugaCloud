import React from 'react';
import { CredentialsForm } from '../components/aws/CredentialsForm';
import { useConfig } from '../hooks/useConfig';

export const Settings: React.FC = () => {
  const { config, updateConfig } = useConfig();

  return (
    <div className="max-w-2xl mx-auto py-8 px-4">
      <h1 className="text-2xl font-bold mb-8 text-gray-100">Settings</h1>
      
      <div className="bg-[#112240] shadow-lg rounded-lg p-6 mb-6 border border-[#233554]">
        <h2 className="text-lg font-medium mb-4 text-gray-100">AWS Credentials</h2>
        <CredentialsForm />
      </div>

      <div className="bg-[#112240] shadow-lg rounded-lg p-6 border border-[#233554]">
        <h2 className="text-lg font-medium mb-4 text-gray-100">Sync Settings</h2>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300">
              Refresh Frequency (seconds)
            </label>
            <input
              type="number"
              value={config.refresh_frequency || 300}
              onChange={(e) => updateConfig({ 
                refresh_frequency: parseInt(e.target.value) 
              })}
              min="60"
              className="mt-1 block w-full rounded-md bg-[#0a192f] border-[#233554] text-gray-100 focus:border-blue-500 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
