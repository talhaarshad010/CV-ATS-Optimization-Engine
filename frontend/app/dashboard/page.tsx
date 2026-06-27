"use client";

import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  UserCheck, 
  Briefcase, 
  Database, 
  Sparkles, 
  Calendar, 
  ChevronRight,
  TrendingUp,
  RefreshCw,
  Clock
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getDashboardStats, DashboardStatsResponse } from '@/lib/api';
import { useAppStore } from '@/lib/store';

export default function DashboardPage() {
  const { setCandidateId, setCandidateName } = useAppStore();
  const [stats, setStats] = useState<DashboardStatsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDashboardStats();
      setStats(data);
    } catch (err: any) {
      console.error(err);
      setError("Failed to fetch dashboard data from server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleSelectCandidate = (candidateId: string, candidateName: string) => {
    setCandidateId(candidateId);
    setCandidateName(candidateName);
    window.location.href = `/score?candidate_id=${candidateId}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <RefreshCw className="w-8 h-8 text-[var(--text-tertiary)] animate-spin" />
        <span className="text-sm text-[var(--text-secondary)] font-mono">Loading dashboard metrics...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div className="p-4 rounded-2xl bg-red-50 border border-red-200 text-red-600 text-sm max-w-md text-center">
          {error}
        </div>
        <Button onClick={fetchStats} className="btn-secondary rounded-xl">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <main className="min-h-screen py-12 px-4 md:px-8">
      <div className="max-w-6xl w-full mx-auto space-y-8 z-10 relative animate-fadeInUp">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <h1 className="text-3xl font-black tracking-tight text-[var(--text-primary)]">
              CV Platform Analytics
            </h1>
            <p className="text-[var(--text-secondary)] text-sm">
              Overview of parsed resumes, skill metrics, and ATS matching histories.
            </p>
          </div>
          <Button onClick={fetchStats} className="btn-secondary rounded-xl">
            <RefreshCw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 stagger-children">
          {/* Card 1 */}
          <div className="glass-card-solid p-6 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">Parsed Candidates</span>
              <h3 className="text-3xl font-black text-[var(--text-primary)]">{stats?.total_candidates || 0}</h3>
            </div>
            <div className="p-3 rounded-2xl bg-black/[0.04] text-[var(--text-secondary)]">
              <UserCheck className="w-6 h-6" />
            </div>
          </div>

          {/* Card 2 */}
          <div className="glass-card-solid p-6 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">Job Matches Evaluated</span>
              <h3 className="text-3xl font-black text-[var(--text-primary)]">{stats?.total_matches || 0}</h3>
            </div>
            <div className="p-3 rounded-2xl bg-black/[0.04] text-[var(--text-secondary)]">
              <Briefcase className="w-6 h-6" />
            </div>
          </div>

          {/* Card 3 */}
          <div className="glass-card-solid p-6 flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">Average Match Score</span>
              <h3 className="text-3xl font-black text-[var(--text-primary)]">
                {stats?.avg_score || 0}%
              </h3>
            </div>
            <div className="p-3 rounded-2xl bg-black/[0.04] text-[var(--text-secondary)]">
              <TrendingUp className="w-6 h-6" />
            </div>
          </div>
        </div>

        {/* Catalog and History */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Candidates Catalog */}
          <div className="glass-card-solid p-0 overflow-hidden">
            <div className="p-6 border-b border-black/[0.04]">
              <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                <Database className="w-4.5 h-4.5" /> Parsed Candidate Catalog
              </h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Candidates processed through extraction and normalization.
              </p>
            </div>
            <div className="p-6">
              <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                {stats?.candidates && stats.candidates.length > 0 ? (
                  stats.candidates.map((cand) => (
                    <div 
                      key={cand.id} 
                      onClick={() => handleSelectCandidate(cand.id, cand.candidate_name || "Unnamed")}
                      className="p-4 rounded-2xl bg-white/40 border border-black/[0.04] hover:border-black/[0.1] hover:bg-white/60 transition-all flex items-center justify-between gap-4 cursor-pointer group"
                    >
                      <div className="space-y-1">
                        <h4 className="text-sm font-bold text-[var(--text-primary)] group-hover:text-black transition-colors">
                          {cand.candidate_name || "Unnamed Candidate"}
                        </h4>
                        <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)] font-mono">
                          <span>{cand.email || "No Email"}</span>
                          <span>•</span>
                          <span>{cand.total_experience_years ? `${cand.total_experience_years} Yrs Exp` : "No Exp Data"}</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="glass-badge text-[10px] px-2 py-0.5">
                          {cand.status}
                        </span>
                        <ChevronRight className="w-4 h-4 text-[var(--text-tertiary)] group-hover:text-[var(--text-primary)] transition-colors" />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-[var(--text-tertiary)] text-sm italic">
                    No candidates parsed yet.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Match Activity History */}
          <div className="glass-card-solid p-0 overflow-hidden">
            <div className="p-6 border-b border-black/[0.04]">
              <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                <BarChart3 className="w-4.5 h-4.5" /> Match Evaluation History
              </h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                History of calculated ATS job description matches.
              </p>
            </div>
            <div className="p-6">
              <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
                {stats?.activity_feed && stats.activity_feed.length > 0 ? (
                  stats.activity_feed.map((act) => (
                    <div 
                      key={act.score_id} 
                      onClick={() => handleSelectCandidate(act.candidate_id, act.candidate_name)}
                      className="p-4 rounded-2xl bg-white/40 border border-black/[0.04] hover:border-black/[0.1] hover:bg-white/60 transition-all flex items-center justify-between gap-4 cursor-pointer group"
                    >
                      <div className="space-y-1">
                        <h4 className="text-sm font-bold text-[var(--text-primary)] group-hover:text-black transition-colors truncate max-w-[240px]">
                          {act.candidate_name}
                        </h4>
                        <div className="flex items-center gap-2 text-xs text-[var(--text-tertiary)]">
                          <span className="font-semibold text-[var(--text-secondary)]">{act.job_title}</span>
                          <span>•</span>
                          <span className="font-mono flex items-center gap-1">
                            <Clock className="w-3 h-3" /> {new Date(act.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <span className="block text-sm font-extrabold text-[var(--text-primary)]">{act.ats_score}%</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-bold ${
                            act.ats_score >= 80 ? "bg-green-50 text-green-700 border border-green-200" :
                            act.ats_score >= 60 ? "bg-amber-50 text-amber-700 border border-amber-200" :
                            "bg-red-50 text-red-700 border border-red-200"
                          }`}>
                            Grade {act.grade}
                          </span>
                        </div>
                        <ChevronRight className="w-4 h-4 text-[var(--text-tertiary)] group-hover:text-[var(--text-primary)] transition-colors" />
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-12 text-[var(--text-tertiary)] text-sm italic">
                    No matching runs calculated yet.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
