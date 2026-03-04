"use client";

import React from "react";
import {
  Plus,
  MessageSquare,
  Settings,
  History,
  LayoutDashboard,
  PanelLeftClose,
  PanelLeftOpen,
  Search
} from "lucide-react";
import { useGlobal } from "@/context/GlobalContext";
import { useTranslation } from "react-i18next";

interface SidebarProps {
  isOpen: boolean;
  toggleSidebar: () => void;
}

export default function Sidebar({ isOpen, toggleSidebar }: SidebarProps) {
  const { chatState, newChatSession } = useGlobal();
  const { t } = useTranslation();

  return (
    <div
      className={`fixed inset-y-0 left-0 z-50 flex flex-col bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-all duration-300 ease-in-out ${isOpen ? "w-64" : "w-0 -translate-x-full md:w-16 md:translate-x-0"
        }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 min-h-[64px]">
        {isOpen ? (
          <h2 className="font-bold text-xl bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent truncate">
            DeepTutor
          </h2>
        ) : (
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
            <span className="text-white font-bold text-xs">DT</span>
          </div>
        )}
        <button
          onClick={toggleSidebar}
          className="p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-500 transition-colors"
        >
          {isOpen ? <PanelLeftClose className="w-5 h-5" /> : <PanelLeftOpen className="w-5 h-5" />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="px-3 mb-2">
        <button
          onClick={newChatSession}
          className={`w-full flex items-center gap-3 px-3 py-3 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-blue-300 dark:hover:border-blue-500/50 transition-all group overflow-hidden ${!isOpen && "justify-center px-0"
            }`}
        >
          <Plus className="w-5 h-5 text-blue-600 shrink-0 group-hover:rotate-90 transition-transform" />
          {isOpen && <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{t("New Chat")}</span>}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1 custom-scrollbar">
        {isOpen && (
          <div className="px-3 mb-2">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{t("Recent Chats")}</p>
          </div>
        )}

        {/* Placeholder for actual chat history items */}
        <div className="space-y-1">
          <button className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors ${!isOpen && "justify-center"}`}>
            <MessageSquare className="w-4 h-4 shrink-0" />
            {isOpen && <span className="text-sm truncate">How to solve calculus...</span>}
          </button>
          <button className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors ${!isOpen && "justify-center"}`}>
            <MessageSquare className="w-4 h-4 shrink-0" />
            {isOpen && <span className="text-sm truncate">Quantum Physics Introduction</span>}
          </button>
        </div>
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 space-y-1">
        <button className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors ${!isOpen && "justify-center"}`}>
          <LayoutDashboard className="w-5 h-5 shrink-0" />
          {isOpen && <span className="text-sm font-medium">{t("Dashboard")}</span>}
        </button>
        <button className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors ${!isOpen && "justify-center"}`}>
          <Settings className="w-5 h-5 shrink-0" />
          {isOpen && <span className="text-sm font-medium">{t("Settings")}</span>}
        </button>
      </div>
    </div>
  );
}
