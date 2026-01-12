'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

// File Node
export const FileNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`px-4 py-3 rounded-xl shadow-lg transition-all duration-200 ${
        selected
          ? 'ring-2 ring-blue-500 ring-offset-2 scale-110'
          : 'hover:scale-105'
      }`}
      style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        minWidth: '180px',
      }}
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-white" />
      
      <div className="flex items-center gap-2 mb-1">
        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
        <span className="text-xs font-semibold text-white/80 uppercase tracking-wide">File</span>
      </div>
      
      <div className="text-white font-semibold text-sm truncate" title={data.label}>
        {data.label}
      </div>
      
      {data.language && (
        <div className="mt-1 text-xs text-white/70">
          {data.language}
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-white" />
    </div>
  );
});

FileNode.displayName = 'FileNode';

// Class Node
export const ClassNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`px-4 py-3 rounded-xl shadow-lg transition-all duration-200 ${
        selected
          ? 'ring-2 ring-purple-500 ring-offset-2 scale-110'
          : 'hover:scale-105'
      }`}
      style={{
        background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
        minWidth: '160px',
      }}
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-white" />
      
      <div className="flex items-center gap-2 mb-1">
        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <span className="text-xs font-semibold text-white/80 uppercase tracking-wide">Class</span>
      </div>
      
      <div className="text-white font-bold text-sm truncate" title={data.label}>
        {data.label}
      </div>
      
      {data.start_line && (
        <div className="mt-1 text-xs text-white/70">
          Lines {data.start_line}-{data.end_line}
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-white" />
    </div>
  );
});

ClassNode.displayName = 'ClassNode';

// Function Node
export const FunctionNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div
      className={`px-4 py-3 rounded-xl shadow-lg transition-all duration-200 ${
        selected
          ? 'ring-2 ring-green-500 ring-offset-2 scale-110'
          : 'hover:scale-105'
      }`}
      style={{
        background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        minWidth: '150px',
      }}
    >
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-white" />
      
      <div className="flex items-center gap-2 mb-1">
        <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
        </svg>
        <span className="text-xs font-semibold text-white/80 uppercase tracking-wide">Function</span>
      </div>
      
      <div className="text-white font-semibold text-sm truncate" title={data.label}>
        {data.label}
      </div>
      
      {data.args && (
        <div className="mt-1 text-xs text-white/70 truncate" title={data.args}>
          ({data.args})
        </div>
      )}
      
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-white" />
    </div>
  );
});

FunctionNode.displayName = 'FunctionNode';
