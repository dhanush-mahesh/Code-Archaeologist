'use client';

import React, { useEffect, useState } from 'react';
import { parseNodeId } from '@/lib/utils';

interface CodeInspectorProps {
  nodeId: string | null;
  onClose: () => void;
}

interface NodeDetails {
  id: string;
  type: 'file' | 'class' | 'function';
  name: string;
  filePath: string;
  startLine?: number;
  endLine?: number;
  language?: string;
  args?: string;
  docstring?: string;
}

export default function CodeInspector({ nodeId, onClose }: CodeInspectorProps) {
  const [details, setDetails] = useState<NodeDetails | null>(null);
  const [code, setCode] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!nodeId) {
      setDetails(null);
      setCode('');
      return;
    }

    const fetchNodeDetails = async () => {
      setLoading(true);
      setError(null);

      try {
        // Parse node ID to get basic info
        const parsed = parseNodeId(nodeId);
        const displayName = parsed.entityName || parsed.filePath;
        const displayType = (parsed.entityType || 'file') as 'file' | 'class' | 'function';
        
        // In a real implementation, we would fetch the actual code from the backend
        // For now, we'll show the node details
        setDetails({
          id: nodeId,
          type: displayType,
          name: displayName,
          filePath: parsed.filePath,
        });

        // Mock code display - in production, fetch from backend
        setCode(`// Code for ${displayName}\n// File: ${parsed.filePath}\n\n// Code would be fetched from the backend here`);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load node details');
      } finally {
        setLoading(false);
      }
    };

    fetchNodeDetails();
  }, [nodeId]);

  if (!nodeId) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white border-l shadow-lg z-50 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b flex items-center justify-between bg-gray-50">
        <h2 className="text-lg font-semibold">Code Inspector</h2>
        <button
          onClick={onClose}
          className="p-1 hover:bg-gray-200 rounded transition-colors"
          title="Close"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-500 text-red-700">
            <p className="font-semibold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        {details && !loading && !error && (
          <div className="p-4 space-y-4">
            {/* Node Info */}
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded font-semibold uppercase">
                  {details.type}
                </span>
                <h3 className="text-lg font-semibold">{details.name}</h3>
              </div>

              <div className="text-sm space-y-1 text-gray-600">
                <div>
                  <span className="font-semibold">File:</span> {details.filePath}
                </div>
                {details.startLine && details.endLine && (
                  <div>
                    <span className="font-semibold">Lines:</span> {details.startLine}-
                    {details.endLine}
                  </div>
                )}
                {details.args && (
                  <div>
                    <span className="font-semibold">Arguments:</span> {details.args}
                  </div>
                )}
              </div>

              {details.docstring && (
                <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                  <div className="font-semibold mb-1">Documentation:</div>
                  <div className="text-gray-700 whitespace-pre-wrap">{details.docstring}</div>
                </div>
              )}
            </div>

            {/* Code Preview */}
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-gray-800 text-white px-3 py-2 text-sm font-mono">
                Code Preview
              </div>
              <pre className="p-4 bg-gray-50 text-sm font-mono overflow-x-auto">
                <code>{code}</code>
              </pre>
            </div>

            {/* Actions */}
            <div className="space-y-2">
              <button className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors text-sm">
                View Full File
              </button>
              <button className="w-full px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 transition-colors text-sm">
                Find References
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
