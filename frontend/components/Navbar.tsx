"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAppStore } from '@/lib/store';
import { 
  Menu, 
  X, 
  Upload, 
  Target, 
  Sparkles, 
  LayoutDashboard, 
  UserCheck 
} from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();
  const { state } = useAppStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { name: 'Upload', href: '/', icon: Upload },
    { name: 'Score Match', href: '/score', icon: Target },
    { name: 'Improve CV', href: '/improve', icon: Sparkles },
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  ];

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  return (
    <nav className="glass-nav sticky top-0 z-50 w-full">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex-shrink-0 flex items-center gap-2">
            <Link 
              href="/" 
              className="text-xl font-black tracking-tight text-[var(--text-primary)] hover:opacity-80 transition-opacity"
            >
              CV Platform
            </Link>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.href);
              
              let targetHref = item.href;
              if (state.candidateId && (item.href === '/score' || item.href === '/improve')) {
                const params = new URLSearchParams();
                params.append('candidate_id', state.candidateId);
                if (state.jobId) {
                  params.append('job_id', state.jobId);
                }
                targetHref = `${item.href}?${params.toString()}`;
              }

              return (
                <Link
                  key={item.name}
                  href={targetHref}
                  className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold tracking-wide transition-all rounded-xl ${
                    active
                      ? 'text-[var(--text-primary)] bg-black/[0.06]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/[0.04]'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.name}
                </Link>
              );
            })}
          </div>

          {/* Active Candidate Pill */}
          <div className="hidden lg:flex items-center gap-2">
            {state.candidateName && (
              <div className="glass-badge text-xs px-3 py-1.5 flex items-center gap-1.5 select-none">
                <UserCheck className="w-3.5 h-3.5" />
                <span className="font-bold">Active:</span> {state.candidateName.split(' ')[0]}
              </div>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/[0.04] focus:outline-none transition-colors"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Panel */}
      {mobileMenuOpen && (
        <div className="md:hidden animate-slideDown border-t border-black/[0.04] bg-white/80 backdrop-blur-xl px-3 pt-2 pb-4 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            let targetHref = item.href;
            if (state.candidateId && (item.href === '/score' || item.href === '/improve')) {
              const params = new URLSearchParams();
              params.append('candidate_id', state.candidateId);
              if (state.jobId) {
                params.append('job_id', state.jobId);
              }
              targetHref = `${item.href}?${params.toString()}`;
            }

            return (
              <Link
                key={item.name}
                href={targetHref}
                onClick={() => setMobileMenuOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                  active
                    ? 'text-[var(--text-primary)] bg-black/[0.06]'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-black/[0.03]'
                }`}
              >
                <Icon className="w-4 h-4" />
                {item.name}
              </Link>
            );
          })}

          {state.candidateName && (
            <div className="px-4 py-3 border-t border-black/[0.04] mt-2">
              <div className="glass-badge text-xs w-full justify-center py-1.5 flex items-center gap-1.5 select-none">
                <UserCheck className="w-3.5 h-3.5" />
                Active: {state.candidateName}
              </div>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}
