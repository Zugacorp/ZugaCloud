import React from 'react';
import { cn } from '../../utils/cn';

interface ProgressProps {
  value: number;
  className?: string;
}

export const Progress: React.FC<ProgressProps> = ({ value, className }) => {
  return (
    <div className={cn("w-full bg-[#1a365d] rounded-full h-2", className)}>
      <div
        className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-in-out"
        style={{ 
          width: `${Math.min(100, Math.max(0, value))}%`,
          transition: 'width 0.3s ease-in-out'
        }}
      />
    </div>
  );
};