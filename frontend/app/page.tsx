'use client';

import React, { useState, useEffect } from 'react';
import GraphCanvas from './components/GraphCanvas';
import ChatSidebar from './components/ChatSidebar';
import CodeInspector from './components/CodeInspector';
import IngestionPanel from './components/IngestionPanel';
import { getGraph } from '@/lib/api';
import { GraphNode, GraphEdge } from '@/types';

export default function Home() {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [showIngestion, setShowIngestion] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadGraph = async () => {
    setLoading(true);
    setError(null);

    try {
      const graphData = await getGraph();
      setNodes(graphData.nodes);
      setEdges(graphData.edges);
      
      if (graphData.nodes.length > 0) {
        setShowIngestion(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGraph();
  }, []);

  const handleNodeHighlight = (nodeIds: string[]) => {
    setHighlightedNodes(new Set(nodeIds));
  };

  const handleNodeClick = (nodeId: string) => {
    setSelectedNodeId(nodeId);
  };

  const handleIngestionComplete = () => {
    setShowIngestion(false);
    loadGraph();
  };

  return (
    <div className="flex h-screen overflow-hidden bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Modern Header with Glassmorphism */}
        <header className="glass border-b border-white/20 px-8 py-5 flex items-center justify-between backdrop-blur-xl animate-in">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold gradient-text">Code Archaeologist</h1>
              <p className="text-sm text-slate-600">Graph-RAG Application for Code Analysis</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowIngestion(!showIngestion)}
              className="btn-secondary"
            >
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                {showIngestion ? 'Hide Ingestion' : 'Ingest Repository'}
              </span>
            </button>
            <button
              onClick={loadGraph}
              disabled={loading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="flex items-center gap-2">
                <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                {loading ? 'Loading...' : 'Refresh'}
              </span>
            </button>
          </div>
        </header>

        {/* Ingestion Panel with Animation */}
        {showIngestion && (
          <div className="p-8 animate-in">
            <IngestionPanel onIngestionComplete={handleIngestionComplete} />
          </div>
        )}

        {/* Graph Canvas */}
        <div className="flex-1 relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center glass z-10 animate-fade-in">
              <div className="text-center">
                <div className="relative w-16 h-16 mx-auto mb-4">
                  <div className="absolute inset-0 rounded-full border-4 border-blue-200"></div>
                  <div className="absolute inset-0 rounded-full border-4 border-blue-600 border-t-transparent animate-spin"></div>
                </div>
                <p className="text-slate-700 font-medium">Loading graph...</p>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center glass z-10 animate-fade-in">
              <div className="text-center max-w-md p-8 glass rounded-2xl">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
                  <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h2 className="text-xl font-semibold mb-2 text-slate-800">Error Loading Graph</h2>
                <p className="text-slate-600 mb-6">{error}</p>
                <button
                  onClick={loadGraph}
                  className="btn-primary"
                >
                  Try Again
                </button>
              </div>
            </div>
          )}

          {!loading && !error && nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center animate-fade-in">
              <div className="text-center max-w-md p-8">
                <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center">
                  <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold mb-3 gradient-text">No Graph Data</h2>
                <p className="text-slate-600 mb-6">
                  Ingest a repository to start analyzing code structure
                </p>
                <button
                  onClick={() => setShowIngestion(true)}
                  className="btn-primary"
                >
                  Ingest Repository
                </button>
              </div>
            </div>
          )}

          {!loading && !error && nodes.length > 0 && (
            <GraphCanvas
              nodes={nodes}
              edges={edges}
              highlightedNodes={highlightedNodes}
              onNodeClick={handleNodeClick}
              onNodeHover={(nodeId) => handleNodeHighlight(nodeId ? [nodeId] : [])}
            />
          )}
        </div>
      </div>

      {/* Chat Sidebar with Glassmorphism */}
      <div className="w-96 glass border-l border-white/20">
        <ChatSidebar
          onNodeHighlight={handleNodeHighlight}
          onNodeClick={handleNodeClick}
        />
      </div>

      {/* Code Inspector */}
      {selectedNodeId && (
        <CodeInspector
          nodeId={selectedNodeId}
          onClose={() => setSelectedNodeId(null)}
        />
      )}
    </div>
  );
}
