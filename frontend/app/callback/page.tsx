'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('Processing authentication...');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    console.log('📥 Callback received:', { code: !!code, state: !!state, error });

    if (error) {
      setStatus('Authentication failed. Redirecting...');
      setTimeout(() => router.push('/'), 3000);
      return;
    }

    if (code && state) {
      handleCallback(code, state);
    } else {
      setStatus('Invalid callback. Redirecting...');
      setTimeout(() => router.push('/'), 3000);
    }
  }, [searchParams, router]);

  async function handleCallback(code: string, state: string) {
    try {
      console.log('🔄 Exchanging code for token...');
      
      const response = await fetch('http://localhost:8000/api/auth/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, state })
      });

      const data = await response.json();
      console.log('📦 Callback response:', data);

      if (data.success) {
        setStatus('Success! Redirecting to dashboard...');
        
        // Store EVERYTHING
        localStorage.setItem('user_token', data.token);
        localStorage.setItem('user_id', data.user.id);
        localStorage.setItem('user_handle', data.user.handle);
        
        console.log('💾 Saved to localStorage:', {
          token: data.token,
          id: data.user.id,
          handle: data.user.handle
        });
        
        // Wait a bit to ensure localStorage is saved
        setTimeout(() => {
          console.log('🚀 Redirecting to dashboard...');
          router.push('/dashboard');
        }, 500);
      } else {
        setStatus('Authentication failed. Redirecting...');
        setTimeout(() => router.push('/'), 3000);
      }
    } catch (error) {
      console.error('❌ Callback error:', error);
      setStatus('Error occurred. Redirecting...');
      setTimeout(() => router.push('/'), 3000);
    }
  }

  return (
    <div className="flex items-center justify-center h-screen bg-[#0B0B0F]">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-white text-lg">{status}</p>
      </div>
    </div>
  );
}