import React from 'react';

export const FileGridSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {[...Array(8)].map((_, i) => (
        <div 
          key={i}
          className="animate-pulse bg-[#112240] p-4 rounded-lg border border-[#233554]"
        >
          <div className="h-32 bg-[#1a365d] rounded-md mb-4" />
          <div className="h-4 bg-[#1a365d] rounded w-3/4 mx-auto" />
          <div className="h-3 bg-[#1a365d] rounded w-1/2 mx-auto mt-2" />
        </div>
      ))}
    </div>
  );
}; 