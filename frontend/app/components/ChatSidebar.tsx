'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Message } from '@/types';
import { sendChatMessage } from '@/lib/api';
import { parseNodeId } from '@/lib/utils';

interface ChatSidebarProps {
  onNodeHighlight?: (nodeIds: string[]) => void;
  onNodeClick?: (nodeId: string) => void;
}

export default function ChatSidebar({ onNodeHighlight, onNodeClick }: ChatSidebarProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage(input.trim());

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        nodeIds: response.node_ids,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      if (response.node_ids.length > 0) {
        onNodeHighlight?.(response.node_ids);
      }
    } catch (error) {
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Error: ${error instanceof Error ? error.message : 'Failed to send message'}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-6 border-b border-white/20">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-800">AI Assistant</h2>
            <p className="text-xs text-slate-600">Ask about your codebase</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center mt-12 animate-fade-in">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-100 to-indigo-100 flex items-center justify-center">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <p className="text-lg font-medium text-slate-800 mb-2">Start a conversation</p>
            <p className="text-sm text-slate-600 mb-6">Ask me anything about your codebase</p>
            <div className="text-left space-y-2 max-w-xs mx-auto">
              <p className="text-xs font-semibold text-slate-700 mb-2">Try asking:</p>
              {[
                'Show me all classes',
                'Find functions that call authenticate',
                'What files contain the User class?'
              ].map((example, i) => (
                <button
                  key={i}
                  onClick={() => setInput(example)}
                  className="w-full text-left px-3 py-2 text-xs glass rounded-lg hover:bg-white/90 transition-all duration-200 text-slate-700"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            message={message}
            onNodeClick={onNodeClick}
            onNodeHover={(nodeId) => onNodeHighlight?.(nodeId ? [nodeId] : [])}
          />
        ))}

        {loading && (
          <div className="flex items-center gap-3 text-slate-600 animate-fade-in">
            <div className="flex gap-1">
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-sm">Thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-6 border-t border-white/20">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask a question..."
            className="flex-1 p-3 glass rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-800 placeholder-slate-400 transition-all duration-200"
            rows={2}
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="px-5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 active:scale-95 shadow-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

interface MessageBubbleProps {
  message: Message;
  onNodeClick?: (nodeId: string) => void;
  onNodeHover?: (nodeId: string | null) => void;
}

function MessageBubble({ message, onNodeClick, onNodeHover }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-in`}>
      <div
        className={`max-w-[85%] rounded-2xl p-4 ${
          isUser 
            ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg' 
            : 'glass text-slate-800 shadow-md'
        }`}
      >
        <div className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</div>

        {message.nodeIds && message.nodeIds.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.nodeIds.map((nodeId) => (
              <NodeChip
                key={nodeId}
                nodeId={nodeId}
                onClick={() => onNodeClick?.(nodeId)}
                onMouseEnter={() => onNodeHover?.(nodeId)}
                onMouseLeave={() => onNodeHover?.(null)}
              />
            ))}
          </div>
        )}

        <div className={`text-xs mt-2 ${isUser ? 'text-blue-100' : 'text-slate-500'}`}>
          {message.timestamp.toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
}

interface NodeChipProps {
  nodeId: string;
  onClick?: () => void;
  onMouseEnter?: () => void;
  onMouseLeave?: () => void;
}

function NodeChip({ nodeId, onClick, onMouseEnter, onMouseLeave }: NodeChipProps) {
  const parsed = parseNodeId(nodeId);
  const displayName = parsed.entityName || parsed.filePath;
  const displayType = parsed.entityType || 'file';

  return (
    <button
      onClick={onClick}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      className="px-3 py-1.5 bg-white/90 hover:bg-white text-slate-700 text-xs rounded-lg border border-slate-200 transition-all duration-200 cursor-pointer transform hover:scale-105 shadow-sm hover:shadow-md"
      title={`Click to inspect ${displayType}: ${displayName}`}
    >
      <span className="font-medium">{displayName}</span>
    </button>
  );
}
