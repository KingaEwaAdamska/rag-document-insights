import { useState, useRef, useEffect, useCallback } from 'react';
import { Loader2 } from 'lucide-react';
import { api, type LLMProviderConfig, type ToolCall, type ConversationSummary, type Message } from '@/lib/api';
import { ChatSidebar } from '@/components/chat/ChatSidebar';
import { ChatHeader } from '@/components/chat/ChatHeader';
import { ChatInput } from '@/components/chat/ChatInput';
import { MessageBubble } from '@/components/chat/MessageBubble';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function uid() {
  return Math.random().toString(36).slice(2);
}

function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
        strong: ({ children }) => <strong className="font-semibold text-zinc-100">{children}</strong>,
        a: ({ children, href }) => (
          <a href={href} className="text-zinc-100 underline underline-offset-4 hover:text-white" target="_blank" rel="noreferrer">
            {children}
          </a>
        ),
        ul: ({ children }) => <ul className="list-disc ml-4 mb-3 space-y-1">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal ml-4 mb-3 space-y-1">{children}</ol>,
        li: ({ children }) => <li className="text-zinc-300">{children}</li>,
        h1: ({ children }) => <h1 className="text-xl font-bold text-zinc-100 mt-6 mb-3 first:mt-0">{children}</h1>,
        h2: ({ children }) => <h2 className="text-lg font-bold text-zinc-100 mt-5 mb-2 first:mt-0">{children}</h2>,
        h3: ({ children }) => <h3 className="text-base font-bold text-zinc-100 mt-4 mb-2 first:mt-0">{children}</h3>,
        code: ({ children, className, ...props }) => {
          const match = /language-(\w+)/.exec(className || '');
          const isInline = !className;
          
          if (!isInline && match) {
            return (
              <CodeBlockWidget 
                language={match[1]} 
                code={String(children).replace(/\n$/, '')} 
              />
            );
          }

          return isInline ? (
            <code className="bg-zinc-800 text-zinc-200 px-1.5 py-0.5 rounded text-[13px] font-mono border border-zinc-700" {...props}>
              {children}
            </code>
          ) : (
            <code className={className} {...props}>{children}</code>
          );
        },
        pre: ({ children }) => <>{children}</>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-zinc-700 pl-4 italic my-4 text-zinc-400">
            {children}
          </blockquote>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  );
}

