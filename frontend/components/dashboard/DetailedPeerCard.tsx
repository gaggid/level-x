// frontend/components/dashboard/DetailedPeerCard.tsx
'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, Zap, TrendingUp, Users } from 'lucide-react';

interface DetailedPeerCardProps {
  peer: {
    handle: string;
    name: string;
    avatar_url?: string | null;
    followers_count: number;
    growth_rate: number;
    peer_insights?: {
      unique_characteristics: string[];
      what_they_do_differently: Array<{
        category: string;
        user_approach: string;
        peer_approach: string;
        impact: string;
        example?: string;
      }>;
      tactical_insights: Array<{
        tactic: string;
        how_they_do_it: string;
        why_it_works: string;
        how_to_copy: string;
        expected_result: string;
      }>;
      example_tweets?: Array<{
        text: string;
        public_metrics: {
          like_count: number;
          retweet_count: number;
        };
      }>;
    };
  };
}

export function DetailedPeerCard({ peer }: DetailedPeerCardProps) {
  const [expanded, setExpanded] = useState(false);
  const cleanHandle = peer.handle.replace('@', '');
  const insights = peer.peer_insights;

  return (
    <div className="bg-[#1A1A24] border border-white/5 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-4">
            <a 
              href={`https://x.com/${cleanHandle}`}
              target="_blank"
              rel="noopener noreferrer"
              className="hover:opacity-80 transition-opacity"
            >
              {peer.avatar_url ? (
                <img 
                  src={peer.avatar_url} 
                  alt={peer.name}
                  className="w-16 h-16 rounded-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const fallback = target.nextElementSibling;
                    if (fallback) {
                      (fallback as HTMLElement).classList.remove('hidden');
                    }
                  }}
                />
              ) : null}
              <div className={peer.avatar_url ? 'hidden' : 'w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-lg font-bold'}>
                {peer.name.slice(0, 2).toUpperCase()}
              </div>
            </a>
            <div>
              <h3 className="text-xl font-bold">{peer.name}</h3>
              <a 
                href={`https://x.com/${cleanHandle}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-slate-400 hover:text-purple-400 transition-colors flex items-center gap-1"
              >
                {peer.handle}
                <ExternalLink size={14} />
              </a>
              <div className="flex items-center gap-4 mt-2 text-sm">
                <span className="text-slate-400">
                  {peer.followers_count.toLocaleString()} followers
                </span>
                <span className="text-emerald-400 font-semibold">
                  +{peer.growth_rate}%/mo
                </span>
              </div>
            </div>
          </div>
          
          {insights && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-purple-400 hover:text-purple-300 transition-colors flex items-center gap-2"
            >
              {expanded ? 'Hide Details' : 'Show Details'}
              {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
            </button>
          )}
        </div>

        {/* Unique Characteristics - Always Visible */}
        {insights && insights.unique_characteristics && insights.unique_characteristics.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-semibold text-purple-400 mb-2">✨ What Makes Them Stand Out:</h4>
            <ul className="space-y-1">
              {insights.unique_characteristics.slice(0, 3).map((char, i) => (
                <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                  <span className="text-purple-400 mt-1">•</span>
                  <span>{char}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {!insights && (
          <div className="text-center py-4 text-slate-500 text-sm">
            <p>Detailed insights will be generated in the next analysis</p>
          </div>
        )}
      </div>

      {/* Expanded Details */}
      {expanded && insights && (
        <div className="border-t border-white/5 p-6 space-y-6 bg-black/20">
          {/* What They Do Differently */}
          {insights.what_they_do_differently && insights.what_they_do_differently.length > 0 && (
            <div>
              <h4 className="text-lg font-bold mb-3 flex items-center gap-2">
                <TrendingUp className="text-amber-400" size={20} />
                What They Do Differently
              </h4>
              <div className="space-y-4">
                {insights.what_they_do_differently.map((diff, i) => (
                  <div key={i} className="bg-[#13131A] rounded-lg p-4">
                    <h5 className="font-semibold text-purple-400 mb-2">{diff.category}</h5>
                    <div className="grid grid-cols-2 gap-4 text-sm mb-2">
                      <div>
                        <p className="text-slate-500 text-xs mb-1">You:</p>
                        <p className="text-slate-300">{diff.user_approach}</p>
                      </div>
                      <div>
                        <p className="text-slate-500 text-xs mb-1">Them:</p>
                        <p className="text-emerald-400">{diff.peer_approach}</p>
                      </div>
                    </div>
                    <p className="text-amber-400 text-sm font-semibold">📊 {diff.impact}</p>
                    {diff.example && (
                      <p className="text-slate-400 text-xs mt-2 italic">{diff.example}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tactical Insights */}
          {insights.tactical_insights && insights.tactical_insights.length > 0 && (
            <div>
              <h4 className="text-lg font-bold mb-3 flex items-center gap-2">
                <Zap className="text-yellow-400" size={20} />
                Tactics You Can Copy
              </h4>
              <div className="space-y-4">
                {insights.tactical_insights.map((tactic, i) => (
                  <div key={i} className="bg-[#13131A] rounded-lg p-4 border border-purple-500/20">
                    <h5 className="font-bold text-white mb-2">{tactic.tactic}</h5>
                    <div className="space-y-2 text-sm">
                      <div>
                        <span className="text-purple-400 font-semibold">How: </span>
                        <span className="text-slate-300">{tactic.how_they_do_it}</span>
                      </div>
                      <div>
                        <span className="text-emerald-400 font-semibold">Why it works: </span>
                        <span className="text-slate-300">{tactic.why_it_works}</span>
                      </div>
                      <div className="bg-purple-500/10 p-2 rounded">
                        <span className="text-purple-400 font-semibold">⚡ Action: </span>
                        <span className="text-white">{tactic.how_to_copy}</span>
                      </div>
                      <div>
                        <span className="text-amber-400 font-semibold">Expected: </span>
                        <span className="text-slate-300">{tactic.expected_result}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Example Tweets */}
          {insights.example_tweets && insights.example_tweets.length > 0 && (
            <div>
              <h4 className="text-lg font-bold mb-3">📝 Example Tweets</h4>
              <div className="space-y-3">
                {insights.example_tweets.slice(0, 3).map((tweet, i) => (
                  <div key={i} className="bg-[#13131A] rounded-lg p-4 border border-white/5">
                    <p className="text-slate-300 text-sm mb-2">{tweet.text}</p>
                    <div className="flex gap-4 text-xs text-slate-500">
                      <span>❤️ {tweet.public_metrics.like_count.toLocaleString()} likes</span>
                      <span>🔄 {tweet.public_metrics.retweet_count.toLocaleString()} retweets</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}