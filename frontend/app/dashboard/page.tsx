// app/dashboard/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import DashboardView from '@/components/dashboard/DashboardView';

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate auth check
    setTimeout(() => setIsLoading(false), 500);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0B0B0F]">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  return <DashboardView />;
}