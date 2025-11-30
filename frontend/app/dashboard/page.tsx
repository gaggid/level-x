'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import DashboardView from '@/components/dashboard/DashboardView';

export default function DashboardPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    const token = localStorage.getItem('user_token');
    
    if (!token) {
      // No token - redirect to login
      router.push('/');
      return;
    }

    try {
      // Verify token is valid
      const response = await fetch('http://localhost:8000/api/user/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setIsAuthenticated(true);
      } else {
        // Invalid token
        localStorage.clear();
        router.push('/');
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.clear();
      router.push('/');
    } finally {
      setIsLoading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0B0B0F]">
        <div className="text-white">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Redirecting...
  }

  return <DashboardView />;
}