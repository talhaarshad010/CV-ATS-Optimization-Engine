import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface UploadResponse {
  candidate_id: string;
  file_name: string;
  raw_text: string;
  char_count: number;
  status: string;
}

export interface Skill {
  normalized: string;
  confidence: number;
}

export interface ParseResponse {
  candidate_id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  total_experience_years: number | null;
  skills: Skill[];
  skill_count: number;
  status: string;
  raw_sections?: Record<string, { text: string; confidence: string }>;
  raw_entities?: {
    name: string;
    email: string;
    phone: string;
    linkedin: string;
    location: string;
    organizations: string[];
    dates: string[];
    ner_method: string;
  };
}

export const api = axios.create({
  baseURL: API_BASE_URL,
});

export async function uploadCV(
  file: File,
  onUploadProgress?: (progressEvent: any) => void
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onUploadProgress && progressEvent.total) {
        onUploadProgress(progressEvent);
      }
    },
  });
  return response.data;
}

export async function parseCV(candidateId: string): Promise<ParseResponse> {
  const response = await api.post<ParseResponse>(`/parse/${candidateId}`);
  return response.data;
}

export interface JobResponse {
  job_id: string;
  parsed_data: {
    job_title: string;
    required_experience_years: number | null;
    required_education: string | null;
    required_skills: string[];
    preferred_skills: string[];
    responsibilities: string[];
  };
}

export interface ScoreExplanationItem {
  factor: string;
  impact: string;
  detail: string;
}

export interface BreakdownItem {
  score: number;
  max: number;
  percentage: number;
}

export interface ScoreResponse {
  ats_score: number;
  grade: string;
  top_positives: ScoreExplanationItem[];
  top_negatives: ScoreExplanationItem[];
  recommendation: string;
  breakdown: {
    skill_match: BreakdownItem;
    experience_match: BreakdownItem;
    education_match: BreakdownItem;
    semantic_similarity: BreakdownItem;
    project_relevance: BreakdownItem;
    certifications: BreakdownItem;
    resume_quality: BreakdownItem;
  };
  matched_skills: string[];
  missing_skills: string[];
}

export interface SkillGapItem {
  skill: string;
  priority: string;
  suggested_course: string;
  suggested_project: string;
  estimated_weeks: number;
}

export interface SkillGapsResponse {
  gaps: SkillGapItem[];
  total_gaps: number;
  estimated_total_weeks: number;
}

export async function createJobDescription(rawText: string): Promise<JobResponse> {
  const response = await api.post<JobResponse>('/jobs', { raw_text: rawText });
  return response.data;
}

export async function computeScore(candidateId: string, jobId: string): Promise<ScoreResponse> {
  const response = await api.post<ScoreResponse>('/score', {
    candidate_id: candidateId,
    job_id: jobId,
  });
  return response.data;
}

export async function getSkillGaps(candidateId: string, jobId: string): Promise<SkillGapsResponse> {
  const response = await api.post<SkillGapsResponse>('/ai/gaps', {
    candidate_id: candidateId,
    job_id: jobId,
  });
  return response.data;
}

export interface RewriteResponse {
  original_bullets: string[];
  rewritten_bullets: string[];
  improvement_count: number;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
}

export interface ReportResponse {
  candidate_id: string;
  job_id: string;
  job_title: string;
  ats_score: number;
  grade: string;
  breakdown: any;
  skill_gaps: SkillGapItem[];
  gaps_summary: {
    total_gaps: number;
    estimated_total_weeks: number;
  };
  rewritten_bullets: RewriteResponse;
  action_plan: string;
}

export async function rewriteBullets(candidateId: string, jobTitle: string = "Software Engineer"): Promise<RewriteResponse> {
  const response = await api.post<RewriteResponse>(`/ai/rewrite/${candidateId}?job_title=${encodeURIComponent(jobTitle)}`);
  return response.data;
}

export async function askChat(question: string, candidateId?: string): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/ai/chat', {
    question,
    candidate_id: candidateId,
  });
  return response.data;
}

export async function getFullReport(candidateId: string, jobId: string): Promise<ReportResponse> {
  const response = await api.post<ReportResponse>(`/ai/report/${candidateId}/${jobId}`);
  return response.data;
}

export interface DashboardStatsResponse {
  total_candidates: number;
  total_matches: number;
  avg_score: number;
  candidates: any[];
  activity_feed: any[];
}

export async function getDashboardStats(): Promise<DashboardStatsResponse> {
  const response = await api.get<DashboardStatsResponse>('/dashboard');
  return response.data;
}

export interface CandidateUpdateRequest {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  location?: string | null;
  linkedin_url?: string | null;
  total_experience_years?: number | null;
  raw_sections?: Record<string, { text: string; confidence: string }>;
}

export async function updateCandidateDetails(candidateId: string, payload: CandidateUpdateRequest): Promise<any> {
  const response = await api.put(`/candidates/${candidateId}`, payload);
  return response.data;
}
