"use client";

import { useState, useEffect, useRef } from "react";
import {
  Send,
  Loader2,
  Bot,
  User,
  Database,
  Globe,
  Calculator,
  FileText,
  Microscope,
  Lightbulb,
  Trash2,
  ExternalLink,
  BookOpen,
  Sparkles,
  Edit3,
  GraduationCap,
  PenTool,
  Save,
} from "lucide-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { useGlobal } from "@/context/GlobalContext";
import { apiUrl } from "@/lib/api";
import { processLatexContent } from "@/lib/latex";
import AddToNotebookModal from "@/components/AddToNotebookModal";
import { useTranslation } from "react-i18next";

interface KnowledgeBase {
  name: string;
  is_default?: boolean;
}

export default function HomePage() {
  const {
    chatState,
    setChatState,
    sendChatMessage,
    clearChatHistory,
    newChatSession,
  } = useGlobal();
  const { t } = useTranslation();

  const [inputMessage, setInputMessage] = useState("");
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [showNotebookModal, setShowNotebookModal] = useState(false);

  // Format chat history for notebook
  const formatChatForNotebook = () => {
    if (chatState.messages.length === 0)
      return { title: "", userQuery: "", output: "" };

    // Use the first user message as title
    const firstUserMsg = chatState.messages.find((m) => m.role === "user");
    const title =
      firstUserMsg?.content.slice(0, 50) +
      (firstUserMsg && firstUserMsg.content.length > 50 ? "..." : "") ||
      t("Chat Session");

    // Format all messages as markdown
    const formattedMessages = chatState.messages
      .map((msg, idx) => {
        const roleLabel =
          msg.role === "user"
            ? `👤 **${t("User")}**`
            : `🤖 **${t("Assistant")}**`;
        return `### ${roleLabel}\n\n${msg.content}`;
      })
      .join("\n\n---\n\n");

    // User query is the concatenation of all user messages
    const userQueries = chatState.messages
      .filter((m) => m.role === "user")
      .map((m) => m.content)
      .join("\n\n");

    return {
      title: `Chat: ${title}`,
      userQuery: userQueries,
      output: formattedMessages,
    };
  };

  // Fetch knowledge bases
  useEffect(() => {
    fetch(apiUrl("/api/v1/knowledge/list"))
      .then((res) => res.json())
      .then((data) => {
        // Ensure data is an array before processing
        const kbList = Array.isArray(data) ? data : [];
        setKbs(kbList);
        if (!chatState.selectedKb && kbList.length > 0) {
          const defaultKb = kbList.find((kb: KnowledgeBase) => kb.is_default);
          if (defaultKb) {
            setChatState((prev) => ({ ...prev, selectedKb: defaultKb.name }));
          } else {
            setChatState((prev) => ({ ...prev, selectedKb: kbList[0].name }));
          }
        }
      })
      .catch((err) => console.error("Failed to fetch KBs:", err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesContainerRef.current) {
      const container = messagesContainerRef.current;
      // Use scrollTop instead of scrollIntoView to prevent page-level scrolling
      container.scrollTo({
        top: container.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [chatState.messages]);

  const handleSend = () => {
    if (!inputMessage.trim() || chatState.isLoading) return;
    sendChatMessage(inputMessage);
    setInputMessage("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    {
      icon: Calculator,
      label: t("Smart Problem Solving"),
      href: "/solver",
      color: "blue",
      description: t("Multi-agent reasoning"),
    },
    {
      icon: PenTool,
      label: t("Generate Practice Questions"),
      href: "/question",
      color: "purple",
      description: t("Auto-validated quizzes"),
    },
    {
      icon: Microscope,
      label: t("Deep Research Reports"),
      href: "/research",
      color: "emerald",
      description: t("Comprehensive analysis"),
    },
    {
      icon: Lightbulb,
      label: t("Generate Novel Ideas"),
      href: "/ideagen",
      color: "amber",
      description: t("Brainstorm & synthesize"),
    },
    {
      icon: GraduationCap,
      label: t("Guided Learning"),
      href: "/guide",
      color: "indigo",
      description: t("Step-by-step tutoring"),
    },
    {
      icon: Edit3,
      label: t("Co-Writer"),
      href: "/co_writer",
      color: "pink",
      description: t("Collaborative writing"),
    },
  ];

  const hasMessages = chatState.messages.length > 0;

  return (
    <div className="h-screen flex flex-col animate-fade-in">
      {/* Empty State / Welcome Screen */}
      {!hasMessages && (
        <div className="flex-1 flex flex-col items-center justify-center px-6">
          <div className="text-center max-w-2xl mx-auto mb-8">
            <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100 mb-3 tracking-tight">
              {t("Welcome to DeepTutor")}
            </h1>
            <p className="text-lg text-slate-500 dark:text-slate-400">
              {t("How can I help you today?")}
            </p>
          </div>

          {/* Input Box - Centered */}
          <div className="w-full max-w-2xl mx-auto mb-12">
            {/* Mode Toggles */}
            <div className="flex items-center justify-between mb-3 px-1">
              <div className="flex items-center gap-2">
                {/* RAG Toggle */}
                <button
                  onClick={() =>
                    setChatState((prev) => ({
                      ...prev,
                      enableRag: !prev.enableRag,
                    }))
                  }
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${chatState.enableRag
                    ? "bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-700"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700"
                    }`}
                >
                  <Database className="w-3.5 h-3.5" />
                  {t("RAG")}
                </button>

                {/* Web Search Toggle */}
                <button
                  onClick={() =>
                    setChatState((prev) => ({
                      ...prev,
                      enableWebSearch: !prev.enableWebSearch,
                    }))
                  }
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-all ${chatState.enableWebSearch
                    ? "bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-700"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700"
                    }`}
                >
                  <Globe className="w-3.5 h-3.5" />
                  {t("Web Search")}
                </button>
              </div>

              {/* KB Selector */}
              {chatState.enableRag && (
                <select
                  value={chatState.selectedKb}
                  onChange={(e) =>
                    setChatState((prev) => ({
                      ...prev,
                      selectedKb: e.target.value,
                    }))
                  }
                  className="text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-1.5 outline-none focus:border-blue-400 dark:text-slate-200"
                >
                  {kbs.map((kb) => (
                    <option key={kb.name} value={kb.name}>
                      {kb.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Input Field */}
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                className="w-full px-5 py-4 pr-14 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all placeholder:text-slate-400 dark:placeholder:text-slate-500 text-slate-700 dark:text-slate-200 shadow-lg shadow-slate-200/50 dark:shadow-slate-900/50"
                placeholder={t("Ask anything...")}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={chatState.isLoading}
              />
              <button
                onClick={handleSend}
                disabled={chatState.isLoading || !inputMessage.trim()}
                className="absolute right-2 top-2 bottom-2 aspect-square bg-blue-600 text-white rounded-xl flex items-center justify-center hover:bg-blue-700 disabled:opacity-50 disabled:hover:bg-blue-600 transition-all shadow-md shadow-blue-500/20"
              >
                {chatState.isLoading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>

          {/* Quick Actions Grid */}
          <div className="w-full max-w-3xl mx-auto">
            <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-4 text-center">
              {t("Explore Modules")}
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {quickActions.map((action, i) => (
                <Link
                  key={i}
                  href={action.href}
                  className={`group p-4 rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:shadow-lg hover:border-${action.color}-300 dark:hover:border-${action.color}-600 transition-all`}
                >
                  <div
                    className={`w-10 h-10 rounded-xl bg-${action.color}-100 dark:bg-${action.color}-900/30 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform`}
                  >
                    <action.icon
                      className={`w-5 h-5 text-${action.color}-600 dark:text-${action.color}-400`}
                    />
                  </div>
                  <h4 className="font-semibold text-slate-900 dark:text-slate-100 text-sm mb-1">
                    {action.label}
                  </h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {action.description}
                  </p>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Chat Interface - When there are messages */}
      {hasMessages && (
        <>
          {/* Header Bar */}
          <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              {/* Mode Toggles */}
              <button
                onClick={() =>
                  setChatState((prev) => ({
                    ...prev,
                    enableRag: !prev.enableRag,
                  }))
                }
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${chatState.enableRag
                  ? "bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                  }`}
              >
                <Database className="w-3 h-3" />
                {t("RAG")}
              </button>

              <button
                onClick={() =>
                  setChatState((prev) => ({
                    ...prev,
                    enableWebSearch: !prev.enableWebSearch,
                  }))
                }
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${chatState.enableWebSearch
                  ? "bg-emerald-100 dark:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300"
                  : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                  }`}
              >
                <Globe className="w-3 h-3" />
                {t("Web Search")}
              </button>

              {chatState.enableRag && (
                <select
                  value={chatState.selectedKb}
                  onChange={(e) =>
                    setChatState((prev) => ({
                      ...prev,
                      selectedKb: e.target.value,
                    }))
                  }
                  className="text-xs bg-slate-100 dark:bg-slate-800 border-0 rounded-lg px-2 py-1 outline-none dark:text-slate-200"
                >
                  {kbs.map((kb) => (
                    <option key={kb.name} value={kb.name}>
                      {kb.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowNotebookModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 rounded-lg transition-colors"
                title={t("Save to Notebook")}
              >
                <Save className="w-3.5 h-3.5" />
                {t("Save to Notebook")}
              </button>
              <button
                onClick={newChatSession}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-slate-500 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
              >
                <Trash2 className="w-3.5 h-3.5" />
                {t("New Chat")}
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div
            ref={messagesContainerRef}
            className="flex-1 overflow-y-auto px-6 py-6 space-y-6"
          >
            {chatState.messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-4 w-full max-w-3xl mx-auto group animate-in fade-in slide-in-from-bottom-2 duration-300 ${msg.role === "user" ? "justify-end" : "justify-start"
                  }`}
              >
                {msg.role === "user" ? (
                  <div className="flex flex-col items-end max-w-[85%]">
                    <div className="bg-slate-200 dark:bg-slate-800 px-5 py-3 rounded-3xl rounded-tr-sm text-slate-800 dark:text-slate-200 shadow-sm border border-slate-300/50 dark:border-slate-700/50">
                      {msg.content}
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-4 w-full">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center shrink-0 shadow-lg shadow-blue-500/20 border border-white/10">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1 space-y-4 min-w-0">
                      <div className="prose prose-slate dark:prose-invert prose-sm md:prose-base max-w-none prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-800 prose-pre:rounded-xl prose-code:text-blue-600 dark:prose-code:text-blue-400">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                        >
                          {processLatexContent(msg.content)}
                        </ReactMarkdown>
                      </div>

                      {/* Loading indicator inside bubble for streaming */}
                      {msg.isStreaming && (
                        <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 text-sm font-medium animate-pulse">
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>{t("Generating...")}</span>
                        </div>
                      )}

                      {/* Sources */}
                      {msg.sources &&
                        (msg.sources.rag?.length ?? 0) +
                        (msg.sources.web?.length ?? 0) >
                        0 && (
                          <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                            {msg.sources.rag?.map((source, i) => (
                              <div
                                key={`rag-${i}`}
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50/50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full text-xs border border-blue-100 dark:border-blue-800/50"
                              >
                                <BookOpen className="w-3.5 h-3.5" />
                                <span>{source.kb_name}</span>
                              </div>
                            ))}
                            {msg.sources.web?.slice(0, 3).map((source, i) => (
                              <a
                                key={`web-${i}`}
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-50/50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-300 rounded-full text-xs hover:bg-emerald-100/50 dark:hover:bg-emerald-900/40 transition-colors border border-emerald-100 dark:border-emerald-800/50"
                              >
                                <Globe className="w-3.5 h-3.5" />
                                <span className="max-w-[150px] truncate">
                                  {source.title || source.url}
                                </span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            ))}
                          </div>
                        )}
                    </div>
                  </div>
                )}
              </div>
            ))}

            {/* Status indicator */}
            {chatState.isLoading && chatState.currentStage && (
              <div className="flex gap-4 w-full max-w-4xl mx-auto">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shrink-0">
                  <Loader2 className="w-4 h-4 text-white animate-spin" />
                </div>
                <div className="flex-1 bg-slate-100 dark:bg-slate-800 px-4 py-3 rounded-2xl rounded-tl-none">
                  <div className="flex items-center gap-2 text-slate-600 dark:text-slate-300 text-sm">
                    <span className="relative flex h-2 w-2">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                    </span>
                    {chatState.currentStage === "rag" &&
                      t("Searching knowledge base...")}
                    {chatState.currentStage === "web" &&
                      t("Searching the web...")}
                    {chatState.currentStage === "generating" &&
                      t("Generating response...")}
                    {!["rag", "web", "generating"].includes(
                      chatState.currentStage,
                    ) && chatState.currentStage}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input Area - Modern Floating Style */}
          <div className="bg-white dark:bg-slate-900 px-6 py-6 border-t border-slate-100 dark:border-slate-800/50">
            <div className="max-w-3xl mx-auto">
              <div className="relative group bg-slate-50 dark:bg-slate-800/50 rounded-3xl border border-slate-200 dark:border-slate-700/50 focus-within:border-blue-500/50 focus-within:ring-4 focus-within:ring-blue-500/5 transition-all duration-300 shadow-sm overflow-hidden">
                <textarea
                  ref={inputRef as any}
                  rows={1}
                  className="w-full px-5 py-4 bg-transparent outline-none resize-none placeholder:text-slate-400 dark:placeholder:text-slate-500 text-slate-700 dark:text-slate-200 min-h-[56px] max-h-[200px] leading-relaxed"
                  placeholder={t("Type your message...")}
                  value={inputMessage}
                  onChange={(e) => {
                    setInputMessage(e.target.value);
                    e.target.style.height = "auto";
                    e.target.style.height = `${e.target.scrollHeight}px`;
                  }}
                  onKeyDown={handleKeyDown}
                  disabled={chatState.isLoading}
                />

                <div className="flex items-center justify-between px-3 py-2 border-t border-slate-200/30 dark:border-slate-700/30 bg-slate-100/30 dark:bg-slate-800/20">
                  <div className="flex items-center gap-1">
                    <button className="p-2 rounded-xl text-slate-500 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-all">
                      <Sparkles className="w-4.5 h-4.5" />
                    </button>
                    <div className="w-px h-4 bg-slate-300 dark:bg-slate-700 mx-1" />
                    <button className="p-2 rounded-xl text-slate-500 hover:text-slate-700 dark:hover:text-slate-200 transition-all">
                      <FileText className="w-4.5 h-4.5" />
                    </button>
                  </div>

                  <button
                    onClick={handleSend}
                    disabled={chatState.isLoading || !inputMessage.trim()}
                    className={`flex items-center justify-center w-10 h-10 rounded-2xl transition-all duration-300 shadow-lg ${inputMessage.trim() && !chatState.isLoading
                        ? "bg-blue-600 text-white shadow-blue-500/25 hover:bg-blue-700 hover:scale-105 active:scale-95"
                        : "bg-slate-200 dark:bg-slate-800 text-slate-400 dark:text-slate-600 shadow-none pointer-events-none"
                      }`}
                  >
                    {chatState.isLoading ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Send className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>
              <p className="mt-3 text-center text-[11px] text-slate-400 dark:text-slate-500 font-medium">
                DeepTutor can make mistakes. Check important info.
              </p>
            </div>
          </div>
        </>
      )}

      {/* Add to Notebook Modal */}
      <AddToNotebookModal
        isOpen={showNotebookModal}
        onClose={() => setShowNotebookModal(false)}
        recordType="chat"
        title={formatChatForNotebook().title}
        userQuery={formatChatForNotebook().userQuery}
        output={formatChatForNotebook().output}
        metadata={{
          session_id: chatState.sessionId,
          message_count: chatState.messages.length,
          enable_rag: chatState.enableRag,
          enable_web_search: chatState.enableWebSearch,
        }}
        kbName={chatState.enableRag ? chatState.selectedKb : undefined}
      />
    </div>
  );
}
