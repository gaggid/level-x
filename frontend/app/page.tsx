// app/page.tsx
'use client';

import React, { useState } from 'react';
import { 
  ArrowRight, 
  BarChart3, 
  Users, 
  Lightbulb, 
  Zap,
  TrendingUp,
  Target,
  Sparkles,
  ChevronRight,
  Check,
  X as XIcon
} from 'lucide-react';
import Link from 'next/link';

export default function Home() {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('signup');

  return (
    <div className="min-h-screen bg-[#0B0B0F] text-white overflow-hidden">
      {/* Ambient Background Effects */}
      <div className="fixed top-0 left-0 w-full h-full pointer-events-none">
        <div className="absolute top-[-10%] left-[10%] w-[600px] h-[600px] bg-purple-600/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[5%] w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[100px]" />
      </div>

      {/* Navigation */}
      <nav className="relative z-50 flex justify-between items-center px-8 py-6 border-b border-white/5 backdrop-blur-xl">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-500 to-purple-400 flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.4)]">
            <span className="font-black text-white text-xl">X</span>
          </div>
          <span className="font-bold text-xl">Level<span className="text-purple-400">X</span></span>
        </div>
        
        <div className="flex items-center gap-6">
          <Link href="#features" className="text-slate-400 hover:text-white transition-colors">Features</Link>
          <Link href="#how-it-works" className="text-slate-400 hover:text-white transition-colors">How It Works</Link>
          <Link href="#pricing" className="text-slate-400 hover:text-white transition-colors">Pricing</Link>
          <button 
            onClick={() => { setAuthMode('login'); setShowAuthModal(true); }}
            className="text-slate-400 hover:text-white transition-colors"
          >
            Login
          </button>
          <button 
            onClick={() => { setAuthMode('signup'); setShowAuthModal(true); }}
            className="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-lg font-semibold transition-all hover:scale-105"
          >
            Get Started
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative z-10 px-8 py-20 text-center max-w-6xl mx-auto">
        <div className="inline-block mb-6 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20">
          <span className="text-purple-400 text-sm font-medium">✨ AI-Powered Growth Intelligence</span>
        </div>
        
        <h1 className="text-6xl md:text-7xl font-black mb-6 leading-tight">
          Grow Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400">X Account</span> Faster
        </h1>
        
        <p className="text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
          See exactly how accounts at your follower level are out-growing you—and copy what works. 
          Powered by AI insights from your top-performing peers.
        </p>

        <div className="flex gap-4 justify-center mb-16">
          <button 
            onClick={() => { setAuthMode('signup'); setShowAuthModal(true); }}
            className="group bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 px-8 py-4 rounded-xl font-bold text-lg transition-all hover:scale-105 shadow-[0_0_30px_rgba(139,92,246,0.3)] flex items-center gap-2"
          >
            Start Growing Free
            <ArrowRight className="group-hover:translate-x-1 transition-transform" size={20} />
          </button>
          <button 
            onClick={() => document.getElementById('demo')?.scrollIntoView({ behavior: 'smooth' })}
            className="px-8 py-4 rounded-xl font-bold text-lg border border-white/10 hover:bg-white/5 transition-all"
          >
            Watch Demo
          </button>
        </div>

        {/* Hero Visual - Dashboard Preview */}
        <div id="demo" className="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl backdrop-blur-xl bg-[#13131A]/50 p-4">
          <img 
            src="/api/placeholder/1200/700" 
            alt="Dashboard Preview"
            className="w-full rounded-xl"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-[#0B0B0F] via-transparent to-transparent pointer-events-none" />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative z-10 px-8 py-20 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Everything You Need to Grow</h2>
          <p className="text-slate-400 text-lg">Data-driven insights that actually work</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <FeatureCard
            icon={<TrendingUp className="text-purple-400" size={28} />}
            title="Growth Score"
            description="Track your X growth with a real-time score that benchmarks you against similar accounts"
          />
          <FeatureCard
            icon={<Users className="text-indigo-400" size={28} />}
            title="Peer Matching"
            description="AI finds 5-10 accounts at your level that are growing faster—see exactly who to learn from"
          />
          <FeatureCard
            icon={<Lightbulb className="text-amber-400" size={28} />}
            title="Actionable Insights"
            description="Get 3 specific tactics you can implement today based on what's working for your peers"
          />
          <FeatureCard
            icon={<Target className="text-emerald-400" size={28} />}
            title="Content Analysis"
            description="Understand what content types, posting times, and engagement tactics drive growth"
          />
          <FeatureCard
            icon={<BarChart3 className="text-blue-400" size={28} />}
            title="Performance Radar"
            description="Visual comparison across 6 key metrics: engagement, velocity, virality, consistency, and more"
          />
          <FeatureCard
            icon={<Sparkles className="text-pink-400" size={28} />}
            title="AI Strategy Generator"
            description="Let AI create a personalized 30-day growth plan based on your unique profile"
          />
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="relative z-10 px-8 py-20 bg-gradient-to-b from-transparent via-purple-900/5 to-transparent">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-4">How LevelX Works</h2>
            <p className="text-slate-400 text-lg">From connection to growth in 3 simple steps</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <StepCard
              number="1"
              title="Connect"
              description="Link your X account securely with OAuth 2.0. We only need read access—never post without permission."
            />
            <StepCard
              number="2"
              title="Analyze"
              description="Our AI analyzes your profile, content style, and finds peers at your level who are crushing it."
            />
            <StepCard
              number="3"
              title="Grow"
              description="Get specific, actionable insights. Implement what works. Watch your growth accelerate."
            />
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="relative z-10 px-8 py-20 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Simple, Transparent Pricing</h2>
          <p className="text-slate-400 text-lg">Credits that never expire. No subscriptions required.</p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <PricingCard
            name="Starter"
            price="$0"
            description="Try before you buy"
            credits="20 credits (one-time)"
            features={[
              "1-2 analyses",
              "Basic insights",
              "3 peer matches",
              "7-day data cache"
            ]}
            cta="Get Started"
            onClick={() => { setAuthMode('signup'); setShowAuthModal(true); }}
          />
          <PricingCard
            name="Level X+"
            price="$29"
            description="For serious creators"
            credits="100 credits/month"
            features={[
              "~6 analyses per month",
              "Deep insights",
              "5 peer matches",
              "Weekly reports",
              "Email support",
              "Credits roll over (1 month)"
            ]}
            cta="Upgrade"
            popular={true}
            onClick={() => { setAuthMode('signup'); setShowAuthModal(true); }}
          />
          <PricingCard
            name="Level X Pro"
            price="$79"
            description="For professionals"
            credits="300 credits/month"
            features={[
              "~20 analyses per month",
              "Advanced insights",
              "8 peer matches",
              "Daily reports",
              "Priority support (24h)",
              "Competitor tracking",
              "Credits roll over (3 months)"
            ]}
            cta="Contact Sales"
            onClick={() => { setAuthMode('signup'); setShowAuthModal(true); }}
          />
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative z-10 px-8 py-20">
        <div className="max-w-4xl mx-auto text-center rounded-3xl bg-gradient-to-r from-purple-600/20 to-indigo-600/20 border border-purple-500/30 p-12">
          <h2 className="text-4xl font-bold mb-4">Ready to Level Up Your X Game?</h2>
          <p className="text-slate-300 text-lg mb-8">Join thousands of creators already growing faster with LevelX</p>
          <button 
            onClick={() => { setAuthMode('signup'); setShowAuthModal(true); }}
            className="bg-white text-black px-8 py-4 rounded-xl font-bold text-lg hover:bg-slate-100 transition-all hover:scale-105"
          >
            Start Free Analysis
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/5 px-8 py-8">
        <div className="max-w-6xl mx-auto flex justify-between items-center text-sm text-slate-500">
          <div>© 2025 LevelX. All rights reserved.</div>
          <div className="flex gap-6">
            <Link href="/privacy" className="hover:text-slate-300">Privacy</Link>
            <Link href="/terms" className="hover:text-slate-300">Terms</Link>
            <Link href="/contact" className="hover:text-slate-300">Contact</Link>
          </div>
        </div>
      </footer>

      {/* Auth Modal */}
      {showAuthModal && (
        <AuthModal 
          mode={authMode} 
          onClose={() => setShowAuthModal(false)}
          onSwitchMode={() => setAuthMode(authMode === 'login' ? 'signup' : 'login')}
        />
      )}
    </div>
  );
}

