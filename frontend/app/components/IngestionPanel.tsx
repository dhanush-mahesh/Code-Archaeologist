'use client';

import React, { useState } from 'react';
import { ingestRepository, JobStatus } from '@/lib/api';
import { isValidGitHubUrl } from '@/lib/utils';

interface IngestionPanelProps {
  onIngestionComplete?: () => void;
}

export default function IngestionPanel({ onIngestionComplete }: IngestionPanelProps) {
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleIngest = async () => {
    if (!repoUrl.trim()) {
      setError('Please enter a repository URL');
      return;
    }

    if (!isValidGitHubUrl(repoUrl)) {
      setError('Please enter a valid GitHub repository URL');
      return;
    }

    setLoading(true);
    setError(null);
    setStatus(null);

    try {
      const result = await ingestRepository(repoUrl.trim());
      setStatus(result);

      if (result.status === 'success') {
        onIngestionComplete?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to ingest repository');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !loading) {
      handleIngest();
    }
  };

  return (
    <div className="glass rounded-2xl p-8 shadow-2xl max-w-3xl mx-auto animate-in">
      <div className="flex items-center gap-4 mb-6">
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 flex items-center justify-center shadow-lg">
          <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        </div>
        <div>
          <h2 className="text-2xl font-bold gradient-text">Ingest Repository</h2>
          <p className="text-sm text-slate-600">
            Enter a GitHub repository URL to analyze its code structure
          </p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="relative">
          <input
            type="text"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="https://github.com/username/repository"
            className="w-full p-4 glass rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 placeholder-slate-400 transition-all duration-200"
            disabled={loading}
          />
          {repoUrl && isValidGitHubUrl(repoUrl) && (
            <div className="absolute right-4 top-1/2 -translate-y-1/2">
              <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          )}
        </div>

        <button
          onClick={handleIngest}
          disabled={loading || !repoUrl.trim()}
          className="w-full btn-primary py-4 text-base font-semibold"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-3">
              <div className="w-5 h-5 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
              Ingesting Repository...
            </span>
          ) : (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              Ingest Repository
            </span>
          )}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500 rounded-lg animate-in">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="font-semibold text-red-800">Error</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {status && (
        <div
          className={`mt-4 p-4 border-l-4 rounded-lg animate-in ${
            status.status === 'success'
              ? 'bg-green-50 border-green-500'
              : status.status === 'error'
              ? 'bg-red-50 border-red-500'
              : 'bg-blue-50 border-blue-500'
          }`}
        >
          <div className="flex items-start gap-3">
            {status.status === 'success' ? (
              <svg className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            <div className="flex-1">
              <p className={`font-semibold capitalize ${
                status.status === 'success' ? 'text-green-800' : 
                status.status === 'error' ? 'text-red-800' : 'text-blue-800'
              }`}>
                {status.status}
              </p>
              <p className={`text-sm ${
                status.status === 'success' ? 'text-green-700' : 
                status.status === 'error' ? 'text-red-700' : 'text-blue-700'
              }`}>
                {status.message}
              </p>

              {status.status === 'success' && (
                <div className="mt-3 grid grid-cols-3 gap-3">
                  <div className="glass rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-blue-600">{status.files_processed}</div>
                    <div className="text-xs text-slate-600">Files</div>
                  </div>
                  <div className="glass rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-green-600">{status.nodes_created}</div>
                    <div className="text-xs text-slate-600">Nodes</div>
                  </div>
                  <div className="glass rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-purple-600">{status.edges_created}</div>
                    <div className="text-xs text-slate-600">Edges</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="mt-6 p-4 glass rounded-xl">
        <p className="text-xs font-semibold text-slate-700 mb-2">✨ Supported repositories:</p>
        <ul className="text-xs text-slate-600 space-y-1">
          <li className="flex items-center gap-2">
            <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Public GitHub repositories
          </li>
          <li className="flex items-center gap-2">
            <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Python (.py) and JavaScript (.js) files
          </li>
          <li className="flex items-center gap-2">
            <svg className="w-3 h-3 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Automatically skips node_modules and virtual environments
          </li>
        </ul>
      </div>
    </div>
  );
}
