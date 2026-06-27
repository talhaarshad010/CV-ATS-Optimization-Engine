"use client";

import React, { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useDropzone } from 'react-dropzone';
import { 
  AlertCircle, 
  CheckCircle2, 
  XCircle, 
  Award, 
  Sparkles, 
  RefreshCw, 
  ArrowLeft, 
  BookOpen, 
  ChevronRight, 
  HelpCircle,
  FileText,
  Bookmark,
  ExternalLink,
  Target,
  Upload,
  Trash2
} from 'lucide-react';

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';

import { 
  uploadCV,
  parseCV, 
  createJobDescription, 
  computeScore, 
  getSkillGaps, 
  ParseResponse, 
  ScoreResponse, 
  SkillGapsResponse 
} from '@/lib/api';
import { useAppStore } from '@/lib/store';

import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Cell 
} from 'recharts';

function ScorePageContent() {
  const searchParams = useSearchParams();
  const candidateIdParam = searchParams.get('candidate_id');

  const { setCandidateId: setStoreCandidateId, setCandidateName: setStoreCandidateName, setJobId: setStoreJobId, setAtsScore: setStoreAtsScore } = useAppStore();

  const [candidateId, setCandidateId] = useState<string>('');
  const [candidateInfo, setCandidateInfo] = useState<ParseResponse | null>(null);
  const [jdText, setJdText] = useState<string>('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [scoreData, setScoreData] = useState<ScoreResponse | null>(null);
  const [gapsData, setGapsData] = useState<SkillGapsResponse | null>(null);

  const [loadingCandidate, setLoadingCandidate] = useState<boolean>(false);
  const [loadingScore, setLoadingScore] = useState<boolean>(false);
  const [loadingGaps, setLoadingGaps] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [mounted, setMounted] = useState<boolean>(false);

  // Bulk Mode states
  const [isBulkMode, setIsBulkMode] = useState<boolean>(false);
  const [bulkFiles, setBulkFiles] = useState<Array<{
    id: string;
    file: File;
    progress: number;
    status: 'queued' | 'uploading' | 'parsing' | 'scoring' | 'done' | 'failed';
    candidateId?: string;
    score?: number;
    grade?: string;
    name?: string;
    error?: string;
  }>>([]);
  const [isProcessingBulk, setIsProcessingBulk] = useState<boolean>(false);

  const onDropBulk = useCallback((acceptedFiles: File[]) => {
    const newItems = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substring(7),
      file,
      progress: 0,
      status: 'queued' as const
    }));
    setBulkFiles(prev => [...prev, ...newItems]);
  }, []);

  const { getRootProps: getRootPropsBulk, getInputProps: getInputPropsBulk, isDragActive: isDragActiveBulk } = useDropzone({
    onDrop: onDropBulk,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    multiple: true,
  });

  const handleRemoveBulkFile = (id: string) => {
    setBulkFiles(prev => prev.filter(f => f.id !== id));
  };

  const handleBulkAnalyze = async () => {
    if (!jdText.trim() || bulkFiles.length === 0) return;
    setIsProcessingBulk(true);
    setError(null);
    try {
      let activeJobId = jobId;
      if (!activeJobId) {
        const jdResponse = await createJobDescription(jdText);
        activeJobId = jdResponse.job_id;
        setJobId(activeJobId);
        setStoreJobId(activeJobId);
      }
      
      // Process sequentially to keep CPU/Ollama load predictable
      for (let i = 0; i < bulkFiles.length; i++) {
        const item = bulkFiles[i];
        if (item.status === 'done') continue;
        
        setBulkFiles(prev => prev.map(f => f.id === item.id ? { ...f, status: 'uploading', progress: 10 } : f));
        
        let currentCid = item.candidateId;
        try {
          if (!currentCid) {
            const uploadRes = await uploadCV(item.file, (progressEvent) => {
              if (progressEvent.total) {
                const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                setBulkFiles(prev => prev.map(f => f.id === item.id ? { ...f, progress: 10 + Math.round(percentCompleted * 0.4) } : f));
              }
            });
            currentCid = uploadRes.candidate_id;
            setBulkFiles(prev => prev.map(f => f.id === item.id ? { ...f, candidateId: currentCid, progress: 50 } : f));
          }
          
          setBulkFiles(prev => prev.map(f => f.id === item.id ? { ...f, status: 'parsing', progress: 60 } : f));
          const parseRes = await parseCV(currentCid);
          const candidateName = parseRes.name || 'Anonymous Candidate';
          setBulkFiles(prev => prev.map(f => f.id === item.id ? { ...f, name: candidateName, progress: 80 } : f));
          
          setBulkFiles(prev => prev.map(f => f.id === item.id ? { ...f, status: 'scoring', progress: 90 } : f));
          const scoreRes = await computeScore(currentCid, activeJobId!);
          
          setBulkFiles(prev => prev.map(f => f.id === item.id ? { 
            ...f, 
            status: 'done', 
            score: scoreRes.ats_score, 
            grade: scoreRes.grade, 
            progress: 100 
          } : f));
        } catch (err: any) {
          console.error(err);
          const errMsg = err.response?.data?.detail || 'Processing failed.';
          setBulkFiles(prev => prev.map(f => f.id === item.id ? { ...f, status: 'failed', error: errMsg, progress: 100 } : f));
        }
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to submit Job Description.');
    } finally {
      setIsProcessingBulk(false);
    }
  };

  const handleViewCandidateDetails = async (candidateId: string, name: string) => {
    setLoadingCandidate(true);
    setError(null);
    try {
      const parseRes = await parseCV(candidateId);
      setCandidateInfo(parseRes);
      setStoreCandidateId(candidateId);
      setStoreCandidateName(parseRes.name || name);
      
      const scoreRes = await computeScore(candidateId, jobId!);
      setScoreData(scoreRes);
      setStoreAtsScore(scoreRes.ats_score);
    } catch (err: any) {
      console.error(err);
      setError('Failed to load detailed profile details.');
    } finally {
      setLoadingCandidate(false);
    }
  };

  useEffect(() => {
    setMounted(true);
  }, []);

  const loadCandidateInfo = useCallback(async (id: string) => {
    if (!id.trim()) return;
    setLoadingCandidate(true);
    setError(null);
    try {
      const data = await parseCV(id.trim());
      setCandidateInfo(data);
      setStoreCandidateId(data.candidate_id);
      setStoreCandidateName(data.name);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to fetch candidate details. Ensure ID is correct.');
      setCandidateInfo(null);
    } finally {
      setLoadingCandidate(false);
    }
  }, [setStoreCandidateId, setStoreCandidateName]);

  useEffect(() => {
    if (candidateIdParam) {
      setCandidateId(candidateIdParam);
      loadCandidateInfo(candidateIdParam);
    }
  }, [candidateIdParam, loadCandidateInfo]);

  const handleIdSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadCandidateInfo(candidateId);
  };

  const handleAnalyzeMatch = async () => {
    if (!candidateInfo?.candidate_id || !jdText.trim()) return;
    setLoadingScore(true);
    setError(null);
    setScoreData(null);
    setGapsData(null);
    setJobId(null);

    try {
      const jdResponse = await createJobDescription(jdText);
      const newJobId = jdResponse.job_id;
      setJobId(newJobId);
      setStoreJobId(newJobId);

      const scoreResponse = await computeScore(candidateInfo.candidate_id, newJobId);
      setScoreData(scoreResponse);
      setStoreAtsScore(scoreResponse.ats_score);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to calculate ATS match score.');
    } finally {
      setLoadingScore(false);
    }
  };

  const handleGetGaps = async () => {
    if (!candidateInfo?.candidate_id || !jobId) return;
    setLoadingGaps(true);
    setError(null);
    try {
      const data = await getSkillGaps(candidateInfo.candidate_id, jobId);
      setGapsData(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to fetch AI improvement tips.');
    } finally {
      setLoadingGaps(false);
    }
  };

  const getChartData = () => {
    if (!scoreData?.breakdown) return [];
    return [
      { name: 'Skill Match', value: scoreData.breakdown.skill_match.percentage },
      { name: 'Experience', value: scoreData.breakdown.experience_match.percentage },
      { name: 'Education', value: scoreData.breakdown.education_match.percentage },
      { name: 'Semantic Match', value: scoreData.breakdown.semantic_similarity.percentage },
      { name: 'Projects', value: scoreData.breakdown.project_relevance.percentage },
      { name: 'Certifications', value: scoreData.breakdown.certifications.percentage },
      { name: 'Resume Quality', value: scoreData.breakdown.resume_quality.percentage },
    ];
  };

  const chartData = getChartData();
  const COLORS = ['#1d1d1f', '#3a3a3c', '#636366', '#48484a', '#8e8e93', '#2c2c2e', '#545456'];

  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const score = scoreData?.ats_score || 0;
  const offset = circumference - (score / 100) * circumference;

  const getGradeStyles = (grade: string) => {
    if (grade.startsWith('A')) return 'text-green-700 bg-green-50 border-green-200';
    if (grade.startsWith('B')) return 'text-blue-700 bg-blue-50 border-blue-200';
    if (grade.startsWith('C')) return 'text-amber-700 bg-amber-50 border-amber-200';
    return 'text-red-700 bg-red-50 border-red-200';
  };

  const getScoreCircleColor = (s: number) => {
    if (s >= 80) return 'stroke-green-500';
    if (s >= 65) return 'stroke-blue-500';
    if (s >= 50) return 'stroke-amber-500';
    return 'stroke-red-500';
  };

  return (
    <main className="min-h-screen flex flex-col items-center py-12 px-4 md:px-8">
      <div className="max-w-5xl w-full z-10 space-y-8 animate-fadeInUp">
        {/* Header */}
        <div className="flex flex-col gap-4">
          <div>
            <Button 
              variant="link" 
              onClick={() => window.location.href = '/'}
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] p-0 flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" /> Back to Upload CV
            </Button>
          </div>

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-2">
              <h1 className="text-3xl md:text-4xl font-black tracking-tight text-[var(--text-primary)]">
                ATS Matching & SHAP Explainer
              </h1>
              <p className="text-[var(--text-secondary)] max-w-xl text-sm">
                Paste your target job description to compute the semantic match score, audit matching criteria, and trace model features.
              </p>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-600 text-sm animate-scaleIn">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <div className="font-medium">{error}</div>
          </div>
        )}

        {/* Toggle Mode Switcher */}
        {!candidateInfo && !scoreData && (
          <div className="flex justify-center mb-6">
            <div className="inline-flex rounded-xl bg-black/[0.04] p-1 border border-black/[0.04]">
              <button
                type="button"
                onClick={() => setIsBulkMode(false)}
                className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                  !isBulkMode 
                    ? 'bg-white shadow text-[var(--text-primary)]' 
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                Single Resume
              </button>
              <button
                type="button"
                onClick={() => setIsBulkMode(true)}
                className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                  isBulkMode 
                    ? 'bg-white shadow text-[var(--text-primary)]' 
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)]'
                }`}
              >
                Bulk Mode (Rank Resumes)
              </button>
            </div>
          </div>
        )}

        {/* Step 1: Candidate ID Fetcher (Single Mode) */}
        {!candidateInfo && !scoreData && !isBulkMode && (
          <div className="glass-card-solid p-0 overflow-hidden max-w-xl mx-auto">
            <div className="p-6 pb-4">
              <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                <Bookmark className="w-5 h-5" /> Select Candidate Profile
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1">Enter your candidate UUID to load skills and experience details.</p>
            </div>
            <form onSubmit={handleIdSubmit}>
              <div className="px-6 pb-4 space-y-2">
                <label htmlFor="candidate-uuid" className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)]">Candidate UUID</label>
                <Input 
                  id="candidate-uuid"
                  placeholder="e.g. 71de1aa9-b3e1-4069-b723-b26769ddfdd8" 
                  value={candidateId}
                  onChange={(e) => setCandidateId(e.target.value)}
                  className="glass-input h-11 text-sm"
                />
              </div>
              <div className="flex justify-end border-t border-black/[0.04] px-6 py-4">
                <Button 
                  type="submit"
                  disabled={loadingCandidate || !candidateId.trim()}
                  className="btn-primary px-5 py-2 rounded-xl text-sm"
                >
                  {loadingCandidate ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Loading Profile...
                    </>
                  ) : 'Load Candidate Details'}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Step 1: Bulk Uploader & Progress (Bulk Mode) */}
        {!candidateInfo && !scoreData && isBulkMode && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fadeIn">
            {/* Left: Input Job Description & Upload zone */}
            <div className="lg:col-span-2 space-y-6">
              {/* JD input */}
              <div className="glass-card-solid p-6 space-y-4">
                <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <FileText className="w-5 h-5" /> Step 1: Paste Job Description
                </h2>
                <textarea
                  placeholder="Paste the target Job Description to rank your bulk CV uploads against..."
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  className="glass-input w-full h-48 p-4 text-sm resize-none"
                />
              </div>

              {/* Multi-Dropzone */}
              <div className="glass-card-solid p-6 space-y-4">
                <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <Upload className="w-5 h-5" /> Step 2: Upload Multiple CVs
                </h2>
                <div 
                  {...getRootPropsBulk()} 
                  className={`border-2 border-dashed rounded-2xl p-10 flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-300 ${
                    isDragActiveBulk 
                      ? 'border-black/30 bg-black/[0.03] scale-[1.01]' 
                      : 'border-black/10 hover:border-black/20 bg-white/40 hover:bg-white/60'
                  }`}
                >
                  <input {...getInputPropsBulk()} />
                  <div className="p-3 rounded-xl bg-black/[0.04] text-[var(--text-secondary)]">
                    <Upload className="w-6 h-6" />
                  </div>
                  <div className="text-center space-y-1">
                    <p className="font-semibold text-sm text-[var(--text-primary)]">
                      Drag & drop multiple resume PDFs here, or click to browse
                    </p>
                    <p className="text-xs text-[var(--text-tertiary)]">Supports PDF and DOCX formats (Max 10MB each)</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Upload Queue & Runner */}
            <div className="glass-card-solid p-0 overflow-hidden flex flex-col justify-between h-[432px]">
              <div className="p-6 border-b border-black/[0.04]">
                <h3 className="text-md font-bold text-[var(--text-primary)]">Upload Queue ({bulkFiles.length})</h3>
                <p className="text-xs text-[var(--text-secondary)] mt-1">Files queued for match analysis.</p>
              </div>
              <div className="flex-1 overflow-y-auto p-6 space-y-3">
                {bulkFiles.length === 0 ? (
                  <div className="text-center py-20 text-[var(--text-tertiary)] text-xs italic select-none">
                    Queue is empty.<br/>Upload files on the left to start.
                  </div>
                ) : (
                  bulkFiles.map((item) => (
                    <div key={item.id} className="p-3 rounded-xl bg-white/60 border border-black/[0.04] flex items-center justify-between gap-3 text-xs">
                      <div className="space-y-1 w-2/3">
                        <p className="font-semibold text-[var(--text-primary)] truncate">{item.file.name}</p>
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] text-[var(--text-tertiary)]">
                            {(item.file.size / (1024 * 1024)).toFixed(2)} MB
                          </span>
                          <span>•</span>
                          <span className={`text-[9px] font-bold uppercase ${
                            item.status === 'done' ? 'text-green-600' :
                            item.status === 'failed' ? 'text-red-600' :
                            item.status === 'queued' ? 'text-[var(--text-tertiary)]' :
                            'text-blue-600'
                          }`}>
                            {item.status}
                          </span>
                        </div>
                        {item.status !== 'queued' && item.status !== 'done' && item.status !== 'failed' && (
                          <div className="w-full bg-black/[0.04] rounded-full h-1 overflow-hidden">
                            <div className="bg-black h-full rounded-full transition-all duration-300" style={{ width: `${item.progress}%` }} />
                          </div>
                        )}
                      </div>
                      <div className="flex items-center gap-1">
                        {item.status === 'done' && item.score !== undefined && (
                          <span className="font-black text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200">
                            {item.score}%
                          </span>
                        )}
                        {!isProcessingBulk && (
                          <button
                            onClick={() => handleRemoveBulkFile(item.id)}
                            className="p-1.5 hover:bg-red-50 text-[var(--text-tertiary)] hover:text-red-600 rounded-lg transition-colors"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
              <div className="p-4 border-t border-black/[0.04] bg-white/30 flex justify-end gap-2">
                <Button
                  onClick={() => setBulkFiles([])}
                  disabled={isProcessingBulk || bulkFiles.length === 0}
                  className="btn-secondary text-xs h-9 rounded-xl px-4"
                >
                  Clear All
                </Button>
                <Button
                  onClick={handleBulkAnalyze}
                  disabled={isProcessingBulk || bulkFiles.length === 0 || !jdText.trim()}
                  className="btn-primary text-xs h-9 rounded-xl px-5"
                >
                  {isProcessingBulk ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 mr-2 animate-spin" /> Analyzing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5 mr-2" /> Analyze & Rank
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Bulk Leaderboard (Ranked Results) */}
        {!candidateInfo && !scoreData && isBulkMode && bulkFiles.some(f => f.status === 'done') && (
          <div className="glass-card-solid p-0 overflow-hidden animate-fadeInUp mt-8">
            <div className="p-6 border-b border-black/[0.04]">
              <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                <Award className="w-5 h-5" /> Ranked Resumes Leaderboard
              </h2>
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                Candidate resumes sorted by their compliance scores against the job description.
              </p>
            </div>
            <div className="p-6">
              <div className="border border-black/[0.06] rounded-2xl overflow-hidden bg-white/60">
                <table className="min-w-full divide-y divide-black/[0.04] text-xs text-left">
                  <thead className="bg-black/[0.02] text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">
                    <tr>
                      <th className="px-5 py-3.5">Rank</th>
                      <th className="px-5 py-3.5">Candidate Name</th>
                      <th className="px-5 py-3.5">File Name</th>
                      <th className="px-5 py-3.5 text-center">Grade</th>
                      <th className="px-5 py-3.5 text-right">ATS Match Score</th>
                      <th className="px-5 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-black/[0.04] text-[var(--text-primary)]">
                    {bulkFiles
                      .filter(f => f.status === 'done' && f.score !== undefined)
                      .sort((a, b) => (b.score || 0) - (a.score || 0))
                      .map((item, idx) => (
                        <tr key={item.id} className="hover:bg-black/[0.01] transition-colors">
                          <td className="px-5 py-3.5 font-bold"># {idx + 1}</td>
                          <td className="px-5 py-3.5 font-bold text-sm">{item.name || 'Anonymous'}</td>
                          <td className="px-5 py-3.5 text-[var(--text-secondary)] font-mono">{item.file.name}</td>
                          <td className="px-5 py-3.5 text-center">
                            <span className={`text-[10px] px-2.5 py-0.5 rounded-md font-bold ${getGradeStyles(item.grade || 'C')}`}>
                              Grade {item.grade || 'N/A'}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-right text-base font-black text-green-700">{item.score}%</td>
                          <td className="px-5 py-3.5 text-right">
                            <Button
                              onClick={() => handleViewCandidateDetails(item.candidateId!, item.name || 'Anonymous')}
                              disabled={loadingCandidate}
                              className="btn-primary text-[10px] h-7 px-3 py-1 rounded-lg"
                            >
                              View Details
                            </Button>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Loading Candidate Skeleton */}
        {loadingCandidate && (
          <div className="glass-card-solid p-6 space-y-4 animate-fadeIn">
            <div className="flex items-center gap-3">
              <RefreshCw className="w-5 h-5 animate-spin text-[var(--text-secondary)]" />
              <span className="text-sm font-semibold text-[var(--text-secondary)]">Loading candidate profile...</span>
            </div>
            <div className="shimmer-loader h-12 rounded-xl" />
            <div className="flex gap-2">
              <div className="shimmer-loader h-8 w-24 rounded-lg" />
              <div className="shimmer-loader h-8 w-24 rounded-lg" />
              <div className="shimmer-loader h-8 w-24 rounded-lg" />
            </div>
          </div>
        )}

        {/* Candidate Profile Banner */}
        {candidateInfo && (
          <div className="glass-card-solid p-0 overflow-hidden animate-scaleIn">
            <div className="flex flex-col md:flex-row md:items-center justify-between p-6 border-b border-black/[0.04]">
              <div className="space-y-1">
                <div className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">Active Candidate Profile</div>
                <h2 className="text-2xl font-bold text-[var(--text-primary)]">
                  {candidateInfo.name || 'Anonymous Candidate'}
                </h2>
                <div className="text-xs text-[var(--text-secondary)] flex flex-wrap gap-x-4 gap-y-1">
                  {candidateInfo.email && <span>Email: {candidateInfo.email}</span>}
                  {candidateInfo.phone && <span>Phone: {candidateInfo.phone}</span>}
                  {candidateInfo.location && <span>Location: {candidateInfo.location}</span>}
                  {candidateInfo.total_experience_years !== null && (
                    <span>Exp: {candidateInfo.total_experience_years} Years</span>
                  )}
                </div>
              </div>
              <div className="flex gap-2 mt-3 md:mt-0">
                <span className="glass-badge text-xs px-3 py-1.5 select-none">
                  UUID: {candidateInfo.candidate_id.substring(0, 8)}...
                </span>
                {isBulkMode && (
                  <Button
                    onClick={() => {
                      setCandidateInfo(null);
                      setScoreData(null);
                      setGapsData(null);
                    }}
                    className="btn-secondary px-3 h-8 rounded-lg text-xs"
                  >
                    ← Leaderboard
                  </Button>
                )}
                <Button
                  variant="ghost"
                  onClick={() => {
                    setCandidateInfo(null);
                    setScoreData(null);
                    setGapsData(null);
                    setJobId(null);
                    setBulkFiles([]);
                  }}
                  className="btn-secondary px-3 h-8 rounded-lg text-xs"
                >
                  Change Profile
                </Button>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-3">
                <div className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)]">Extracted Skills ({candidateInfo.skill_count})</div>
                <div className="flex flex-wrap gap-2 max-h-24 overflow-y-auto pr-2">
                  {candidateInfo.skills && candidateInfo.skills.length > 0 ? (
                    candidateInfo.skills.map((skill, index) => (
                      <span key={index} className="glass-badge text-xs px-2.5 py-1">
                        {skill.normalized}
                      </span>
                    ))
                  ) : (
                    <span className="text-sm text-[var(--text-tertiary)] italic">No skills extracted for this candidate.</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Job Description */}
        {candidateInfo && !scoreData && (
          <div className="glass-card-solid p-0 overflow-hidden animate-fadeInUp">
            <div className="p-6 pb-4">
              <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                <FileText className="w-5 h-5" /> Paste Job Description
              </h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                Paste the full target job posting text here to analyze semantic compliance and experience matches.
              </p>
            </div>
            <div className="px-6 pb-4">
              <textarea
                placeholder="We are looking for a Senior Developer with 3+ years of experience in Python, FastAPI, and Docker..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                className="glass-input w-full h-64 p-4 text-sm resize-none"
              />
            </div>
            <div className="flex justify-end border-t border-black/[0.04] px-6 py-4">
              <Button 
                onClick={handleAnalyzeMatch}
                disabled={loadingScore || !jdText.trim()}
                className="btn-primary px-6 py-2 rounded-xl text-sm"
              >
                {loadingScore ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Analyzing Match...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" /> Analyze Match
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* Score Loading Skeleton */}
        {loadingScore && (
          <div className="glass-card-solid p-6 space-y-4 animate-fadeIn">
            <div className="flex items-center gap-3">
              <RefreshCw className="w-5 h-5 animate-spin text-[var(--text-secondary)]" />
              <span className="text-sm font-semibold text-[var(--text-secondary)]">Computing ATS match score...</span>
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="shimmer-loader h-40 rounded-2xl" />
              <div className="shimmer-loader h-40 rounded-2xl col-span-2" />
            </div>
          </div>
        )}

        {/* Step 3: Results */}
        {scoreData && (
          <div className="space-y-8 stagger-children">
            {/* Score Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Circular Gauge */}
              <div className="glass-card-solid flex flex-col items-center justify-center p-6 space-y-4">
                <div className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] text-center">ATS Score</div>
                <div className="relative flex items-center justify-center w-36 h-36">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="72" cy="72" r={radius} className="stroke-black/[0.06]" strokeWidth="9" fill="transparent" />
                    <circle
                      cx="72" cy="72" r={radius}
                      className={`${getScoreCircleColor(score)} progress-ring`}
                      strokeWidth="9"
                      strokeDasharray={circumference}
                      strokeDashoffset={offset}
                      strokeLinecap="round"
                      fill="transparent"
                    />
                  </svg>
                  <div className="absolute text-center space-y-0.5">
                    <span className="text-4xl font-black text-[var(--text-primary)]">{score}</span>
                    <span className="block text-[9px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">out of 100</span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[var(--text-secondary)]">Grade:</span>
                  <span className={`text-xs border font-bold px-3 py-0.5 rounded-full ${getGradeStyles(scoreData.grade)}`}>
                    {scoreData.grade}
                  </span>
                </div>
              </div>

              {/* Chart */}
              <div className="glass-card-solid md:col-span-2 p-6 flex flex-col justify-between">
                <div className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] mb-4">Criteria Breakdown</div>
                <div className="w-full h-56">
                  {mounted && chartData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 10, top: 0, bottom: 0 }}>
                        <XAxis type="number" domain={[0, 100]} hide />
                        <YAxis 
                          dataKey="name" type="category" stroke="#6e6e73" fontSize={11} width={95}
                          tickLine={false} axisLine={false}
                        />
                        <Tooltip
                          cursor={{ fill: 'rgba(0, 0, 0, 0.03)' }}
                          contentStyle={{
                            backgroundColor: 'rgba(255, 255, 255, 0.9)',
                            backdropFilter: 'blur(20px)',
                            borderColor: 'rgba(0, 0, 0, 0.08)',
                            borderRadius: '12px',
                            color: '#1d1d1f',
                            fontSize: '12px',
                            boxShadow: '0 8px 32px rgba(0,0,0,0.08)'
                          }}
                          formatter={(value: any) => [`${value}%`, 'Score']}
                        />
                        <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={14}>
                          {chartData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-[var(--text-tertiary)] text-xs italic">
                      Loading chart...
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* AI Recommendation Banner */}
            <div className="glass-card-solid p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="text-xs font-bold text-[var(--text-primary)] flex items-center gap-1.5 uppercase tracking-wide">
                  <Award className="w-4 h-4" /> AI Scorer Recommendation
                </div>
                <p className="text-[var(--text-secondary)] text-sm leading-relaxed">
                  {scoreData.recommendation}
                </p>
              </div>
              <div className="flex-shrink-0">
                {!gapsData ? (
                  <Button 
                    onClick={handleGetGaps}
                    disabled={loadingGaps}
                    className="btn-primary text-xs px-4 py-2 rounded-xl"
                  >
                    {loadingGaps ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 mr-2 animate-spin" /> Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5 mr-2" /> Get AI Improvement Tips
                      </>
                    )}
                  </Button>
                ) : (
                  <Button
                    onClick={() => window.location.href = `/improve?candidate_id=${candidateInfo?.candidate_id}&job_id=${jobId}`}
                    className="btn-primary text-xs px-4 py-2 rounded-xl"
                  >
                    Open CV Optimizer
                  </Button>
                )}
              </div>
            </div>

            {/* SHAP Feature Impacts */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)] flex items-center gap-2">
                <HelpCircle className="w-4 h-4" /> SHAP Feature Impacts (CV Strengths & Gaps)
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Positive */}
                <div className="glass-card-solid p-0 overflow-hidden">
                  <div className="p-4 border-b border-black/[0.04]">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-500" /> Top Positive Attributions
                    </h3>
                  </div>
                  <div className="p-4 space-y-3">
                    {scoreData.top_positives && scoreData.top_positives.length > 0 ? (
                      scoreData.top_positives.slice(0, 2).map((item, index) => (
                        <div key={index} className="p-3.5 rounded-xl bg-green-50 border border-green-100 flex items-start gap-3">
                          <span className="text-xs font-bold text-green-700 bg-green-100 px-2 py-0.5 rounded-md mt-0.5 select-none">
                            {item.impact}
                          </span>
                          <div className="space-y-0.5">
                            <span className="text-xs font-bold text-[var(--text-primary)] block">{item.factor}</span>
                            <span className="text-xs text-[var(--text-secondary)] leading-relaxed block">{item.detail}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <span className="text-xs text-[var(--text-tertiary)] italic">No significant positive features computed.</span>
                    )}
                  </div>
                </div>

                {/* Negative */}
                <div className="glass-card-solid p-0 overflow-hidden">
                  <div className="p-4 border-b border-black/[0.04]">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                      <XCircle className="w-4 h-4 text-red-500" /> Top Negative Attributions
                    </h3>
                  </div>
                  <div className="p-4 space-y-3">
                    {scoreData.top_negatives && scoreData.top_negatives.length > 0 ? (
                      scoreData.top_negatives.slice(0, 2).map((item, index) => (
                        <div key={index} className="p-3.5 rounded-xl bg-red-50 border border-red-100 flex items-start gap-3">
                          <span className="text-xs font-bold text-red-700 bg-red-100 px-2 py-0.5 rounded-md mt-0.5 select-none">
                            {item.impact}
                          </span>
                          <div className="space-y-0.5">
                            <span className="text-xs font-bold text-[var(--text-primary)] block">{item.factor}</span>
                            <span className="text-xs text-[var(--text-secondary)] leading-relaxed block">{item.detail}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <span className="text-xs text-[var(--text-tertiary)] italic">No significant negative features computed.</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Matched vs Missing Skills */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-card-solid p-0 overflow-hidden">
                <div className="p-4 border-b border-black/[0.04]">
                  <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-green-500" /> Matched Skills ({scoreData.matched_skills.length})
                  </h3>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">Skills in your resume that meet job specifications.</p>
                </div>
                <div className="p-4 flex flex-wrap gap-2 max-h-48 overflow-y-auto">
                  {scoreData.matched_skills.length > 0 ? (
                    scoreData.matched_skills.map((skill, index) => (
                      <span key={index} className="text-xs px-2.5 py-1 rounded-lg bg-green-50 border border-green-100 text-green-700 font-medium">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-[var(--text-tertiary)] italic">No matching skills found.</span>
                  )}
                </div>
              </div>

              <div className="glass-card-solid p-0 overflow-hidden">
                <div className="p-4 border-b border-black/[0.04]">
                  <h3 className="text-sm font-bold text-[var(--text-primary)] flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-red-500" /> Missing Skills ({scoreData.missing_skills.length})
                  </h3>
                  <p className="text-xs text-[var(--text-secondary)] mt-1">Required skills not detected in your resume.</p>
                </div>
                <div className="p-4 flex flex-wrap gap-2 max-h-48 overflow-y-auto">
                  {scoreData.missing_skills.length > 0 ? (
                    scoreData.missing_skills.map((skill, index) => (
                      <span key={index} className="text-xs px-2.5 py-1 rounded-lg bg-red-50 border border-red-100 text-red-700 font-medium">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-[var(--text-tertiary)] italic">Excellent! No missing skills.</span>
                  )}
                </div>
              </div>
            </div>

            {/* AI Skill Gaps */}
            {gapsData && (
              <div className="glass-card-solid p-0 overflow-hidden animate-fadeInUp">
                <div className="p-6 border-b border-black/[0.04]">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                        <BookOpen className="w-5 h-5" /> AI Learning Timeline & Study Paths
                      </h2>
                      <p className="text-sm text-[var(--text-secondary)] mt-1">
                        Curated study courses and practice projects to acquire missing skills.
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-xs text-[var(--text-secondary)] font-semibold">Estimated Study Duration</div>
                      <span className="text-lg font-black text-[var(--text-primary)]">
                        {gapsData.estimated_total_weeks} Weeks
                      </span>
                    </div>
                  </div>
                </div>
                <div className="p-6 space-y-6">
                  {gapsData.gaps && gapsData.gaps.length > 0 ? (
                    <div className="relative border-l-2 border-black/10 pl-6 ml-3 space-y-6">
                      {gapsData.gaps.map((item, index) => (
                        <div key={index} className="relative group">
                          <span className="absolute -left-[29px] top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-white border-2 border-black/20 group-hover:border-black/40 transition-colors">
                            <span className="h-1.5 w-1.5 rounded-full bg-black/40" />
                          </span>
                          
                          <div className="space-y-2">
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                              <div className="flex items-center gap-2.5">
                                <h4 className="font-bold text-[var(--text-primary)] text-sm">{item.skill}</h4>
                                <span className={`text-[9px] uppercase font-bold px-2 py-0.5 rounded-md border ${
                                  item.priority === 'high' 
                                    ? 'bg-red-50 text-red-700 border-red-200' 
                                    : 'bg-amber-50 text-amber-700 border-amber-200'
                                }`}>
                                  {item.priority} Priority
                                </span>
                              </div>
                              <span className="text-xs text-[var(--text-secondary)] font-semibold">{item.estimated_weeks} Weeks</span>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div className="p-3.5 rounded-xl bg-white/60 border border-black/[0.04] space-y-1">
                                <span className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">Free Learning Course</span>
                                <p className="text-xs text-[var(--text-primary)] font-medium leading-relaxed">{item.suggested_course}</p>
                              </div>
                              <div className="p-3.5 rounded-xl bg-white/60 border border-black/[0.04] space-y-1">
                                <span className="text-[10px] uppercase font-bold text-[var(--text-tertiary)] tracking-wider">Practice Project</span>
                                <p className="text-xs text-[var(--text-primary)] font-medium leading-relaxed">{item.suggested_project}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-6 text-[var(--text-tertiary)] text-sm italic">
                      No matching gaps to address. Excellent profile match!
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Bottom Actions */}
            <div className="flex justify-end gap-3 pt-6 border-t border-black/[0.04]">
              <Button
                variant="outline"
                onClick={() => {
                  setScoreData(null);
                  setGapsData(null);
                  setJobId(null);
                }}
                className="btn-secondary px-5 py-2 rounded-xl text-sm"
              >
                Analyze Another Job
              </Button>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

export default function ScorePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <RefreshCw className="w-10 h-10 animate-spin text-[var(--text-tertiary)] mx-auto" />
          <p className="text-[var(--text-secondary)] text-sm">Loading ATS Analyzer...</p>
        </div>
      </div>
    }>
      <ScorePageContent />
    </Suspense>
  );
}
