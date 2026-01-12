'use client';

import React, { useCallback, useEffect } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  Panel,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { GraphNode, GraphEdge } from '@/types';
import { FileNode, ClassNode, FunctionNode } from './CustomNodes';

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  highlightedNodes?: Set<string>;
  onNodeClick?: (nodeId: string) => void;
  onNodeHover?: (nodeId: string | null) => void;
}

const nodeTypes = {
  file: FileNode,
  class: ClassNode,
  function: FunctionNode,
};

export default function GraphCanvas({
  nodes: graphNodes,
  edges: graphEdges,
  highlightedNodes = new Set(),
  onNodeClick,
  onNodeHover,
}: GraphCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Convert graph data to ReactFlow format
  useEffect(() => {
    const flowNodes: Node[] = graphNodes.map((node) => ({
      id: node.id,
      type: node.type,
      position: node.position,
      data: {
        ...node.data,
      },
      selected: highlightedNodes.has(node.id),
    }));

    const flowEdges: Edge[] = graphEdges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: highlightedNodes.has(edge.source) || highlightedNodes.has(edge.target),
      style: {
        stroke: edge.type === 'CALLS' 
          ? '#f093fb' 
          : edge.type === 'DEFINES' 
          ? '#4facfe' 
          : '#667eea',
        strokeWidth: highlightedNodes.has(edge.source) || highlightedNodes.has(edge.target) ? 3 : 2,
        opacity: highlightedNodes.size > 0 
          ? (highlightedNodes.has(edge.source) || highlightedNodes.has(edge.target) ? 1 : 0.3)
          : 0.6,
      },
      labelStyle: {
        fontSize: 11,
        fontWeight: 600,
        fill: '#64748b',
      },
      labelBgStyle: {
        fill: 'white',
        fillOpacity: 0.9,
      },
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [graphNodes, graphEdges, highlightedNodes, setNodes, setEdges]);

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onNodeClick?.(node.id);
    },
    [onNodeClick]
  );

  const handleNodeMouseEnter = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      onNodeHover?.(node.id);
    },
    [onNodeHover]
  );

  const handleNodeMouseLeave = useCallback(() => {
    onNodeHover?.(null);
  }, [onNodeHover]);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        onNodeMouseEnter={handleNodeMouseEnter}
        onNodeMouseLeave={handleNodeMouseLeave}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        attributionPosition="bottom-left"
        minZoom={0.1}
        maxZoom={2}
      >
        <Background 
          variant={BackgroundVariant.Dots} 
          gap={20} 
          size={1}
          color="#cbd5e1"
        />
        <Controls className="glass rounded-xl shadow-lg" />
        <Panel position="top-left" className="glass rounded-xl p-4 shadow-lg animate-in">
          <div className="text-sm space-y-2">
            <div className="font-semibold text-slate-800 mb-3 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
              </svg>
              Legend
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-md shadow-sm" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }} />
              <span className="text-slate-700 text-xs">File</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-md shadow-sm" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }} />
              <span className="text-slate-700 text-xs">Class</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-md shadow-sm" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }} />
              <span className="text-slate-700 text-xs">Function</span>
            </div>
          </div>
        </Panel>
        <Panel position="top-right" className="glass rounded-xl p-4 shadow-lg animate-in">
          <div className="text-sm">
            <div className="font-semibold text-slate-800 mb-2 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Stats
            </div>
            <div className="space-y-1 text-slate-700">
              <div className="flex justify-between gap-4 text-xs">
                <span>Nodes:</span>
                <span className="font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">{nodes.length}</span>
              </div>
              <div className="flex justify-between gap-4 text-xs">
                <span>Edges:</span>
                <span className="font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">{edges.length}</span>
              </div>
            </div>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}
