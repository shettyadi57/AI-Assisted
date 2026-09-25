import React, { createContext, useContext, useEffect, useState } from 'react';

export type PageId =
  | 'overview'
  | 'evidence'
  | 'fragments'
  | 'reconstruction'
  | 'validation'
  | 'reports'
  | 'settings';

export interface ApiHealth {
  status: string;
  version: string;
  api_version: string;
  current_phase: number;
  disclaimer: string;
}

export interface EndpointTestResult {
  endpoint: string;
  method: string;
  statusCode: number;
  phase: string;
  stage: string;
  detail: string;
  timestamp: string;
}

interface InvestigationContextType {
  currentPage: PageId;
  setCurrentPage: (page: PageId) => void;
  apiHealth: ApiHealth | null;
  isApiOnline: boolean;
  isLoadingHealth: boolean;
  healthError: string | null;
  refreshHealth: () => Promise<void>;
  lastEndpointTest: EndpointTestResult | null;
  testPhaseEndpoint: (endpoint: string, method?: string) => Promise<EndpointTestResult>;
}

const InvestigationContext = createContext<InvestigationContextType | undefined>(undefined);

export const InvestigationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentPage, setCurrentPage] = useState<PageId>('overview');
  const [apiHealth, setApiHealth] = useState<ApiHealth | null>(null);
  const [isLoadingHealth, setIsLoadingHealth] = useState<boolean>(true);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [lastEndpointTest, setLastEndpointTest] = useState<EndpointTestResult | null>(null);

  const refreshHealth = async () => {
    setIsLoadingHealth(true);
    try {
      const res = await fetch('/api/v1/health');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: ApiHealth = await res.json();
      setApiHealth(data);
      setHealthError(null);
    } catch (err: any) {
      setHealthError(err.message || 'API Unreachable');
      setApiHealth(null);
    } finally {
      setIsLoadingHealth(false);
    }
  };

  useEffect(() => {
    refreshHealth();
  }, []);

  const testPhaseEndpoint = async (endpoint: string, method: string = 'POST'): Promise<EndpointTestResult> => {
    try {
      const res = await fetch(endpoint, { method });
      const data = await res.json();
      const result: EndpointTestResult = {
        endpoint,
        method,
        statusCode: res.status,
        phase: data.phase || 'Unknown',
        stage: data.stage || 'Unknown',
        detail: data.detail || 'Deferred endpoint',
        timestamp: new Date().toLocaleTimeString(),
      };
      setLastEndpointTest(result);
      return result;
    } catch (err: any) {
      const errorResult: EndpointTestResult = {
        endpoint,
        method,
        statusCode: 0,
        phase: 'Network Error',
        stage: 'error',
        detail: err.message,
        timestamp: new Date().toLocaleTimeString(),
      };
      setLastEndpointTest(errorResult);
      return errorResult;
    }
  };

  return (
    <InvestigationContext.Provider
      value={{
        currentPage,
        setCurrentPage,
        apiHealth,
        isApiOnline: Boolean(apiHealth),
        isLoadingHealth,
        healthError,
        refreshHealth,
        lastEndpointTest,
        testPhaseEndpoint,
      }}
    >
      {children}
    </InvestigationContext.Provider>
  );
};

export const useInvestigation = (): InvestigationContextType => {
  const context = useContext(InvestigationContext);
  if (!context) {
    throw new Error('useInvestigation must be used within an InvestigationProvider');
  }
  return context;
};
