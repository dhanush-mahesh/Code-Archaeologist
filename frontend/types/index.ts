/**
 * Type definitions for Code Archaeologist
 */

// ========== Graph Types ==========

export type NodeType = 'file' | 'class' | 'function';
export type EdgeType = 'CONTAINS' | 'DEFINES' | 'CALLS';

export interface GraphNode {
  id: string;
  type: NodeType;
  data: {
    label: string;
    path?: string;
    language?: string;
    name?: string;
    args?: string;
    docstring?: string;
    startLine?: number;
    endLine?: number;
    filePath?: string;
    [key: string]: any;
  };
  position: {
    x: number;
    y: number;
  };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ========== Chat Types ==========

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  nodeIds?: string[];
  timestamp: Date;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

// ========== Ingestion Types ==========

export interface IngestionJob {
  status: 'success' | 'error' | 'in_progress';
  message: string;
  jobId?: string;
  filesProcessed: number;
  nodesCreated: number;
  edgesCreated: number;
}

// ========== UI State Types ==========

export interface HighlightState {
  nodeIds: Set<string>;
  source: 'chat' | 'hover' | 'selection' | null;
}

export interface SelectedNode {
  nodeId: string;
  node: GraphNode;
}

export interface CodeInspectorState {
  isOpen: boolean;
  nodeId: string | null;
  code: string | null;
  language: string | null;
  highlightRange: [number, number] | null;
}

// ========== Component Props Types ==========

export interface GraphCanvasProps {
  data: GraphData;
  highlightedNodes: Set<string>;
  onNodeClick: (nodeId: string) => void;
  onNodeHover: (nodeId: string | null) => void;
}

export interface ChatSidebarProps {
  onNodeReference: (nodeIds: string[]) => void;
  onNodeHover: (nodeId: string | null) => void;
}

export interface CodeInspectorProps {
  nodeId: string | null;
  onClose: () => void;
}

export interface NodeChipProps {
  nodeId: string;
  onHover: (nodeId: string | null) => void;
  onClick: (nodeId: string) => void;
}

// ========== API Response Types ==========

export interface ApiError {
  error: string;
  detail?: string;
}

export interface HealthStatus {
  status: string;
  database: string;
  parser: string;
  ingestion: string;
  rag: string;
}

// ========== Layout Types ==========

export interface LayoutConfig {
  algorithm: 'dagre' | 'force' | 'grid';
  direction?: 'TB' | 'LR' | 'BT' | 'RL';
  spacing?: {
    node: number;
    rank: number;
  };
}

// ========== Filter Types ==========

export interface GraphFilters {
  nodeTypes: Set<NodeType>;
  edgeTypes: Set<EdgeType>;
  searchQuery: string;
}
