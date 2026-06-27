"use client";

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { 
  ArrowLeft, 
  Sparkles, 
  RefreshCw, 
  AlertCircle, 
  Copy, 
  Check, 
  Send, 
  Download, 
  BookOpen, 
  MessageSquare, 
  FileText,
  Bookmark,
  Award
} from 'lucide-react';

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

import { 
  parseCV, 
  getSkillGaps, 
  rewriteBullets, 
  askChat, 
  getFullReport,
  ParseResponse,
  RewriteResponse,
  SkillGapsResponse,
  ChatResponse
} from '@/lib/api';
import { useAppStore } from '@/lib/store';

interface ChatMessage {
  sender: 'user' | 'bot';
  text: string;
}

function ImprovePageContent() {
  const searchParams = useSearchParams();
  const candidateIdParam = searchParams.get('candidate_id');
  const jobIdParam = searchParams.get('job_id');

  const { state: storeState, setCandidateId: setStoreCandidateId, setCandidateName: setStoreCandidateName, setJobId: setStoreJobId } = useAppStore();

  const [candidateId, setCandidateId] = useState<string>('');
  const [jobId, setJobId] = useState<string>('');
  const [candidateInfo, setCandidateInfo] = useState<ParseResponse | null>(null);

  const [activeTab, setActiveTab] = useState<'rewrite' | 'gaps' | 'chat'>('rewrite');

  const [targetTitle, setTargetTitle] = useState<string>('Software Engineer');
  const [bulletsData, setBulletsData] = useState<RewriteResponse | null>(null);
  const [loadingRewrite, setLoadingRewrite] = useState<boolean>(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const [gapsData, setGapsData] = useState<SkillGapsResponse | null>(null);
  const [loadingGaps, setLoadingGaps] = useState<boolean>(false);

  const [chatInput, setChatInput] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { 
      sender: 'bot', 
      text: "Hello! I am your AI Career Assistant. Ask me anything about your ATS score match, missing skills, or advice on how to improve your CV summary." 
    }
  ]);
  const [loadingChat, setLoadingChat] = useState<boolean>(false);

  const [loadingProfile, setLoadingProfile] = useState<boolean>(false);
  const [loadingReport, setLoadingReport] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const cid = candidateIdParam || storeState.candidateId || '';
    const jid = jobIdParam || storeState.jobId || '';
    setCandidateId(cid);
    setJobId(jid);

    if (cid && !candidateInfo) {
      setLoadingProfile(true);
      parseCV(cid)
        .then(data => {
          setCandidateInfo(data);
          setStoreCandidateId(data.candidate_id);
          setStoreCandidateName(data.name);
          if (jid) setStoreJobId(jid);
        })
        .catch(err => console.error(err))
        .finally(() => setLoadingProfile(false));
    }
  }, [candidateIdParam, jobIdParam, storeState.candidateId, storeState.jobId, candidateInfo, setStoreCandidateId, setStoreCandidateName, setStoreJobId]);

  const handleLoadProfile = async () => {
    if (!candidateId.trim()) return;
    setLoadingProfile(true);
    setError(null);
    try {
      const data = await parseCV(candidateId.trim());
      setCandidateInfo(data);
      setStoreCandidateId(data.candidate_id);
      setStoreCandidateName(data.name);
      if (jobId.trim()) setStoreJobId(jobId.trim());
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to load candidate profile. Verify candidate ID.');
      setCandidateInfo(null);
    } finally {
      setLoadingProfile(false);
    }
  };

  const handleRewrite = async () => {
    const activeId = candidateInfo?.candidate_id || candidateId;
    if (!activeId.trim()) return;
    setLoadingRewrite(true);
    setError(null);
    setBulletsData(null);
    try {
      const data = await rewriteBullets(activeId.trim(), targetTitle);
      setBulletsData(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to rewrite bullets with Llama 3.1.');
    } finally {
      setLoadingRewrite(false);
    }
  };

  const handleLoadGaps = useCallback(async () => {
    const activeId = candidateInfo?.candidate_id || candidateId;
    if (!activeId.trim() || !jobId.trim()) return;
    setLoadingGaps(true);
    setError(null);
    try {
      const data = await getSkillGaps(activeId.trim(), jobId.trim());
      setGapsData(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to analyze skill gaps.');
    } finally {
      setLoadingGaps(false);
    }
  }, [candidateInfo, candidateId, jobId]);

  useEffect(() => {
    if (activeTab === 'gaps' && !gapsData) {
      handleLoadGaps();
    }
  }, [activeTab, gapsData, handleLoadGaps]);

  const handleSendChat = async (textToSend?: string) => {
    const query = textToSend || chatInput;
    if (!query.trim()) return;

    const activeId = candidateInfo?.candidate_id || candidateId;
    setChatMessages(prev => [...prev, { sender: 'user', text: query }]);
    if (!textToSend) setChatInput('');
    
    setLoadingChat(true);
    try {
      const response = await askChat(query, activeId || undefined);
      setChatMessages(prev => [...prev, { sender: 'bot', text: response.answer }]);
    } catch (err: any) {
      console.error(err);
      setChatMessages(prev => [...prev, { 
        sender: 'bot', 
        text: 'Sorry, I encountered an error communicating with local Llama 3.1.' 
      }]);
    } finally {
      setLoadingChat(false);
    }
  };

  const handleCopy = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleDownloadReport = async () => {
    const activeId = candidateInfo?.candidate_id || candidateId;
    if (!activeId.trim() || !jobId.trim()) {
      setError('Both Candidate ID and Job ID are required to download a report.');
      return;
    }

    setLoadingReport(true);
    setError(null);
    try {
      const report = await getFullReport(activeId.trim(), jobId.trim());
      
      const textContent = `===========================================================
                 ATS SCORE ANALYSIS REPORT
===========================================================
Candidate ID  : ${report.candidate_id}
Job ID        : ${report.job_id}
Target Role   : ${report.job_title.toUpperCase()}
ATS Match Score: ${report.ats_score}/100 (${report.grade} Grade)
Generated On  : ${new Date().toLocaleDateString()}

-----------------------------------------------------------
1. CRITERIA MATCH DETAILS
-----------------------------------------------------------
${Object.entries(report.breakdown || {}).map(([key, val]: [string, any]) => {
  const categoryName = key.replace('_', ' ').toUpperCase();
  return `- ${categoryName.padEnd(20)}: ${val.score}/${val.max} pts (${val.percentage}%)`;
}).join('\n')}

-----------------------------------------------------------
2. ACTIONABLE IMPROVEMENT PLAN
-----------------------------------------------------------
${report.action_plan}

-----------------------------------------------------------
3. NORMALIZED SKILL GAPS
-----------------------------------------------------------
Total Gaps: ${report.gaps_summary.total_gaps}
Estimated Study Period: ${report.gaps_summary.estimated_total_weeks} weeks

${report.skill_gaps && report.skill_gaps.length > 0 ? 
  report.skill_gaps.map((g: any, i: number) => `
[${i + 1}] Skill: ${g.skill} (${g.priority.toUpperCase()} Priority - ${g.estimated_weeks} weeks)
    - Free Study Course: ${g.suggested_course}
    - Practice Project:  ${g.suggested_project}
`).join('\n') : '- No skill gaps detected! Ideal match.'}

-----------------------------------------------------------
4. REWRITTEN WORK EXPERIENCES
-----------------------------------------------------------
${report.rewritten_bullets && report.rewritten_bullets.original_bullets && report.rewritten_bullets.original_bullets.length > 0 ?
  report.rewritten_bullets.original_bullets.map((orig: string, idx: number) => `
[${idx + 1}] ORIGINAL BULLET:
${orig}

[${idx + 1}] AI-REWRITTEN BULLET:
${report.rewritten_bullets.rewritten_bullets[idx] || 'N/A'}
`).join('\n') : '- No bullets rewritten or experience section was empty.'}

===========================================================
      Generated automatically by local Llama 3.1
===========================================================`;

      const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `ATS_Improvement_Report_${report.job_title.replace(/\s+/g, '_')}.txt`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to download report.');
    } finally {
      setLoadingReport(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'high':
        return 'bg-red-50 text-red-700 border border-red-200';
      case 'medium':
        return 'bg-amber-50 text-amber-700 border border-amber-200';
      default:
        return 'bg-green-50 text-green-700 border border-green-200';
    }
  };

  return (
    <main className="min-h-screen flex flex-col items-center py-12 px-4 md:px-8">
      <div className="max-w-5xl w-full z-10 space-y-8 animate-fadeInUp">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div className="flex justify-between items-center">
            <Button 
              variant="link" 
              onClick={() => window.location.href = `/score?candidate_id=${candidateInfo?.candidate_id || candidateId}`}
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] p-0 flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" /> Back to Match Analyzer
            </Button>
            
            {candidateId && jobId && (
              <Button
                onClick={handleDownloadReport}
                disabled={loadingReport}
                className="btn-secondary flex items-center gap-2 h-9 px-4 text-xs font-semibold rounded-xl"
              >
                {loadingReport ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Download className="w-3.5 h-3.5" />
                )}
                Download Full Report
              </Button>
            )}
          </div>

          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full glass-badge text-xs font-semibold">
              <Sparkles className="w-3.5 h-3.5" /> AI Improvement Suite
            </div>
            <h1 className="text-3xl md:text-4xl font-black tracking-tight text-[var(--text-primary)]">
              CV Optimization Engine
            </h1>
            <p className="text-[var(--text-secondary)] max-w-xl text-sm">
              Use local Llama 3.1 to rewrite bullets, bridge skill gaps, or chat directly about key CV optimizations.
            </p>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-600 text-sm animate-scaleIn">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <div className="font-medium">{error}</div>
          </div>
        )}

        {/* Profile Loader */}
        {!candidateInfo && (
          <div className="glass-card-solid p-0 overflow-hidden max-w-xl mx-auto">
            <div className="p-6 pb-4">
              <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                <Bookmark className="w-5 h-5" /> Select Candidate Profile
              </h2>
            </div>
            <div className="px-6 pb-4 space-y-4">
              <div className="space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)]">Candidate UUID</label>
                <Input 
                  placeholder="e.g. 71de1aa9-b3e1-4069-b723-b26769ddfdd8" 
                  value={candidateId}
                  onChange={(e) => setCandidateId(e.target.value)}
                  className="glass-input h-11 text-sm"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)]">Job UUID (Optional)</label>
                <Input 
                  placeholder="e.g. 88de1aa9-b3e1-4069-b723-b26769ddfdd8" 
                  value={jobId}
                  onChange={(e) => setJobId(e.target.value)}
                  className="glass-input h-11 text-sm"
                />
              </div>
            </div>
            <div className="flex justify-end border-t border-black/[0.04] px-6 py-4">
              <Button 
                onClick={handleLoadProfile}
                disabled={loadingProfile || !candidateId.trim()}
                className="btn-primary px-5 py-2 rounded-xl text-sm"
              >
                {loadingProfile ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Loading...
                  </>
                ) : 'Load Profile'}
              </Button>
            </div>
          </div>
        )}

        {/* Loading skeleton */}
        {loadingProfile && (
          <div className="glass-card-solid p-6 space-y-4 animate-fadeIn">
            <div className="flex items-center gap-3">
              <RefreshCw className="w-5 h-5 animate-spin text-[var(--text-secondary)]" />
              <span className="text-sm font-semibold text-[var(--text-secondary)]">Loading candidate profile...</span>
            </div>
            <div className="shimmer-loader h-12 rounded-xl" />
          </div>
        )}

        {/* Candidate Details */}
        {candidateInfo && (
          <div className="glass-card-solid p-0 overflow-hidden animate-scaleIn">
            <div className="flex flex-col md:flex-row md:items-center justify-between p-6 border-b border-black/[0.04]">
              <div className="space-y-1">
                <h2 className="text-xl font-bold text-[var(--text-primary)]">
                  {candidateInfo.name || 'Extracted Profile'}
                </h2>
                <div className="text-xs text-[var(--text-secondary)] flex flex-wrap gap-x-4">
                  {candidateInfo.email && <span>{candidateInfo.email}</span>}
                  {candidateInfo.location && <span>{candidateInfo.location}</span>}
                  {candidateInfo.total_experience_years !== null && (
                    <span>{candidateInfo.total_experience_years} Years Experience</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2 items-center mt-3 md:mt-0">
                <span className="glass-badge text-xs px-2.5 py-1">
                  ID: {candidateInfo.candidate_id.substring(0, 8)}...
                </span>
                {jobId && (
                  <span className="glass-badge text-xs px-2.5 py-1">
                    Job: {jobId.substring(0, 8)}...
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Workspace Tabs */}
        {candidateInfo && (
          <div className="space-y-6">
            {/* Tab Bar */}
            <div className="flex border-b border-black/[0.04] gap-6">
              <button
                onClick={() => setActiveTab('rewrite')}
                className={`pb-3 text-sm font-semibold tracking-wide transition-all border-b-2 ${
                  activeTab === 'rewrite' 
                    ? 'border-[var(--text-primary)] text-[var(--text-primary)]' 
                    : 'border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                Rewritten Bullets
              </button>
              <button
                onClick={() => setActiveTab('gaps')}
                disabled={!jobId}
                className={`pb-3 text-sm font-semibold tracking-wide transition-all border-b-2 disabled:opacity-30 disabled:cursor-not-allowed ${
                  activeTab === 'gaps' 
                    ? 'border-[var(--text-primary)] text-[var(--text-primary)]' 
                    : 'border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                Skill Gaps Learning
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`pb-3 text-sm font-semibold tracking-wide transition-all border-b-2 ${
                  activeTab === 'chat' 
                    ? 'border-[var(--text-primary)] text-[var(--text-primary)]' 
                    : 'border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                Chat Assistant
              </button>
            </div>

            {/* Tab 1: Rewritten Bullets */}
            {activeTab === 'rewrite' && (
              <div className="space-y-6 animate-fadeIn">
                <div className="glass-card-solid p-0 overflow-hidden">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 border-b border-black/[0.04]">
                    <div>
                      <h3 className="text-base font-bold text-[var(--text-primary)]">Bullet Points Optimizer</h3>
                      <p className="text-xs text-[var(--text-secondary)] mt-1">
                        Rewrites experience bullets using strong action verbs and metric placeholders.
                      </p>
                    </div>
                    <div className="flex gap-2 max-w-xs w-full sm:w-auto">
                      <Input
                        placeholder="Target Role (e.g. Django Developer)"
                        value={targetTitle}
                        onChange={(e) => setTargetTitle(e.target.value)}
                        className="glass-input text-xs h-9"
                      />
                      <Button
                        onClick={handleRewrite}
                        disabled={loadingRewrite || !targetTitle.trim()}
                        className="btn-primary text-xs h-9 flex-shrink-0 px-4 rounded-xl"
                      >
                        {loadingRewrite ? 'Rewriting...' : 'Rewrite'}
                      </Button>
                    </div>
                  </div>
                  <div className="p-6">
                    {loadingRewrite && (
                      <div className="flex flex-col items-center justify-center py-16 space-y-4">
                        <RefreshCw className="w-10 h-10 text-[var(--text-tertiary)] animate-spin" />
                        <div className="text-center space-y-1">
                          <p className="font-semibold text-[var(--text-primary)]">Llama 3 is thinking...</p>
                          <p className="text-xs text-[var(--text-tertiary)]">This can take 10-30s on CPU compilation bounds.</p>
                        </div>
                      </div>
                    )}

                    {!loadingRewrite && !bulletsData && (
                      <div className="text-center py-16 text-[var(--text-tertiary)] text-sm italic">
                        Enter your target role and click Rewrite to optimize bullet points.
                      </div>
                    )}

                    {!loadingRewrite && bulletsData && (
                      <div className="space-y-6 stagger-children">
                        {bulletsData.original_bullets.map((orig, index) => (
                          <div 
                            key={index} 
                            className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-2xl bg-white/40 border border-black/[0.04]"
                          >
                            <div className="space-y-2 border-b md:border-b-0 md:border-r border-black/[0.04] pb-3 md:pb-0 md:pr-4">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-tertiary)]">Original Bullet</span>
                              <p className="text-xs text-[var(--text-secondary)] leading-relaxed font-mono">{orig}</p>
                            </div>
                            
                            <div className="space-y-2 flex flex-col justify-between">
                              <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                  <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-primary)]">AI Improved Bullet</span>
                                  <Button
                                    variant="ghost"
                                    onClick={() => handleCopy(bulletsData.rewritten_bullets[index] || '', index)}
                                    className="h-7 w-7 p-0 hover:bg-black/[0.04] rounded-lg text-[var(--text-tertiary)]"
                                  >
                                    {copiedIndex === index ? (
                                      <Check className="w-3.5 h-3.5 text-green-500" />
                                    ) : (
                                      <Copy className="w-3.5 h-3.5" />
                                    )}
                                  </Button>
                                </div>
                                <p className="text-xs text-[var(--text-primary)] leading-relaxed font-mono">
                                  {bulletsData.rewritten_bullets[index] || 'Failed to rewrite this point.'}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Skill Gaps */}
            {activeTab === 'gaps' && (
              <div className="space-y-6 animate-fadeIn">
                <div className="glass-card-solid p-0 overflow-hidden">
                  <div className="p-6 border-b border-black/[0.04]">
                    <h3 className="text-base font-bold text-[var(--text-primary)]">Bridge Missing Skill Gaps</h3>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">
                      Study curriculum suggested by local Llama 3.1 based on required parameters.
                    </p>
                  </div>
                  <div className="p-6">
                    {loadingGaps && (
                      <div className="flex flex-col items-center justify-center py-16 space-y-4">
                        <RefreshCw className="w-8 h-8 text-[var(--text-tertiary)] animate-spin" />
                        <p className="text-xs text-[var(--text-tertiary)]">Querying learning recommendations...</p>
                      </div>
                    )}

                    {!loadingGaps && gapsData && (
                      <div className="space-y-6">
                        <div className="border border-black/[0.06] rounded-2xl overflow-hidden bg-white/60">
                          <table className="min-w-full divide-y divide-black/[0.04] text-xs text-left">
                            <thead className="bg-black/[0.02] text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">
                              <tr>
                                <th className="px-5 py-3.5">Skill</th>
                                <th className="px-5 py-3.5">Priority</th>
                                <th className="px-5 py-3.5">Suggested Course</th>
                                <th className="px-5 py-3.5">Practice Project</th>
                                <th className="px-5 py-3.5 text-right">Weeks</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-black/[0.04] text-[var(--text-primary)]">
                              {gapsData.gaps && gapsData.gaps.length > 0 ? (
                                gapsData.gaps.map((item, idx) => (
                                  <tr key={idx} className="hover:bg-black/[0.02] transition-colors">
                                    <td className="px-5 py-3.5 font-bold">{item.skill}</td>
                                    <td className="px-5 py-3.5">
                                      <span className={`${getPriorityColor(item.priority)} text-[9px] uppercase font-bold px-2 py-0.5 rounded-md`}>
                                        {item.priority}
                                      </span>
                                    </td>
                                    <td className="px-5 py-3.5 leading-relaxed max-w-xs text-[var(--text-secondary)]">{item.suggested_course}</td>
                                    <td className="px-5 py-3.5 leading-relaxed max-w-xs text-[var(--text-secondary)]">{item.suggested_project}</td>
                                    <td className="px-5 py-3.5 text-right font-semibold">{item.estimated_weeks} wks</td>
                                  </tr>
                                ))
                              ) : (
                                <tr>
                                  <td colSpan={5} className="px-5 py-8 text-center text-[var(--text-tertiary)] italic">
                                    No skill gaps found for this job description.
                                  </td>
                                </tr>
                              )}
                            </tbody>
                          </table>
                        </div>

                        <div className="flex justify-end p-4 rounded-2xl bg-white/40 border border-black/[0.04]">
                          <div className="text-right space-y-0.5">
                            <span className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">Estimated Study Plan</span>
                            <span className="block text-lg font-black text-[var(--text-primary)]">
                              {gapsData.estimated_total_weeks} Weeks Total
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Tab 3: Chat Assistant */}
            {activeTab === 'chat' && (
              <div className="space-y-6 animate-fadeIn">
                <div className="glass-card-solid p-0 overflow-hidden flex flex-col h-[600px]">
                  <div className="p-6 border-b border-black/[0.04]">
                    <h3 className="text-base font-bold text-[var(--text-primary)] flex items-center gap-2">
                      <MessageSquare className="w-5 h-5" /> RAG Chat Assistant
                    </h3>
                    <p className="text-xs text-[var(--text-secondary)] mt-1">
                      Ask context-aware questions about your resume, scoring details, and targeted recommendations.
                    </p>
                  </div>
                  
                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-6 space-y-4">
                    {chatMessages.map((msg, index) => (
                      <div 
                        key={index}
                        className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
                      >
                        <div 
                          className={`max-w-[80%] rounded-2xl p-4 text-xs leading-relaxed ${
                            msg.sender === 'user'
                              ? 'bg-black text-white rounded-br-sm'
                              : 'bg-white/70 border border-black/[0.06] text-[var(--text-primary)] rounded-bl-sm'
                          }`}
                        >
                          <p className="whitespace-pre-wrap">{msg.text}</p>
                        </div>
                      </div>
                    ))}
                    {loadingChat && (
                      <div className="flex justify-start animate-fadeIn">
                        <div className="bg-white/70 border border-black/[0.06] text-[var(--text-secondary)] rounded-2xl rounded-bl-sm p-4 text-xs flex items-center gap-2">
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Llama 3 is typing...</span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Input area */}
                  <div className="border-t border-black/[0.04] p-4 flex flex-col gap-3 bg-white/30">
                    <div className="flex flex-wrap gap-2 w-full">
                      <span className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider self-center mr-1">Suggestions:</span>
                      {[
                        "Why is my ATS score low?",
                        "What skills should I add first?",
                        "How can I improve my summary?"
                      ].map((item, idx) => (
                        <button
                          key={idx}
                          disabled={loadingChat}
                          onClick={() => handleSendChat(item)}
                          className="text-[10px] font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-white/60 border border-black/[0.06] hover:border-black/[0.12] px-3 py-1 rounded-full transition-all"
                        >
                          {item}
                        </button>
                      ))}
                    </div>

                    <div className="flex gap-2 w-full">
                      <Input
                        placeholder="Ask your AI assistant..."
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSendChat();
                        }}
                        disabled={loadingChat}
                        className="glass-input text-xs h-10"
                      />
                      <Button
                        onClick={() => handleSendChat()}
                        disabled={loadingChat || !chatInput.trim()}
                        className="btn-primary rounded-xl h-10 w-10 p-0 flex items-center justify-center"
                      >
                        <Send className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

export default function ImprovePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <RefreshCw className="w-10 h-10 animate-spin text-[var(--text-tertiary)] mx-auto" />
          <p className="text-[var(--text-secondary)] text-sm">Loading CV Optimizer...</p>
        </div>
      </div>
    }>
      <ImprovePageContent />
    </Suspense>
  );
}
