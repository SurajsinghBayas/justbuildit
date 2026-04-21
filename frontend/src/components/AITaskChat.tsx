// Phase 1 — Task AI Chat Drawer
// Floating chat interface powered by Bedrock: POST /tasks/{id}/ai-chat

import { useState, useRef, useEffect } from "react";
import apiClient from "@/api/client";
import {
  X,
  Send,
  Loader2,
  Sparkles,
  Bot,
  User,
  MessageSquare,
} from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
  ts: number;
}

interface Props {
  task: any;
  open: boolean;
  onClose: () => void;
}

export default function AITaskChat({ task, open, onClose }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when opened + add welcome message
  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100);
      if (messages.length === 0) {
        setMessages([
          {
            role: "assistant",
            content: `Hi! I'm your AI assistant for **"${task.title}"**. Ask me anything — implementation approach, breaking it into steps, potential risks, or time estimates.`,
            ts: Date.now(),
          },
        ]);
      }
    }
  }, [open]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");

    const userMsg: Message = { role: "user", content: text, ts: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setSending(true);

    try {
      const res = await apiClient.post(`/tasks/${task.id}/ai-chat`, {
        message: text,
        task_context: {
          title: task.title,
          description: task.description,
          complexity_label: task.complexity_label,
          risk_factors: task.risk_factors || [],
          subtasks: task.subtasks || [],
          story_points: task.story_points,
        },
      });
      const reply =
        res.data?.reply || res.data?.message || "No response from AI.";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: reply, ts: Date.now() },
      ]);
    } catch (err: any) {
      const errMsg =
        err?.response?.status === 501
          ? "This endpoint is coming soon. The task chat AI is being connected to Bedrock."
          : err?.response?.data?.detail ||
            "Connection failed. Is the backend running?";
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `⚠️ ${errMsg}`, ts: Date.now() },
      ]);
    } finally {
      setSending(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end p-4 pointer-events-none">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/20 backdrop-blur-sm pointer-events-auto"
        onClick={onClose}
      />

      {/* Chat panel */}
      <div
        className="relative pointer-events-auto w-full max-w-md bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden"
        style={{ height: "520px" }}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-violet-600 to-purple-600 text-white flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-sm truncate">Task AI Assistant</p>
            <p className="text-[10px] text-violet-200 truncate">{task.title}</p>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-full hover:bg-white/20 flex items-center justify-center transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Suggested prompts */}
        {messages.length <= 1 && (
          <div className="px-4 py-2 border-b border-gray-50 flex gap-2 overflow-x-auto flex-shrink-0">
            {[
              "How should I approach this?",
              "What are the risks?",
              "Break it into sub-tasks",
              "Time estimate?",
            ].map((q) => (
              <button
                key={q}
                onClick={() => {
                  setInput(q);
                  inputRef.current?.focus();
                }}
                className="flex-shrink-0 text-[10px] font-medium px-2.5 py-1 rounded-full border border-violet-200 text-violet-600 bg-violet-50 hover:bg-violet-100 transition-colors whitespace-nowrap"
              >
                {q}
              </button>
            ))}
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
          {messages.map((m) => (
            <div
              key={m.ts}
              className={`flex gap-2 ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
                  m.role === "user"
                    ? "bg-gray-900"
                    : "bg-gradient-to-br from-violet-500 to-purple-600"
                }`}
              >
                {m.role === "user" ? (
                  <User className="w-3 h-3 text-white" />
                ) : (
                  <Sparkles className="w-3 h-3 text-white" />
                )}
              </div>
              <div
                className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
                  m.role === "user"
                    ? "bg-gray-900 text-white rounded-tr-sm"
                    : "bg-gray-50 text-gray-800 border border-gray-100 rounded-tl-sm"
                }`}
              >
                {m.content}
              </div>
            </div>
          ))}
          {sending && (
            <div className="flex gap-2">
              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <Loader2 className="w-3 h-3 text-white animate-spin" />
              </div>
              <div className="bg-gray-50 border border-gray-100 rounded-2xl rounded-tl-sm px-3 py-2">
                <div className="flex gap-1">
                  <span
                    className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <span
                    className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <span
                    className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 pb-4 pt-2 border-t border-gray-50 flex-shrink-0">
          <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 focus-within:border-violet-400 focus-within:ring-2 focus-within:ring-violet-100 transition-all">
            <MessageSquare className="w-4 h-4 text-gray-300 flex-shrink-0" />
            <input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) =>
                e.key === "Enter" && !e.shiftKey && sendMessage()
              }
              placeholder="Ask anything about this task…"
              className="flex-1 bg-transparent text-sm outline-none text-gray-800 placeholder:text-gray-400"
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || sending}
              className="w-7 h-7 rounded-lg bg-violet-600 hover:bg-violet-700 disabled:bg-gray-200 flex items-center justify-center transition-colors flex-shrink-0"
            >
              <Send className="w-3 h-3 text-white" />
            </button>
          </div>
          <p className="text-[10px] text-gray-300 mt-1.5 text-center">
            Powered by AWS Bedrock
          </p>
        </div>
      </div>
    </div>
  );
}
