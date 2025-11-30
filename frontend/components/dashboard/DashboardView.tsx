// components/dashboard/DashboardView.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  Zap, TrendingUp, Users, Lightbulb, Clock, ArrowRight,
  Sparkles, Target, ChevronRight, Play, BarChart3, Crown, AlertCircle
} from 'lucide-react';
import { 
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, 
  PolarRadiusAxis, Radar, Tooltip, AreaChart, Area
} from 'recharts';
import { api } from '@/lib/api';
import { transformBackendAnalysis, formatDate } from '@/lib/transformers';
import { UserData, AnalysisResult, AnalysisHistoryItem } from '@/types/dashboard';

// ============================================
// ANIMATED COUNTER COMPONENT
// ============================================
function AnimatedNumber({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = value;
    const duration = 2000;
    const increment = end / (duration / 16);

    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [value]);

  return (
    <span>
      {count.toFixed(1)}
      {suffix}
    </span>
  );
}

// ============================================
// CIRCULAR PROGRESS (X-SCORE GAUGE)
// ============================================
function CircularProgress({ score }: { score: number }) {
  const [progress, setProgress] = useState(0);
  const circumference = 2 * Math.PI * 120;

  useEffect(() => {
    setTimeout(() => setProgress(score), 100);
  }, [score]);

  const getColor = (score: number) => {
    if (score >= 80) return '#10b981'; // green
    if (score >= 60) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <div className="relative w-64 h-64 mx-auto">
      {/* Background Circle */}
      <svg className="transform -rotate-90 w-full h-full">
        <circle
          cx="128"
          cy="128"
          r="120"
          stroke="rgba(255,255,255,0.05)"
          strokeWidth="12"
          fill="none"
        />
        {/* Progress Circle */}
        <circle
          cx="128"
          cy="128"
          r="120"
          stroke={getColor(score)}
          strokeWidth="12"
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - (progress / 100) * circumference}
          strokeLinecap="round"
          className="transition-all duration-2000 ease-out"
          style={{ filter: `drop-shadow(0 0 8px ${getColor(score)})` }}
        />
      </svg>
      {/* Center Score */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="text-6xl font-black" style={{ color: getColor(score) }}>
          <AnimatedNumber value={score} />
        </div>
        <div className="text-slate-400 text-sm mt-2">X-Score</div>
      </div>
    </div>
  );
}

