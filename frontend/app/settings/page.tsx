'use client';

import { useState } from 'react';
import { User, CreditCard, Bell, Shield } from 'lucide-react';

export default function SettingsPage() {
  return (
    <div className="min-h-screen bg-[#0B0B0F] text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Settings</h1>
        
        <div className="space-y-6">
          {/* Profile Section */}
          <div className="bg-[#13131A] border border-white/5 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <User className="text-purple-400" size={24} />
              <h2 className="text-xl font-bold">Profile</h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-400">X Handle</label>
                <p className="text-lg">@your_handle</p>
              </div>
              <div>
                <label className="text-sm text-slate-400">Account Connected</label>
                <p className="text-sm text-emerald-400">✓ Connected</p>
              </div>
            </div>
          </div>

          {/* Credits & Billing */}
          <div className="bg-[#13131A] border border-white/5 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <CreditCard className="text-purple-400" size={24} />
              <h2 className="text-xl font-bold">Credits & Billing</h2>
            </div>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-slate-400">Available Credits</label>
                <p className="text-2xl font-bold text-purple-400">250 credits</p>
              </div>
              <button className="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-lg font-semibold">
                Buy More Credits
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}