// components/dashboard/DashboardView.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  Users, 
  Zap, 
  AlertCircle, 
  Sparkles,
  ChevronRight,
  ArrowUp,
  ChevronDown,
  Clock
} from 'lucide-react';
import { 
  RadarChart, 
  PolarGrid, 
  PolarAngleAxis, 
  PolarRadiusAxis, 
  Radar, 
  ResponsiveContainer,
  Tooltip,
  AreaChart,
  Area
} from 'recharts';
import { api } from '@/lib/api';
import { transformBackendAnalysis } from '@/lib/transformers';
import type { UserData, AnalysisResult, AnalysisHistoryItem, PeerAccount, Insight } from '@/types/dashboard';
import { formatDate } from '@/lib/transformers';
import { DetailedPeerCard } from './DetailedPeerCard';  // ADD THIS LINE

// Peer Account Card Component
function PeerCard({ peer }: { peer: PeerAccount }) {
  const sparklineData = Array.from({ length: 7 }, (_, i) => ({
    v: Math.random() * 100 + 50
  }));
  
  // Extract handle without @
  const cleanHandle = peer.handle.replace('@', '');

  return (
    <a 
      href={`https://x.com/${cleanHandle}`}
      target="_blank"
      rel="noopener noreferrer"
      className="block bg-[#1A1A24] border border-white/5 rounded-xl p-4 hover:border-purple-500/30 transition-all hover:scale-[1.02] cursor-pointer"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          {peer.avatar_url ? (
            <img 
              src={peer.avatar_url} 
              alt={peer.name}
              className="w-10 h-10 rounded-full object-cover"
              onError={(e) => {
                // Fallback to initials if image fails to load
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                target.nextElementSibling?.classList.remove('hidden');
              }}
            />
          ) : null}
          <div className={peer.avatar_url ? 'hidden' : 'w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-sm font-bold'}>
            {peer.avatar}
          </div>
          <div>
            <p className="font-bold text-sm">{peer.name}</p>
            <p className="text-xs text-slate-500">{peer.handle}</p>
          </div>
        </div>
        <div className="px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-xs font-bold text-emerald-400">
          {peer.score}%
        </div>
      </div>

      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-400">
          Growth: <span className="text-emerald-400 font-semibold">{peer.trend}</span>
        </div>
        <div className="h-8 w-20">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sparklineData}>
              <defs>
                <linearGradient id={`grad-${peer.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.4}/>
                  <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <Area 
                type="monotone" 
                dataKey="v" 
                stroke="#8b5cf6" 
                fill={`url(#grad-${peer.id})`} 
                strokeWidth={2} 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </a>
  );
}

// Insight Card Component
function InsightCard({ insight, index }: { insight: Insight; index: number }) {
  const priorityColors = {
    1: 'from-red-500 to-orange-500',
    2: 'from-amber-500 to-yellow-500',
    3: 'from-blue-500 to-indigo-500',
  };

  return (
    <div className="bg-[#1A1A24] border border-white/5 rounded-2xl p-6 hover:border-purple-500/20 transition-all">
      <div className="flex items-start gap-4 mb-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${priorityColors[insight.priority as keyof typeof priorityColors]} flex items-center justify-center text-xl font-black flex-shrink-0`}>
          {index + 1}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold mb-2">{insight.title}</h3>
          <p className="text-slate-400 text-sm leading-relaxed mb-4">{insight.finding}</p>
          
          {/* Always show details */}
          <div className="space-y-3 pt-4 border-t border-white/5">
            <div>
              <p className="text-emerald-400 text-sm font-semibold mb-1">📈 Expected Impact</p>
              <p className="text-slate-300 text-sm">{insight.impact}</p>
            </div>
            <div>
              <p className="text-purple-400 text-sm font-semibold mb-1">⚡ Action Steps</p>
              <p className="text-slate-300 text-sm">{insight.action}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main Dashboard Component
export default function DashboardView() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasRunAnalysis, setHasRunAnalysis] = useState(false);
  
  const [userData, setUserData] = useState<UserData | null>(null);
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisResult | null>(null);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryItem[]>([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    setIsLoading(true);
    setError(null);

    try {
      const user = await api.getCurrentUser();
      setUserData(user);
      
      const latest = await api.getLatestAnalysis();
      if (latest) {
        setLatestAnalysis(transformBackendAnalysis(latest));
        setHasRunAnalysis(true);
      }
      
      const history = await api.getAnalysisHistory(5);
      setAnalysisHistory(history);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleStartAnalysis() {
    if (!userData) return;

    // Credit check with dev skip option
    if (userData.credits < 15) {
      const skipPayment = window.confirm(
        '⚠️ Insufficient credits!\n\n' +
        'You need 15 credits to run an analysis.\n\n' +
        'Click OK to view pricing plans, or Cancel to skip for dev testing.'
      );
      
      if (skipPayment) {
        alert('Pricing page coming soon! For now, manually add credits in database.');
        return;
      } else {
        console.log('DEV MODE: Skipping credit check');
      }
    }

    await handleRunAnalysis();
  }

  async function handleRunAnalysis() {
    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await api.runAnalysis('standard');
      const transformed = transformBackendAnalysis(result);
      
      setLatestAnalysis(transformed);
      setHasRunAnalysis(true);
      
      const updatedUser = await api.getCurrentUser();
      setUserData(updatedUser);
      
      const history = await api.getAnalysisHistory(5);
      setAnalysisHistory(history);

      alert('✅ Analysis complete! Check out your new insights below.');
    } catch (err: any) {
      console.error('Analysis failed:', err);
      setError(err.message || 'Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  }

  // Add this function to make history items clickable
  async function loadAnalysisById(analysisId: string) {
    setIsLoading(true);
    try {
      const analysis = await api.getAnalysisById(analysisId);
      const transformed = transformBackendAnalysis(analysis);
      setLatestAnalysis(transformed);
      setHasRunAnalysis(true);
    } catch (error) {
      console.error('Failed to load analysis:', error);
    } finally {
      setIsLoading(false);
    }
  }

  // Loading State
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0B0B0F]">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white text-lg animate-pulse">Loading your insights...</p>
        </div>
      </div>
    );
  }

  // Error State
  if (error && !userData) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0B0B0F]">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Oops! Something went wrong</h2>
          <p className="text-slate-400 mb-6">{error}</p>
          <button 
            onClick={loadDashboardData}
            className="bg-purple-600 hover:bg-purple-700 px-6 py-3 rounded-xl font-bold transition-all"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0B0F] text-white">
      {/* Top Navigation */}
      <nav className="border-b border-white/5 backdrop-blur-xl sticky top-0 z-50 bg-[#0B0B0F]/80">
        <div className="max-w-7xl mx-auto px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-purple-400 flex items-center justify-center">
              <span className="font-black text-white text-xl">X</span>
            </div>
            <span className="font-bold text-xl">Level<span className="text-purple-400">X</span></span>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="bg-[#13131A] px-4 py-2 rounded-lg border border-white/5 flex items-center gap-2">
              <Zap className="text-purple-400" size={16} />
              <span className="text-slate-400 text-sm">Credits</span>
              <span className="text-xl font-bold text-purple-400">{userData?.credits || 250}</span>
            </div>
            <button 
              onClick={() => {
                localStorage.clear();
                window.location.href = '/';
              }}
              className="text-slate-400 hover:text-white transition-colors px-4 py-2"
            >
              Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* User Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">
            Welcome back, <span className="text-purple-400">{userData?.handle}</span>
          </h1>
          <p className="text-slate-400">Ready to level up your X game?</p>
        </div>

        {/* Basic Stats Card - Always Visible */}
        <div className="bg-[#13131A] border border-white/5 rounded-2xl p-6 mb-8">
          <div className="grid grid-cols-3 gap-6">
            <div>
              <p className="text-slate-400 text-sm mb-1">Followers</p>
              <p className="text-3xl font-bold">{userData?.followers_count?.toLocaleString() || 0}</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm mb-1">Following</p>
              <p className="text-3xl font-bold">{userData?.following_count?.toLocaleString() || 0}</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm mb-1">Status</p>
              <p className="text-xl font-bold text-emerald-400">Active</p>
            </div>
          </div>
        </div>

        {/* No Analysis Yet - Show Start Button */}
        {!hasRunAnalysis && (
          <div className="text-center py-20 bg-gradient-to-br from-purple-900/20 to-indigo-900/20 border border-purple-500/20 rounded-2xl">
            <Sparkles className="w-16 h-16 text-purple-500 mx-auto mb-4" />
            <h2 className="text-2xl font-bold mb-2">Ready to get started?</h2>
            <p className="text-slate-400 mb-8 max-w-md mx-auto">
              Run your first analysis to see how you compare to top performers at your level.
            </p>
            <button 
              onClick={handleStartAnalysis}
              disabled={isAnalyzing}
              className="bg-gradient-to-r from-purple-600 to-indigo-600 px-8 py-4 rounded-xl font-bold text-lg hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/50"
            >
              {isAnalyzing ? (
                <span className="flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Analyzing...
                </span>
              ) : (
                '⚡ Start Analysis'
              )}
            </button>
            {isAnalyzing && (
              <p className="text-slate-500 text-sm mt-4">This usually takes 15-30 seconds...</p>
            )}
          </div>
        )}

        {/* Has Analysis - Show Results */}
        {hasRunAnalysis && latestAnalysis && (
          <>
            {/* X-Score */}
            <div className="bg-gradient-to-br from-purple-900/20 to-indigo-900/20 border border-purple-500/20 rounded-2xl p-8 mb-8">
              <div className="flex items-center justify-center mb-8">
                <div className="relative">
                  <svg className="w-48 h-48 transform -rotate-90">
                    <circle
                      cx="96"
                      cy="96"
                      r="88"
                      stroke="rgba(139, 92, 246, 0.1)"
                      strokeWidth="12"
                      fill="none"
                    />
                    <circle
                      cx="96"
                      cy="96"
                      r="88"
                      stroke="url(#gradient)"
                      strokeWidth="12"
                      fill="none"
                      strokeDasharray={`${(latestAnalysis.x_score / 100) * 553} 553`}
                      strokeLinecap="round"
                      className="transition-all duration-1000"
                    />
                    <defs>
                      <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#10b981" />
                        <stop offset="100%" stopColor="#8b5cf6" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <div className="text-5xl font-black text-emerald-400">{latestAnalysis.x_score}</div>
                    <div className="text-sm text-slate-500">X-Score</div>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <div className="flex items-center justify-center gap-2 text-emerald-400 mb-2">
                  <ArrowUp size={20} />
                  <span className="font-bold">+{latestAnalysis.score_change}% from last week</span>
                </div>
                <p className="text-slate-400">
                  Growing faster than <span className="font-bold text-white">{latestAnalysis.percentile}%</span> of accounts at your level
                </p>
              </div>
            </div>

            {/* Performance Matrix - FULL WIDTH */}
            <div className="bg-[#13131A] border border-white/5 rounded-2xl p-6 mb-8">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold flex items-center gap-2">
                    <TrendingUp className="text-purple-400" />
                    Performance Matrix
                  </h2>
                  <p className="text-slate-400 text-sm">See where you shine and where to improve</p>
                </div>
                <div className="flex gap-4 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                    <span className="text-slate-400">You</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-slate-600"></div>
                    <span className="text-slate-400">Top Peers</span>
                  </div>
                </div>
              </div>

              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={latestAnalysis.performance_metrics}>
                    <PolarGrid stroke="#2A2A35" strokeWidth={1.5} />
                    <PolarAngleAxis 
                      dataKey="metric" 
                      tick={{ fill: '#94a3b8', fontSize: 13, fontWeight: 600 }}
                    />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar
                      name="You"
                      dataKey="you"
                      stroke="#8b5cf6"
                      strokeWidth={3}
                      fill="#8b5cf6"
                      fillOpacity={0.3}
                    />
                    <Radar
                      name="Peers"
                      dataKey="peers"
                      stroke="#475569"
                      strokeWidth={2}
                      fill="#475569"
                      fillOpacity={0.1}
                      strokeDasharray="5 5"
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#13131A', 
                        borderColor: '#2A2A35', 
                        borderRadius: '12px',
                        border: '1px solid rgba(139, 92, 246, 0.2)'
                      }}
                      itemStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>

              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-white/5">
                <div className="text-center">
                  <div className="text-2xl font-bold text-emerald-400">
                    {latestAnalysis.performance_metrics.filter(m => m.you > m.peers).length}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">Strengths</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-amber-400">
                    {latestAnalysis.performance_metrics.filter(m => Math.abs(m.you - m.peers) < 10).length}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">On Track</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-400">
                    {latestAnalysis.performance_metrics.filter(m => m.you < m.peers - 10).length}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">Needs Work</div>
                </div>
              </div>
            </div>

            {/* Top Peers - Deep Analysis */}
            <div className="mb-8">
              <div className="mb-6">
                <h2 className="text-2xl font-bold flex items-center gap-2 mb-2">
                  <Users className="text-indigo-400" />
                  Top Peers - Deep Analysis
                </h2>
                <p className="text-slate-400">
                  Learn exactly what makes these accounts successful and how to copy their tactics
                </p>
              </div>
              
              <div className="space-y-6">
                {latestAnalysis.top_peers && latestAnalysis.top_peers.length > 0 ? (
                  latestAnalysis.top_peers.map((peer) => (
                    <DetailedPeerCard key={peer.id} peer={peer} />
                  ))
                ) : (
                  <div className="bg-[#1A1A24] border border-white/5 rounded-xl p-8 text-center">
                    <Users className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <p className="text-slate-400 mb-2">No peer data available</p>
                    <p className="text-slate-500 text-sm">Peer insights will appear after running a new analysis</p>
                  </div>
                )}
              </div>
            </div>

            {/* AI Insights */}
            <div className="mt-8">
              <div className="mb-6">
                <h2 className="text-2xl font-bold flex items-center gap-2 mb-2">
                  <Sparkles className="text-amber-400" />
                  AI Growth Insights
                </h2>
                <p className="text-slate-400">Personalized tactics from your top-performing peers</p>
              </div>

              <div className="grid lg:grid-cols-3 gap-6">
                {latestAnalysis.insights.map((insight, index) => (
                  <InsightCard key={index} insight={insight} index={index} />
                ))}
              </div>
            </div>

            {/* Recent Analyses */}
            <div className="mt-8 bg-[#13131A] border border-white/5 rounded-2xl p-6">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Clock className="text-purple-400" />
                Recent Analyses
              </h2>
              
              {analysisHistory.length > 0 ? (
                <div className="space-y-3">
                  {analysisHistory.map((analysis) => (
                    <button
                      key={analysis.id}
                      onClick={() => loadAnalysisById(analysis.id)}
                      className="w-full flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-all border border-transparent hover:border-purple-500/30 text-left"
                    >
                      <div>
                        <p className="text-sm font-semibold">{formatDate(analysis.created_at)}</p>
                        <p className="text-xs text-slate-500 mt-1">
                          {new Date(analysis.created_at).toLocaleString('en-US', {
                            weekday: 'short',
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">{analysis.credits_used} credits used</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold text-2xl text-purple-400">{analysis.x_score}</p>
                        <p className="text-xs text-slate-500">X-Score</p>
                        {analysis.id === latestAnalysis.id && (
                          <span className="inline-block mt-1 px-2 py-0.5 bg-emerald-500/20 text-emerald-400 text-xs rounded-full">
                            Current
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No analysis history yet. Run your first analysis!</p>
              )}
            </div>
          </>
        )}
      </div>

      {/* Floating Run Analysis Button */}
      {hasRunAnalysis && (
        <div className="fixed bottom-8 right-8 z-50">
          <button 
            onClick={handleStartAnalysis}
            disabled={isAnalyzing}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 px-6 py-4 rounded-full font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-2xl shadow-purple-500/50 hover:scale-110 flex items-center gap-2"
            title="Run new analysis"
          >
            {isAnalyzing ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Run Analysis
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}