"use client";

import React, { createContext, useContext, useState, useEffect } from 'react';

export interface AppState {
  candidateId: string | null;
  candidateName: string | null;
  jobId: string | null;
  atsScore: number | null;
}

interface AppContextType {
  state: AppState;
  setCandidateId: (id: string | null) => void;
  setCandidateName: (name: string | null) => void;
  setJobId: (id: string | null) => void;
  setAtsScore: (score: number | null) => void;
  clearState: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AppState>({
    candidateId: null,
    candidateName: null,
    jobId: null,
    atsScore: null,
  });

  // Hydrate from localStorage once mounted
  useEffect(() => {
    try {
      const stored = localStorage.getItem('cv_platform_state');
      if (stored) {
        setState(JSON.parse(stored));
      }
    } catch (e) {
      console.error('Failed to load local storage state:', e);
    }
  }, []);

  // Persist state to localStorage on state changes
  useEffect(() => {
    try {
      localStorage.setItem('cv_platform_state', JSON.stringify(state));
    } catch (e) {
      console.error('Failed to save state to local storage:', e);
    }
  }, [state]);

  const setCandidateId = (id: string | null) => {
    setState(prev => ({ ...prev, candidateId: id }));
  };

  const setCandidateName = (name: string | null) => {
    setState(prev => ({ ...prev, candidateName: name }));
  };

  const setJobId = (id: string | null) => {
    setState(prev => ({ ...prev, jobId: id }));
  };

  const setAtsScore = (score: number | null) => {
    setState(prev => ({ ...prev, atsScore: score }));
  };

  const clearState = () => {
    setState({
      candidateId: null,
      candidateName: null,
      jobId: null,
      atsScore: null,
    });
  };

  return (
    <AppContext.Provider value={{
      state,
      setCandidateId,
      setCandidateName,
      setJobId,
      setAtsScore,
      clearState
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppStore() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppStore must be used within an AppProvider');
  }
  return context;
}