// ============================================
// INSIGHT CARD WITH INTERACTION
// ============================================
function InsightCard({ 
  insight, 
  index 
}: { 
  insight: {
    title: string;
    finding: string;
    impact: string;
    action: string;
  };
  index: number;
}) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <div 
      className="group bg-gradient-to-br from-[#1A1A23] to-[#13131A] border border-white/5 rounded-2xl p-6 hover:border-purple-500/50 transition-all duration-300 hover:-translate-y-2 hover:shadow-[0_20px_40px_rgba(139,92,246,0.2)] cursor-pointer"
      style={{ 
        animation: `slideUp 0.6s ease-out ${index * 0.1}s both`
      }}
      onClick={() => setIsExpanded(!isExpanded)}
    >
      {/* Priority Badge */}
      <div className="flex items-center justify-between mb-4">
        <div className="px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-xs font-bold text-purple-400">
          Priority #{index + 1}
        </div>
        <Lightbulb className="text-amber-400 group-hover:rotate-12 transition-transform" size={24} />
      </div>

      {/* Title */}
      <h4 className="text-lg font-bold mb-3 group-hover:text-purple-400 transition-colors">
        {insight.title}
      </h4>

      {/* Finding */}
      <p className="text-sm text-slate-400 mb-4 leading-relaxed">
        {insight.finding}
      </p>

      {/* Impact */}
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={16} className="text-emerald-400" />
        <span className="text-sm text-emerald-400 font-semibold">{insight.impact}</span>
      </div>

      {/* Expandable Action */}
      <div 
        className={`overflow-hidden transition-all duration-300 ${
          isExpanded ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="pt-4 border-t border-white/10">
          <div className="text-xs text-slate-500 mb-2">ACTION PLAN</div>
          <p className="text-sm text-white">{insight.action}</p>
          <button className="mt-4 w-full py-2 bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/30 rounded-lg text-sm font-semibold text-purple-400 transition-colors flex items-center justify-center gap-2">
            <Play size={14} /> Implement Now
          </button>
        </div>
      </div>

      {/* Expand Indicator */}
      <div className="flex items-center justify-center mt-4 text-xs text-slate-500">
        <ChevronRight 
          size={16} 
          className={`transform transition-transform ${isExpanded ? 'rotate-90' : ''}`}
        />
        <span>{isExpanded ? 'Less' : 'More'} Details</span>
      </div>
    </div>
  );
}

// ============================================
// PEER CARD WITH SPARKLINE
// ============================================
function PeerCard({ peer, index }: { peer: any; index: number }) {
  const sparklineData = [
    { v: peer.score - 15 },
    { v: peer.score - 10 },
    { v: peer.score - 5 },
    { v: peer.score + 2 },
    { v: peer.score }
  ];

  return (
    <div 
      className="bg-[#1A1A23] border border-white/5 rounded-xl p-4 hover:border-purple-500/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-[0_10px_30px_rgba(139,92,246,0.15)] cursor-pointer group"
      style={{ 
        animation: `slideRight 0.5s ease-out ${index * 0.1}s both`
      }}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {/* Avatar */}
          <div className="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg group-hover:scale-110 transition-transform">
            {peer.avatar}
          </div>
          <div>
            <p className="font-semibold text-white group-hover:text-purple-400 transition-colors">
              {peer.name}
            </p>
            <p className="text-xs text-slate-500">{peer.handle}</p>
          </div>
        </div>
        {/* Match Score Badge */}
        <div className="px-2 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-xs font-bold text-emerald-400">
          {peer.score}%
        </div>
      </div>

      {/* Growth Trend */}
      <div className="flex items-center justify-between">
        <div className="text-xs text-slate-400">
          Growth: <span className="text-emerald-400 font-semibold">{peer.trend}</span>
        </div>
        {/* Sparkline */}
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
    </div>
  );
}

// ============================================
// MAIN DASHBOARD
// ============================================
export default function DashboardView() {
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [userData, setUserData] = useState<UserData | null>(null);
  const [latestAnalysis, setLatestAnalysis] = useState<AnalysisResult | null>(null);
  const [analysisHistory, setAnalysisHistory] = useState<AnalysisHistoryItem[]>([]);

  // Fetch all dashboard data
  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch all data in parallel
      const [user, latest, history] = await Promise.all([
        api.getCurrentUser(),
        api.getLatestAnalysis(),
        api.getAnalysisHistory(5),
      ]);

      setUserData(user);
      
      if (latest) {
        setLatestAnalysis(transformBackendAnalysis(latest));
      }
      
      setAnalysisHistory(history);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }

  // Handle Run New Analysis
  async function handleRunAnalysis() {
    if (!userData || userData.credits < 15) {
      alert('Insufficient credits. Please purchase more credits.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const result = await api.runAnalysis('standard');
      const transformed = transformBackendAnalysis(result);
      
      setLatestAnalysis(transformed);
      
      // Update credits
      const updatedUser = await api.getCurrentUser();
      setUserData(updatedUser);
      
      // Refresh history
      const history = await api.getAnalysisHistory(5);
      setAnalysisHistory(history);

      // Success message
      alert('✅ Analysis complete! Check out your new insights below.');
    } catch (err) {
      console.error('Analysis failed:', err);
      setError('Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  }

  // Loading state
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

  // Error state
  if (error && !latestAnalysis) {
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

  // No analysis yet
  if (!latestAnalysis) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#0B0B0F]">
        <div className="text-center max-w-md">
          <Sparkles className="w-16 h-16 text-purple-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-white mb-2">Ready to get started?</h2>
          <p className="text-slate-400 mb-6">
            Run your first analysis to see how you compare to top performers at your level.
          </p>
          <button 
            onClick={handleRunAnalysis}
            disabled={isAnalyzing}
            className="bg-gradient-to-r from-purple-600 to-indigo-600 px-8 py-4 rounded-xl font-bold hover:scale-105 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? 'Analyzing...' : '🚀 Run Your First Analysis'}
          </button>
          <p className="text-sm text-slate-500 mt-4">
            Cost: 15 credits • You have {userData?.credits || 0} credits
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0B0F] text-white">
      
      {/* Ambient Background */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute top-[-20%] left-[20%] w-[600px] h-[600px] bg-purple-600/10 rounded-full blur-[120px] animate-pulse-slow" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[100px] animate-pulse-slow" style={{ animationDelay: '1s' }} />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-white/5 backdrop-blur-xl bg-[#0B0B0F]/80 sticky top-0">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex justify-between items-center">
            <div className="animate-fadeIn">
              <h1 className="text-2xl font-bold mb-1">
                Welcome back, <span className="text-purple-400">{userData?.handle || '@user'}</span>
              </h1>
              <p className="text-slate-400 text-sm">Ready to level up your X game?</p>
            </div>
            <div className="flex items-center gap-4 animate-fadeIn" style={{ animationDelay: '0.2s' }}>
              {/* Credit Balance */}
              <div className="flex items-center gap-2 px-4 py-2 bg-purple-500/10 rounded-xl border border-purple-500/20 hover:bg-purple-500/20 transition-all cursor-pointer group">
                <Zap className="text-purple-400 group-hover:scale-110 transition-transform" size={20} />
                <div>
                  <div className="text-xs text-slate-400">Credits</div>
                  <div className="font-bold text-lg">
                    <AnimatedNumber value={userData?.credits || 0} />
                  </div>
                </div>
              </div>
              
              {/* Run Analysis Button */}
              <button 
                onClick={handleRunAnalysis}
                disabled={isAnalyzing || (userData?.credits || 0) < 15}
                className="relative bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-3 rounded-xl font-bold hover:scale-105 transition-all shadow-[0_0_30px_rgba(139,92,246,0.3)] hover:shadow-[0_0_40px_rgba(139,92,246,0.5)] group overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                <span className="absolute inset-0 bg-white/20 transform -skew-x-12 -translate-x-full group-hover:translate-x-full transition-transform duration-700"></span>
                <span className="relative flex items-center gap-2">
                  <Sparkles size={18} className="group-hover:rotate-12 transition-transform" />
                  {isAnalyzing ? 'Analyzing...' : 'Run New Analysis'}
                  {!isAnalyzing && <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />}
                </span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 p-8">
        <div className="max-w-7xl mx-auto space-y-8">
          
          {/* X-Score Hero */}
          <div 
            className="bg-gradient-to-br from-purple-900/40 via-indigo-900/30 to-[#13131A] border border-purple-500/30 rounded-3xl p-12 relative overflow-hidden"
            style={{ animation: 'scaleIn 0.8s ease-out' }}
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl"></div>
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl"></div>
            
            <div className="relative z-10 text-center">
              <CircularProgress score={latestAnalysis.x_score} />
              <div className="mt-6 space-y-2">
                <div className="flex items-center justify-center gap-2 text-emerald-400">
                  <TrendingUp size={20} />
                  <span className="font-semibold">
                    {latestAnalysis.score_change > 0 ? '+' : ''}{latestAnalysis.score_change.toFixed(1)}% from last week
                  </span>
                </div>
                <p className="text-slate-400 text-lg">
                  Growing faster than <span className="text-white font-bold">{latestAnalysis.percentile}%</span> of accounts at your level
                </p>
              </div>
            </div>
          </div>

          {/* Performance Radar + Peers */}
          <div className="grid lg:grid-cols-3 gap-8">
            
            {/* Performance Radar */}
            <div 
              className="lg:col-span-2 bg-[#13131A] border border-white/5 rounded-2xl p-8 hover:border-purple-500/30 transition-all"
              style={{ animation: 'slideUp 0.6s ease-out 0.2s both' }}
            >
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-2xl font-bold flex items-center gap-3">
                    <Target className="text-purple-400" size={28} />
                    Performance Matrix
                  </h3>
                  <p className="text-slate-400 text-sm mt-1">See where you shine and where to improve</p>
                </div>
                <div className="flex gap-4 text-xs">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-purple-500 shadow-[0_0_8px_#a855f7]"></div>
                    <span>You</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-slate-600"></div>
                    <span>Top Peers</span>
                  </div>
                </div>
              </div>

              <div className="h-[400px] w-full">
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

              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-white/5">
                <div className="text-center">
                  <div className="text-2xl font-bold text-emerald-400">
                    {latestAnalysis.performance_metrics.filter(m => m.you > m.peers).length}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">Strengths</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-amber-400">
                    {latestAnalysis.performance_metrics.filter(m => m.you < m.peers).length}
                  </div>
                  <div className="text-xs text-slate-500 mt-1">To Improve</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">{latestAnalysis.insights.length}</div>
                  <div className="text-xs text-slate-500 mt-1">Insights</div>
                </div>
              </div>
            </div>

            {/* Top Peers */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <Users className="text-indigo-400" size={24} />
                  Top Peers
                </h3>
              </div>
              <p className="text-slate-400 text-sm">Accounts crushing it at your level</p>
              
              <div className="space-y-3 mt-4">
                {latestAnalysis.top_peers.map((peer, index) => (
                  <PeerCard key={peer.id} peer={peer} index={index} />
                ))}
              </div>

              {/* Upgrade Prompt */}
              <div className="mt-6 p-4 rounded-xl bg-gradient-to-br from-amber-500/10 to-purple-500/10 border border-amber-500/20 hover:border-amber-500/40 transition-all cursor-pointer group">
                <div className="flex items-center gap-3">
                  <Crown className="text-amber-400" size={24} />
                  <div>
                    <p className="font-semibold text-sm">Unlock 50+ More Peers</p>
                    <p className="text-xs text-slate-400">Upgrade to Pro</p>
                  </div>
                  <ChevronRight className="ml-auto text-slate-500 group-hover:text-amber-400 group-hover:translate-x-1 transition-all" size={20} />
                </div>
              </div>
            </div>
          </div>

          {/* AI Insights */}
          <div>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold flex items-center gap-3">
                  <Sparkles className="text-amber-400" size={28} />
                  AI Growth Insights
                </h3>
                <p className="text-slate-400 text-sm mt-1">Personalized tactics from your top-performing peers</p>
              </div>
              <div className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-xs font-bold text-indigo-400 animate-pulse">
                Powered by Grok AI
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              {latestAnalysis.insights.map((insight, index) => (
                <InsightCard key={index} insight={insight} index={index} />
              ))}
            </div>
          </div>

          {/* Recent Analyses */}
          <div 
            className="bg-[#13131A] border border-white/5 rounded-2xl p-8"
            style={{ animation: 'slideUp 0.6s ease-out 0.6s both' }}
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold flex items-center gap-3">
                <Clock className="text-slate-400" size={24} />
                Recent Analyses
              </h3>
            </div>

            <div className="space-y-1">
              {analysisHistory.map((analysis, index) => (
                <div 
                  key={analysis.id} 
                  className="flex items-center justify-between p-4 hover:bg-white/5 rounded-xl transition-all cursor-pointer group"
                  style={{ animation: `fadeIn 0.4s ease-out ${0.8 + index * 0.1}s both` }}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                      <BarChart3 className="text-purple-400" size={20} />
                    </div>
                    <div>
                      <p className="font-medium">Analysis</p>
                      <p className="text-sm text-slate-500">
                        {formatDate(analysis.created_at)} • {analysis.credits_used} credits
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="text-xs text-slate-500">Score</div>
                      <div className="text-lg font-bold text-purple-400">{analysis.x_score.toFixed(1)}</div>
                    </div>
                    <ChevronRight className="text-slate-500 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" size={20} />
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </main>

      {/* Global Styles */}
      <style jsx global>{`
        @keyframes slideUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideRight {
          from { opacity: 0; transform: translateX(-20px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes scaleIn {
          from { opacity: 0; transform: scale(0.95); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.1; }
          50% { opacity: 0.2; }
        }
        .animate-pulse-slow {
          animation: pulse-slow 4s ease-in-out infinite;
        }
        .animate-fadeIn {
          animation: fadeIn 0.6s ease-out;
        }
      `}</style>
    </div>
  );
}