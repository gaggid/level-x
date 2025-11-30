'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function CallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState('Processing...');

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const error = searchParams.get('error');

    if (error) {
      setStatus('Authentication failed. Redirecting...');
      setTimeout(() => router.push('/'), 3000);
      return;
    }

    if (code && state) {
      // TODO: Send to your FastAPI backend
      fetch('/api/auth/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, state })
      })
        .then(res => res.json())
        .then(data => {
          if (data.success) {
            setStatus('Success! Redirecting to dashboard...');
            localStorage.setItem('user_token', data.token);
            setTimeout(() => router.push('/dashboard'), 1500);
          } else {
            setStatus('Authentication failed. Redirecting...');
            setTimeout(() => router.push('/'), 3000);
          }
        })
        .catch(() => {
          setStatus('Error occurred. Redirecting...');
          setTimeout(() => router.push('/'), 3000);
        });
    }
  }, [searchParams, router]);

  return (
    <div className="flex items-center justify-center h-screen bg-[#0B0B0F]">
      <div className="text-center">
        <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-white text-lg">{status}</p>
      </div>
    </div>
  );
}