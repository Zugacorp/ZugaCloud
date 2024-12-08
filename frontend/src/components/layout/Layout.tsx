import React from 'react';
import { Navbar } from './Navbar';
import { SyncStatus } from '../sync/SyncStatus';

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#0a192f] flex flex-col">
      <Navbar />
      <main className="flex-1 container mx-auto px-4 py-6 mb-16">
        {children}
      </main>
      <SyncStatus />
    </div>
  );
};
