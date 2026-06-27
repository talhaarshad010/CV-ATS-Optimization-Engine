-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS candidates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    raw_text TEXT,
    status TEXT DEFAULT 'pending',
    candidate_name TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    location TEXT,
    total_experience_years NUMERIC(4,1),
    raw_sections JSONB,
    raw_entities JSONB,
    ner_method TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Index for faster queries by status
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);

-- Create extracted_skills table
CREATE TABLE IF NOT EXISTS extracted_skills (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    skill_raw TEXT NOT NULL,
    skill_normalized TEXT NOT NULL,
    confidence NUMERIC(3,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Disable Row-Level Security (RLS) on both tables for backend uploads
ALTER TABLE candidates DISABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_skills DISABLE ROW LEVEL SECURITY;

-- Auto-update updated_at for candidates
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER candidates_updated_at
    BEFORE UPDATE ON candidates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Create job_descriptions table
CREATE TABLE IF NOT EXISTS job_descriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    parsed_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Disable Row-Level Security (RLS) on job_descriptions for backend inserts
ALTER TABLE job_descriptions DISABLE ROW LEVEL SECURITY;

-- Create ats_scores table
CREATE TABLE IF NOT EXISTS ats_scores (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    candidate_id UUID REFERENCES candidates(id) ON DELETE CASCADE,
    job_id UUID REFERENCES job_descriptions(id) ON DELETE CASCADE,
    ats_score INTEGER NOT NULL,
    grade VARCHAR(10) NOT NULL,
    breakdown JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Disable Row-Level Security (RLS) on ats_scores for backend inserts
ALTER TABLE ats_scores DISABLE ROW LEVEL SECURITY;