function SuggestionChipsBlock({
  chips,
  onSelect,
}: {
  chips: string[];
  onSelect: (chip: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {chips.map((chip, i) => (
        <button
          key={i}
          onClick={() => onSelect(chip)}
          className="px-3 py-1.5 text-xs rounded-full border border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/60"
        >
          {chip}
        </button>
      ))}
    </div>
  );
}

function RetrievalPanelBlock({
  chunks,
}: {
  chunks: Array<{ document_name: string; excerpt: string; score: number; chunk_index: number }>;
}) {
  const [open, setOpen] = useState(false);

  if (chunks.length === 0) return null;

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="text-xs text-zinc-500 hover:text-zinc-300 underline-offset-2 hover:underline"
      >
        {open ? 'Hide sources' : `Show sources (${chunks.length})`}
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {chunks.map((c, i) => (
            <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-xs text-zinc-400 truncate">{c.document_name}</span>
                <span className="text-xs text-zinc-600 shrink-0">
                  chunk {c.chunk_index} · {Math.round(c.score * 100)}%
                </span>
              </div>
              <p className="text-xs text-zinc-500 line-clamp-3">{c.excerpt}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const TOOL_LABELS: Record<string, string> = {
  search_documents: 'Searching documents',
  list_documents: 'Listing documents',
  get_document_chunk: 'Fetching chunk context',
};

function ToolCallBlock({ toolCall }: { toolCall: ToolCall }) {
  const label = TOOL_LABELS[toolCall.tool] ?? toolCall.tool;
  const isRunning = toolCall.status === 'running';
  const isError = toolCall.status === 'error';

  return (
    <div className="mt-2 flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2 text-xs">
      {isRunning ? (
        <Loader2 className="h-3.5 w-3.5 text-zinc-500 animate-spin shrink-0" />
      ) : isError ? (
        <AlertCircle className="h-3.5 w-3.5 text-red-500 shrink-0" />
      ) : (
        <CheckCircle2 className="h-3.5 w-3.5 text-zinc-500 shrink-0" />
      )}
      <span className="text-zinc-400">{label}</span>
      {toolCall.result_summary && (
        <span className="text-zinc-600">- {toolCall.result_summary}</span>
      )}
    </div>
  );
}

function ActionButtonsBlock({ buttons }: { buttons: Array<{ label: string; primary?: boolean }> }) {
  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {buttons.map((btn, i) => (
        <button
          key={i}
          className={cn(
            'px-3.5 py-1.5 text-xs rounded-md font-medium',
            btn.primary ? 'bg-zinc-100 text-zinc-900' : 'border border-zinc-700 text-zinc-400',
          )}
        >
          {btn.label}
        </button>
      ))}
    </div>
  );
}

function CodeBlockWidget({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  function copy() {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="mt-3 border border-zinc-800 rounded-lg overflow-hidden">
      <div className="flex justify-between px-4 py-2 bg-zinc-900">
        <span className="text-xs text-zinc-500">{language}</span>
        <button onClick={copy} className="text-xs text-zinc-500 hover:text-zinc-300">
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="p-4 text-xs text-zinc-300 bg-zinc-950 overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );
}

// ── Message Bubble ─────────────────────────────────────────────────────────

function MessageBubble({
  message,
  onChipClick,
}: {
  message: Message | (Message & { streaming?: boolean });
  onChipClick: (text: string) => void;
}) {
  const isUser = message.role === 'user';

  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'h-7 w-7 rounded-full flex items-center justify-center shrink-0',
          isUser ? 'bg-zinc-700 text-xs' : 'bg-zinc-800',
        )}
      >
        {isUser ? 'U' : <Bot className="h-3.5 w-3.5" />}
      </div>

      <div className="flex-1 min-w-0">
        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm max-w-[90%] break-words',
            isUser ? 'bg-zinc-800 text-zinc-100 ml-auto' : 'text-zinc-300',
          )}
        >
          <MarkdownContent content={message.content} />
          {'streaming' in message && message.streaming && (
            <span className="inline-block w-1 h-4 bg-zinc-400 ml-1 animate-pulse align-middle" />
          )}
        </div>

        {!isUser && message.components && (
          <div className="max-w-[90%]">
            {message.components.map((c, i) => {
              switch (c.type) {
                case 'suggestion_chips':
                  return <SuggestionChipsBlock key={i} chips={c.chips} onSelect={onChipClick} />;
                case 'action_buttons':
                  return <ActionButtonsBlock key={i} buttons={c.buttons} />;
                case 'code_block':
                  return <CodeBlockWidget key={i} language={c.language} code={c.code} />;
                case 'retrieval_panel':
                  return <RetrievalPanelBlock key={i} chunks={c.chunks} />;
                case 'tool_call':
                  return <ToolCallBlock key={i} toolCall={c} />;
              }
            })}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Chat ──────────────────────────────────────────────────────────────

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  content: "Hello! I'm your RAG assistant. Ask me anything.",
  created_at: new Date().toISOString(),
};

export function ChatPage() {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const [providers, setProviders] = useState<LLMProviderConfig[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState('');

  const bottomRef = useRef<HTMLDivElement>(null);

  // load conversations
  const loadConversations = useCallback(async () => {
    try {
      const list = await api.chat.listConversations();
      setConversations(list);
    } catch (e) {
      console.error('Failed to load conversations', e);
    }
  }, []);

  // load providers
  useEffect(() => {
    api.providers.list(true).then((list) => {
      setProviders(list);
      const active = list.find((p) => p.is_active);
      if (active) setSelectedProviderId(active.id);
    });
    void loadConversations();
  }, [loadConversations]);

  // load messages for conversation
  const selectConversation = useCallback(async (id: string) => {
    setConversationId(id);
    setTyping(true);
    try {
      const msgs = await api.chat.getMessages(id);
      setMessages(msgs.length > 0 ? msgs : [WELCOME_MESSAGE]);
    } catch (e) {
      console.error('Failed to load messages', e);
      setMessages([WELCOME_MESSAGE]);
    } finally {
      setTyping(false);
    }
  }, []);

  const startNewChat = () => {
    setConversationId(undefined);
    setMessages([WELCOME_MESSAGE]);
    setInput('');
  };

  const deleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this conversation?')) return;
    try {
      await api.chat.deleteConversation(id);
      if (conversationId === id) {
        startNewChat();
      }
      void loadConversations();
    } catch (e) {
      console.error('Failed to delete conversation', e);
    }
  };

  // scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || typing) return;

      setInput('');
      const userMessageId = uid();
      const newUserMsg: Message = {
        id: userMessageId,
        role: 'user',
        content: trimmed,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, newUserMsg]);

      setTyping(true);

      const assistantMessageId = uid();
      setMessages((prev) => [
        ...prev,
        { id: assistantMessageId, role: 'assistant', content: '', streaming: true, created_at: new Date().toISOString() },
      ]);

      try {
        const response = await api.chat.send({
          message: trimmed,
          provider_id: selectedProviderId || undefined,
          conversation_id: conversationId,
        });

        if (!response.ok) throw new Error('Failed to send message');

        const reader = response.body?.getReader();
        if (!reader) throw new Error('No reader');

        const decoder = new TextDecoder();
        let fullContent = '';
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith('data: ')) {
              const data = trimmedLine.slice(6).trim();
              if (data === '[DONE]') break;
              if (!data) continue;

              try {
                const parsed = JSON.parse(data);
                if (parsed.conversation_id && !conversationId) {
                  setConversationId(parsed.conversation_id);
                  void loadConversations();
                }
                if (parsed.content) {
                  fullContent += parsed.content;
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessageId ? { ...m, content: fullContent } : m,
                    ),
                  );
                }
                if (parsed.tool_call) {
                  const tc: ToolCall = { type: 'tool_call', ...parsed.tool_call };
                  setMessages((prev) =>
                    prev.map((m) => {
                      if (m.id !== assistantMessageId) return m;
                      const existing = m.components ?? [];
                      const idx = existing.findIndex(
                        (c) => c.type === 'tool_call' && c.id === tc.id,
                      );
                      const updated =
                        idx >= 0
                          ? existing.map((c, i) => (i === idx ? tc : c))
                          : [...existing, tc];
                      return { ...m, components: updated };
                    }),
                  );
                }
                if (parsed.components) {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === assistantMessageId ? { ...m, components: parsed.components } : m,
                    ),
                  );
                }
              } catch (e) {
                console.error('Error parsing SSE data', e);
              }
            }
          }
        }

        setMessages((prev) =>
          prev.map((m) => (m.id === assistantMessageId ? { ...m, streaming: false } : m)),
        );
      } catch (e) {
        console.error(e);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMessageId
              ? { ...m, content: '❌ Error: cannot reach backend (FastAPI).', streaming: false }
              : m,
          ),
        );
      } finally {
        setTyping(false);
      }
    },
    [typing, selectedProviderId, conversationId, loadConversations],
  );

  return (
    <div className="flex h-full overflow-hidden">
      <ChatSidebar
        conversations={conversations}
        conversationId={conversationId}
        sidebarOpen={sidebarOpen}
        onNewChat={startNewChat}
        onSelectConversation={selectConversation}
        onDeleteConversation={deleteConversation}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 bg-zinc-950">
        <ChatHeader
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen((s) => !s)}
          conversationId={conversationId}
          conversations={conversations}
          providers={providers}
          selectedProviderId={selectedProviderId}
          onProviderChange={setSelectedProviderId}
        />

        {/* messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <div className="max-w-3xl mx-auto space-y-6 pb-4">
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} onChipClick={(t) => void sendMessage(t)} />
            ))}

            {typing && (
              <div className="flex items-center gap-2 text-zinc-500 text-xs px-10">
                <Loader2 className="h-3 w-3 animate-spin" />
                Thinking...
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        <ChatInput
          input={input}
          setInput={setInput}
          onSendMessage={sendMessage}
          typing={typing}
        />
      </div>
    </div>
  );
}