// Feature Card Component
function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="group p-6 rounded-2xl bg-[#13131A] border border-white/5 hover:border-purple-500/30 transition-all hover:-translate-y-1">
      <div className="w-14 h-14 rounded-xl bg-white/5 flex items-center justify-center mb-4 group-hover:bg-purple-500/10 transition-colors">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}

// Step Card Component
function StepCard({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="relative text-center">
      <div className="inline-block w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-4xl font-black mb-6 shadow-[0_0_30px_rgba(139,92,246,0.3)]">
        {number}
      </div>
      <h3 className="text-2xl font-bold mb-3">{title}</h3>
      <p className="text-slate-400 leading-relaxed">{description}</p>
    </div>
  );
}

// Pricing Card Component
function PricingCard({ 
  name, 
  price, 
  description, 
  credits, 
  features, 
  cta, 
  popular = false,
  onClick
}: { 
  name: string; 
  price: string; 
  description: string; 
  credits: string; 
  features: string[]; 
  cta: string; 
  popular?: boolean;
  onClick: () => void;
}) {
  return (
    <div className={`relative p-8 rounded-2xl ${popular ? 'bg-gradient-to-b from-purple-900/40 to-[#13131A] border-2 border-purple-500' : 'bg-[#13131A] border border-white/5'}`}>
      {popular && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-purple-500 text-xs font-bold uppercase">
          Most Popular
        </div>
      )}
      <div className="mb-6">
        <h3 className="text-2xl font-bold mb-2">{name}</h3>
        <p className="text-slate-400 text-sm mb-4">{description}</p>
        <div className="flex items-baseline gap-2">
          <span className="text-5xl font-black">{price}</span>
          {price !== "$0" && <span className="text-slate-500">/month</span>}
        </div>
        <p className="text-purple-400 text-sm mt-2 font-medium">{credits}</p>
      </div>
      
      <button 
        onClick={onClick}
        className={`w-full py-3 rounded-xl font-bold mb-6 transition-all ${popular ? 'bg-purple-600 hover:bg-purple-700' : 'bg-white/5 hover:bg-white/10 border border-white/10'}`}
      >
        {cta}
      </button>

      <ul className="space-y-3">
        {features.map((feature, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
            <Check className="text-purple-400 flex-shrink-0 mt-0.5" size={16} />
            {feature}
          </li>
        ))}
      </ul>
    </div>
  );
}

// Auth Modal Component
function AuthModal({ mode, onClose, onSwitchMode }: { mode: 'login' | 'signup'; onClose: () => void; onSwitchMode: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-md bg-[#13131A] rounded-2xl border border-white/10 p-8">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white"
        >
          <XIcon size={24} />
        </button>

        <h2 className="text-3xl font-bold mb-2">{mode === 'login' ? 'Welcome Back' : 'Get Started Free'}</h2>
        <p className="text-slate-400 mb-8">{mode === 'login' ? 'Log in to continue growing' : 'Create your account in seconds'}</p>

        <button className="w-full bg-white text-black py-3 rounded-xl font-bold flex items-center justify-center gap-3 hover:bg-slate-100 transition-colors mb-6">
          <XIcon size={20} />
          Continue with X
        </button>

        <div className="text-center text-sm text-slate-400">
          {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
          <button onClick={onSwitchMode} className="text-purple-400 hover:text-purple-300 font-medium">
            {mode === 'login' ? 'Sign up' : 'Log in'}
          </button>
        </div>
      </div>
    </div>
  );
}