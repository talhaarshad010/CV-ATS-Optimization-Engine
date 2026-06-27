"use client";

import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  CheckCircle, 
  AlertCircle, 
  User, 
  Mail, 
  Phone, 
  MapPin, 
  Briefcase, 
  FileText, 
  Sparkles, 
  RefreshCw,
  ExternalLink,
  Building,
  GraduationCap,
  Globe,
  Award,
  BookOpen
} from 'lucide-react';

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { uploadCV, parseCV, UploadResponse, ParseResponse, updateCandidateDetails } from '@/lib/api';
import { useAppStore } from '@/lib/store';

export default function Home() {
  const { setCandidateId, setCandidateName, setJobId, setAtsScore, clearState } = useAppStore();

  const [file, setFile] = useState<File | null>(null);
  const [previewTab, setPreviewTab] = useState<'profile' | 'sections' | 'entities'>('profile');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [isParsing, setIsParsing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const [parsedData, setParsedData] = useState<ParseResponse | null>(null);

  // Editable CV Profile states
  const [localName, setLocalName] = useState<string>('');
  const [localEmail, setLocalEmail] = useState<string>('');
  const [localPhone, setLocalPhone] = useState<string>('');
  const [localLocation, setLocalLocation] = useState<string>('');
  const [localLinkedin, setLocalLinkedin] = useState<string>('');
  const [localExperience, setLocalExperience] = useState<string>('');
  const [isSavingProfile, setIsSavingProfile] = useState<boolean>(false);
  const [localSections, setLocalSections] = useState<Record<string, string>>({
    summary: '',
    experience: '',
    education: '',
    projects: '',
    certifications: '',
    languages: '',
    achievements: ''
  });

  // Synchronize local editable states with newly parsed data
  useEffect(() => {
    if (parsedData) {
      setLocalName(parsedData.name || '');
      setLocalEmail(parsedData.email || '');
      setLocalPhone(parsedData.phone || '');
      setLocalLocation(parsedData.location || '');
      setLocalLinkedin(parsedData.linkedin_url || '');
      setLocalExperience(parsedData.total_experience_years !== null && parsedData.total_experience_years !== undefined ? parsedData.total_experience_years.toString() : '');
      
      const sectionsObj: Record<string, string> = {};
      const sectionKeys = ['summary', 'experience', 'education', 'projects', 'certifications', 'languages', 'achievements'];
      sectionKeys.forEach(key => {
        sectionsObj[key] = parsedData.raw_sections?.[key]?.text || '';
      });
      setLocalSections(sectionsObj);
    } else {
      setLocalName('');
      setLocalEmail('');
      setLocalPhone('');
      setLocalLocation('');
      setLocalLinkedin('');
      setLocalExperience('');
      setLocalSections({
        summary: '',
        experience: '',
        education: '',
        projects: '',
        certifications: '',
        languages: '',
        achievements: ''
      });
    }
  }, [parsedData]);

  const handleSectionChange = (section: string, value: string) => {
    setLocalSections(prev => ({
      ...prev,
      [section]: value
    }));
  };

  const handleSaveProfile = async () => {
    if (!parsedData) return;
    try {
      setIsSavingProfile(true);
      setError(null);
      
      const expFloat = parseFloat(localExperience);
      const payload = {
        name: localName,
        email: localEmail,
        phone: localPhone,
        location: localLocation,
        linkedin_url: localLinkedin,
        total_experience_years: isNaN(expFloat) ? null : expFloat,
        raw_sections: {} as Record<string, { text: string; confidence: string }>
      };
      
      Object.keys(localSections).forEach(key => {
        payload.raw_sections[key] = {
          text: localSections[key],
          confidence: localSections[key].length > 20 ? 'high' : 'low'
        };
      });

      await updateCandidateDetails(parsedData.candidate_id, payload);
    } catch (err: any) {
      console.error(err);
      setError("Failed to save profile changes to database.");
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleCompareScore = async () => {
    if (!parsedData) return;
    await handleSaveProfile();
    window.location.href = `/score?candidate_id=${parsedData.candidate_id}`;
  };

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      setError(null);
      setUploadData(null);
      setParsedData(null);
      setUploadProgress(0);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    },
    maxFiles: 1,
  });

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setUploadProgress(15);

    try {
      const data = await uploadCV(file, (progressEvent) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(15 + Math.round(percentCompleted * 0.8));
      });
      
      setUploadProgress(100);
      setUploadData(data);
      setCandidateId(data.candidate_id);
      setIsUploading(false);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to upload and extract text from CV.');
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleParse = async () => {
    if (!uploadData?.candidate_id) return;

    setIsParsing(true);
    setError(null);

    try {
      const data = await parseCV(uploadData.candidate_id);
      setParsedData(data);
      setCandidateName(data.name);
      setJobId(null);
      setAtsScore(null);
      setIsParsing(false);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to parse CV and extract skills.');
      setIsParsing(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadProgress(0);
    setUploadData(null);
    setParsedData(null);
    setError(null);
  };

  const getParsedDegrees = (eduText?: string) => {
    if (!eduText) return [];
    const degreeRegex = /\b(bachelor|master|phd|doctorate|b\.s|m\.s|b\.sc|m\.sc|b\.a|m\.a|mba|associate|degree|diploma)\b/gi;
    const matches = eduText.match(degreeRegex) || [];
    return Array.from(new Set(matches.map(m => m.toUpperCase())));
  };

  return (
    <main className="min-h-screen flex flex-col items-center py-12 px-4 md:px-8">
      <div className="max-w-4xl w-full z-10 space-y-8 animate-fadeInUp">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-badge text-sm font-semibold">
            <Sparkles className="w-4 h-4" /> CV Platform Parser
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight text-[var(--text-primary)]">
            Resume Extraction Engine
          </h1>
          <p className="text-[var(--text-secondary)] max-w-xl mx-auto text-base">
            Upload your resume, extract raw structural contents in real-time, and run advanced skill normalization against ESCO standards.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-center gap-3 p-4 rounded-2xl bg-red-50 border border-red-200 text-red-600 text-sm animate-scaleIn">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <div className="font-medium">{error}</div>
          </div>
        )}

        {/* Upload Zone & Actions */}
        {!uploadData && (
          <div className="glass-card-solid p-0 overflow-hidden animate-fadeInUp">
            <div className="p-6 pb-4">
              <h2 className="text-lg font-bold text-[var(--text-primary)]">Upload your Resume</h2>
              <p className="text-sm text-[var(--text-secondary)] mt-1">PDF and DOCX formats are supported. Maximum file size is 10MB.</p>
            </div>
            <div className="px-6 pb-6 space-y-6">
              <div 
                {...getRootProps()} 
                className={`border-2 border-dashed rounded-2xl p-12 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all duration-300 ${
                  isDragActive 
                    ? 'border-black/30 bg-black/[0.03] scale-[1.01]' 
                    : 'border-black/10 hover:border-black/20 bg-white/40 hover:bg-white/60'
                } ${isDragActive ? 'animate-borderPulse' : ''}`}
              >
                <input {...getInputProps()} />
                <div className={`p-4 rounded-2xl bg-black/[0.04] text-[var(--text-secondary)] transition-transform duration-300 ${isDragActive ? 'animate-float' : ''}`}>
                  <Upload className="w-8 h-8" />
                </div>
                {file ? (
                  <div className="text-center space-y-1">
                    <p className="font-bold text-[var(--text-primary)]">{file.name}</p>
                    <p className="text-xs text-[var(--text-tertiary)]">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                ) : (
                  <div className="text-center space-y-1">
                    <p className="font-semibold text-[var(--text-primary)]">
                      Drag & drop your CV file here, or click to browse
                    </p>
                    <p className="text-xs text-[var(--text-tertiary)]">
                      Supports PDF, DOCX (Max 10MB)
                    </p>
                  </div>
                )}
              </div>

              {isUploading && (
                <div className="space-y-2 animate-fadeIn">
                  <div className="flex justify-between text-xs font-semibold text-[var(--text-secondary)]">
                    <span>Extracting raw text...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <div className="w-full bg-black/[0.04] rounded-full h-2 overflow-hidden">
                    <div 
                      className="bg-black h-full rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
            {file && (
              <div className="flex justify-end gap-3 border-t border-black/[0.04] px-6 py-4">
                <Button 
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="btn-primary px-6 py-2 rounded-xl text-sm"
                >
                  {isUploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Uploading...
                    </>
                  ) : 'Upload CV'}
                </Button>
              </div>
            )}
          </div>
        )}

        {/* Uploaded View (Raw Text Preview) */}
        {uploadData && (
          <div className="space-y-6 stagger-children">
            <div className="glass-card-solid p-0 overflow-hidden">
              <div className="flex flex-row items-center justify-between p-6 pb-5 border-b border-black/[0.04]">
                <div className="space-y-1">
                  <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-500" />
                    CV Uploaded Successfully
                  </h2>
                  <p className="text-sm text-[var(--text-secondary)]">
                    Candidate file: <span className="text-[var(--text-primary)] font-semibold">{uploadData.file_name}</span>
                  </p>
                </div>
                <div className="text-right">
                  <span className="glass-badge text-xs px-3 py-1.5">
                    ID: {uploadData.candidate_id.substring(0, 8)}...
                  </span>
                </div>
              </div>
              <div className="p-6 space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold text-[var(--text-secondary)] flex items-center gap-2">
                    <FileText className="w-4 h-4" /> Extracted Raw Text Preview ({uploadData.char_count} chars)
                  </label>
                  <textarea
                    readOnly
                    value={uploadData.raw_text}
                    className="glass-input w-full h-48 p-4 text-xs font-mono text-[var(--text-secondary)] resize-y"
                  />
                </div>
              </div>
              <div className="flex justify-between border-t border-black/[0.04] px-6 py-4">
                <Button 
                  variant="ghost" 
                  onClick={handleReset}
                  disabled={isParsing}
                  className="btn-secondary px-4 py-2 rounded-xl text-sm"
                >
                  Upload Another File
                </Button>
                {!parsedData && (
                  <Button
                    onClick={handleParse}
                    disabled={isParsing}
                    className="btn-primary px-6 py-2 rounded-xl text-sm"
                  >
                    {isParsing ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Analyzing CV...
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-4 h-4 mr-2" /> Analyze CV
                      </>
                    )}
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Parsing Skeleton Loader */}
        {isParsing && (
          <div className="glass-card-solid p-6 space-y-4 animate-fadeIn">
            <div className="flex items-center gap-3">
              <RefreshCw className="w-5 h-5 animate-spin text-[var(--text-secondary)]" />
              <span className="text-sm font-semibold text-[var(--text-secondary)]">Analyzing your CV with NLP pipeline...</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="shimmer-loader h-10 rounded-xl" />
              <div className="shimmer-loader h-10 rounded-xl" />
              <div className="shimmer-loader h-10 rounded-xl" />
              <div className="shimmer-loader h-10 rounded-xl" />
            </div>
            <div className="shimmer-loader h-24 rounded-xl" />
            <div className="shimmer-loader h-24 rounded-xl" />
          </div>
        )}

        {/* CV Parser Preview Panel */}
        <div className="glass-card-solid p-0 overflow-hidden mt-8 animate-fadeInUp" style={{ animationDelay: '100ms' }}>
          <div className="p-6 border-b border-black/[0.04]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  Structured CV Parser Preview
                </h2>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  {parsedData 
                    ? "Verify the automatically extracted fields, parsed sections, and detected NLP entities." 
                    : "Upload and analyze a CV to see the extracted sections and named entities populate here."}
                </p>
              </div>
              <div className="flex gap-2">
                <span className={`glass-badge px-3 py-1.5 text-xs font-semibold ${
                  parsedData 
                    ? "!bg-green-50 !border-green-200 !text-green-700" 
                    : ""
                }`}>
                  {parsedData ? "✓ Parsed" : "○ Empty"}
                </span>
              </div>
            </div>

            {/* Tab Selector */}
            <div className="flex gap-6 mt-6 border-b border-black/[0.04] pb-0 text-sm">
              <button
                type="button"
                onClick={() => setPreviewTab('profile')}
                className={`pb-3 font-semibold tracking-wide transition-all border-b-2 ${
                  previewTab === 'profile' 
                    ? 'border-[var(--text-primary)] text-[var(--text-primary)]' 
                    : 'border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                Personal Details
              </button>
              <button
                type="button"
                onClick={() => setPreviewTab('sections')}
                className={`pb-3 font-semibold tracking-wide transition-all border-b-2 ${
                  previewTab === 'sections' 
                    ? 'border-[var(--text-primary)] text-[var(--text-primary)]' 
                    : 'border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                Extracted Sections
              </button>
              <button
                type="button"
                onClick={() => setPreviewTab('entities')}
                className={`pb-3 font-semibold tracking-wide transition-all border-b-2 ${
                  previewTab === 'entities' 
                    ? 'border-[var(--text-primary)] text-[var(--text-primary)]' 
                    : 'border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]'
                }`}
              >
                Granular Entities (NER)
              </button>
            </div>
          </div>

          <div className="p-6">
            {/* Tab 1: Profile & Contact Details */}
            {previewTab === 'profile' && (
              <div className="space-y-6 animate-fadeIn">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 stagger-children">
                  {/* Name */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5" /> Full Name
                    </label>
                    <input
                      type="text"
                      placeholder="Waiting for CV..."
                      value={localName}
                      onChange={(e) => setLocalName(e.target.value)}
                      className="glass-input h-11 w-full px-4 text-sm font-medium"
                    />
                  </div>

                  {/* Email */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5" /> Email Address
                    </label>
                    <input
                      type="text"
                      placeholder="Waiting for CV..."
                      value={localEmail}
                      onChange={(e) => setLocalEmail(e.target.value)}
                      className="glass-input h-11 w-full px-4 text-sm font-medium"
                    />
                  </div>

                  {/* Phone */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                      <Phone className="w-3.5 h-3.5" /> Phone Number
                    </label>
                    <input
                      type="text"
                      placeholder="Waiting for CV..."
                      value={localPhone}
                      onChange={(e) => setLocalPhone(e.target.value)}
                      className="glass-input h-11 w-full px-4 text-sm font-medium"
                    />
                  </div>

                  {/* Location */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5" /> Location
                    </label>
                    <input
                      type="text"
                      placeholder="Waiting for CV..."
                      value={localLocation}
                      onChange={(e) => setLocalLocation(e.target.value)}
                      className="glass-input h-11 w-full px-4 text-sm font-medium"
                    />
                  </div>

                  {/* LinkedIn */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                      <Globe className="w-3.5 h-3.5" /> LinkedIn URL
                    </label>
                    <input
                      type="text"
                      placeholder="Waiting for CV..."
                      value={localLinkedin}
                      onChange={(e) => setLocalLinkedin(e.target.value)}
                      className="glass-input h-11 w-full px-4 text-sm font-medium"
                    />
                  </div>

                  {/* Total Experience */}
                  <div className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                      <Briefcase className="w-3.5 h-3.5" /> Total Experience (Years)
                    </label>
                    <input
                      type="text"
                      placeholder="Waiting for CV..."
                      value={localExperience}
                      onChange={(e) => setLocalExperience(e.target.value)}
                      className="glass-input h-11 w-full px-4 text-sm font-medium"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Extracted CV Sections */}
            {previewTab === 'sections' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fadeIn stagger-children">
                {[
                  { key: 'summary', label: 'Summary', icon: FileText, placeholder: 'Extracted Summary will appear here...' },
                  { key: 'experience', label: 'Experience Section', icon: Briefcase, placeholder: 'Extracted Experience section will appear here...' },
                  { key: 'education', label: 'Education Section', icon: GraduationCap, placeholder: 'Extracted Education section will appear here...' },
                  { key: 'projects', label: 'Projects Section', icon: BookOpen, placeholder: 'Extracted Projects section will appear here...' },
                  { key: 'certifications', label: 'Certifications', icon: Award, placeholder: 'Extracted Certifications will appear here...' },
                  { key: 'languages', label: 'Languages', icon: Globe, placeholder: 'Extracted Languages will appear here...' },
                ].map(({ key, label, icon: Icon, placeholder }) => (
                  <div key={key} className="space-y-2">
                    <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                      <Icon className="w-3.5 h-3.5" /> {label}
                    </label>
                    <textarea
                      placeholder={placeholder}
                      value={localSections[key] || ''}
                      onChange={(e) => handleSectionChange(key, e.target.value)}
                      className="glass-input w-full h-28 p-3 text-xs font-mono resize-y"
                    />
                  </div>
                ))}

                {/* Achievements — full width */}
                <div className="space-y-2 md:col-span-2">
                  <label className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                    <Award className="w-3.5 h-3.5" /> Achievements Section
                  </label>
                  <textarea
                    placeholder="Extracted Achievements will appear here..."
                    value={localSections.achievements || ''}
                    onChange={(e) => handleSectionChange('achievements', e.target.value)}
                    className="glass-input w-full h-24 p-3 text-xs font-mono resize-y"
                  />
                </div>
              </div>
            )}

            {/* Tab 3: Granular Entities (NER) */}
            {previewTab === 'entities' && (
              <div className="space-y-6 animate-fadeIn stagger-children">
                {/* Names Detected */}
                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                    <User className="w-3.5 h-3.5" /> Personal Names Identified
                  </h4>
                  <div className="flex flex-wrap gap-2 p-4 rounded-2xl bg-white/50 border border-black/[0.04] min-h-[48px]">
                    {parsedData?.raw_entities?.name ? (
                      <span className="glass-badge text-xs px-3 py-1 font-mono">
                        {parsedData.raw_entities.name}
                      </span>
                    ) : (
                      <span className="text-xs text-[var(--text-tertiary)] italic select-none">No names parsed yet.</span>
                    )}
                  </div>
                </div>

                {/* Locations */}
                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                    <MapPin className="w-3.5 h-3.5" /> Locations Detected
                  </h4>
                  <div className="flex flex-wrap gap-2 p-4 rounded-2xl bg-white/50 border border-black/[0.04] min-h-[48px]">
                    {parsedData?.raw_entities?.location ? (
                      <span className="glass-badge text-xs px-3 py-1 font-mono">
                        {parsedData.raw_entities.location}
                      </span>
                    ) : (
                      <span className="text-xs text-[var(--text-tertiary)] italic select-none">No locations parsed yet.</span>
                    )}
                  </div>
                </div>

                {/* Universities */}
                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                    <GraduationCap className="w-3.5 h-3.5" /> Universities Detected
                  </h4>
                  <div className="flex flex-wrap gap-2 p-4 rounded-2xl bg-white/50 border border-black/[0.04] min-h-[48px]">
                    {parsedData?.raw_entities?.organizations ? (
                      parsedData.raw_entities.organizations
                        .filter(org => /university|college|institute|school|polytechnic/i.test(org))
                        .map((univ, idx) => (
                          <span key={idx} className="glass-badge text-xs px-3 py-1 font-mono">
                            {univ}
                          </span>
                        ))
                    ) : null}
                    {(!parsedData?.raw_entities?.organizations || 
                      parsedData.raw_entities.organizations.filter(org => /university|college|institute|school|polytechnic/i.test(org)).length === 0) && (
                      <span className="text-xs text-[var(--text-tertiary)] italic select-none">No academic organizations identified.</span>
                    )}
                  </div>
                </div>

                {/* Companies */}
                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                    <Building className="w-3.5 h-3.5" /> Companies Detected
                  </h4>
                  <div className="flex flex-wrap gap-2 p-4 rounded-2xl bg-white/50 border border-black/[0.04] min-h-[48px]">
                    {parsedData?.raw_entities?.organizations ? (
                      parsedData.raw_entities.organizations
                        .filter(org => !/university|college|institute|school|polytechnic/i.test(org))
                        .map((comp, idx) => (
                          <span key={idx} className="glass-badge text-xs px-3 py-1 font-mono">
                            {comp}
                          </span>
                        ))
                    ) : null}
                    {(!parsedData?.raw_entities?.organizations || 
                      parsedData.raw_entities.organizations.filter(org => !/university|college|institute|school|polytechnic/i.test(org)).length === 0) && (
                      <span className="text-xs text-[var(--text-tertiary)] italic select-none">No companies identified.</span>
                    )}
                  </div>
                </div>

                {/* Degrees */}
                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                    <GraduationCap className="w-3.5 h-3.5" /> Academic Degrees Detected
                  </h4>
                  <div className="flex flex-wrap gap-2 p-4 rounded-2xl bg-white/50 border border-black/[0.04] min-h-[48px]">
                    {parsedData?.raw_sections?.education?.text && getParsedDegrees(parsedData.raw_sections.education.text).length > 0 ? (
                      getParsedDegrees(parsedData.raw_sections.education.text).map((deg, idx) => (
                        <span key={idx} className="glass-badge text-xs px-3 py-1 font-mono">
                          {deg}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-[var(--text-tertiary)] italic select-none">No academic degrees identified.</span>
                    )}
                  </div>
                </div>

                {/* Skills */}
                <div className="space-y-2">
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5" /> Skills Extracted ({parsedData?.skill_count || 0})
                  </h4>
                  <div className="flex flex-wrap gap-2 p-4 rounded-2xl bg-white/50 border border-black/[0.04] min-h-[48px]">
                    {parsedData?.skills && parsedData.skills.length > 0 ? (
                      parsedData.skills.map((skill, index) => (
                        <span 
                          key={index} 
                          className="glass-badge text-xs px-3 py-1 flex items-center gap-1.5 font-mono"
                        >
                          <span>{skill.normalized}</span>
                          {skill.confidence > 0 && (
                            <span className="text-[10px] font-bold text-[var(--text-secondary)] bg-black/[0.06] px-1.5 rounded">
                              {Math.round(skill.confidence * 100)}%
                            </span>
                          )}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-[var(--text-tertiary)] italic select-none">No skills parsed yet.</span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action Footer */}
          <div className="flex justify-end gap-3 border-t border-black/[0.04] px-6 py-4">
            <Button 
              onClick={handleReset}
              disabled={isSavingProfile || !parsedData}
              className="btn-secondary px-5 py-2 rounded-xl text-sm"
            >
              Clear and Restart
            </Button>
            <Button 
              onClick={handleSaveProfile}
              disabled={isSavingProfile || !parsedData}
              className="btn-secondary px-5 py-2 rounded-xl text-sm"
            >
              {isSavingProfile ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" /> Save Details
                </>
              )}
            </Button>
            <Button
              onClick={handleCompareScore}
              disabled={isSavingProfile || !parsedData}
              className="btn-primary px-5 py-2 rounded-xl text-sm"
            >
              Compare ATS Score
            </Button>
          </div>
        </div>
      </div>
    </main>
  );
}
