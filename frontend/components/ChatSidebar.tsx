"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { useUser } from "@/contexts/UserContext";
import { useChat } from "@/contexts/ChatContext";
import { fetchRecommendations } from "@/lib/api";
import { ChatMessage, Recommendation } from "@/lib/types";
import Link from "next/link";

interface ChatSidebarProps {
  initialMessage?: string;
  quickChips?: Array<{ text: string; label: string }>;
  initialConversationId?: string;
  onRecommendationsUpdate?: (recommendations: Recommendation[]) => void;
  hideProductCards?: boolean;
  /** Number of recommendations to fetch (default 5). Use 20 for browse page to regenerate full list. */
  topK?: number;
}

export function ChatSidebar({ 
  initialMessage, 
  quickChips = [], 
  initialConversationId,
  onRecommendationsUpdate,
  hideProductCards = false,
  topK = 5
}: ChatSidebarProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(initialConversationId);
  const { userId } = useUser();
  const { llmProvider } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialConversationId) {
      setConversationId(initialConversationId);
    }
  }, [initialConversationId]);

  useEffect(() => {
    if (initialMessage) {
      setMessages([
        {
          id: "1",
          role: "assistant",
          content: initialMessage,
          timestamp: new Date(),
        },
      ]);
    }
  }, [initialMessage]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (text?: string) => {
    const messageText = text || input.trim();
    if (!messageText || !userId) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!text) setInput("");
    setIsLoading(true);

    try {
      const response = await fetchRecommendations({
        message: messageText,
        conversation_id: conversationId,
        user_id: userId,
        top_k: topK,
        llm_provider: llmProvider,
      });

      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }

      if (response.recommendations && onRecommendationsUpdate) {
        onRecommendationsUpdate(response.recommendations);
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        recommendations: response.recommendations,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!userId) {
    return null;
  }

  return (
    <div className="sticky top-[86px]">
      <div className="flex items-center justify-between gap-2.5 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-[34px] h-[34px] rounded-xl bg-[rgba(167,139,250,.14)] border border-[rgba(167,139,250,.28)] flex items-center justify-center flex-shrink-0">
            <span className="text-base">💬</span>
          </div>
          <div>
            <h2 className="text-sm font-extrabold m-0">Digital Sales Assistant</h2>
            <p className="text-[12.5px] text-[var(--muted-foreground)] mt-0.5 m-0">
              Ask to refine results (e.g., "cheaper", "fragrance-free", "show cleansers").
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            setMessages(initialMessage ? [{ id: "1", role: "assistant", content: initialMessage, timestamp: new Date() }] : []);
            setConversationId(undefined);
          }}
          className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted-foreground)] transition-colors hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
        >
          ⟲ Reset
        </Button>
      </div>

      <div className="border border-[rgba(228,234,242,.9)] bg-white/98 rounded-[var(--radius)] overflow-hidden flex flex-col h-[560px] max-[980px]:h-[420px]">
        <div className="p-3 overflow-auto flex-1 flex flex-col gap-2.5" ref={messagesEndRef}>
          {messages.length === 0 && (
            <div className="text-center text-[var(--muted-foreground)] py-8">
              <p className="text-[13px]">Start a conversation to get product recommendations!</p>
            </div>
          )}

          {messages.map((message) => (
            <div
              key={message.id}
              className={`max-w-[92%] p-3 rounded-[14px] text-[13px] leading-[1.5] border ${
                message.role === "user"
                  ? "ml-auto bg-[rgba(45,212,191,.14)] border-[rgba(45,212,191,.28)]"
                  : "mr-auto bg-[rgba(241,245,249,.85)] border-[rgba(228,234,242,.9)]"
              }`}
            >
              {message.role === "assistant" ? (
                <div className="chat-content [&_p]:mb-1.5 [&_p:last-child]:mb-0 [&_ul]:list-disc [&_ul]:list-inside [&_ul]:my-2 [&_ul]:space-y-0.5 [&_li]:text-[12.5px] [&_strong]:font-bold [&_strong]:text-[var(--text)]">
                  <ReactMarkdown
                    components={{
                      p: ({ children }) => <p className="mb-1.5 last:mb-0">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc list-inside space-y-0.5 my-2">{children}</ul>,
                      li: ({ children }) => <li className="text-[12.5px]">{children}</li>,
                      strong: ({ children }) => <strong className="font-bold text-[var(--text)]">{children}</strong>,
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <span>{message.content}</span>
              )}
              {!hideProductCards && message.recommendations && message.recommendations.length > 0 && (
                <div className="mt-2 space-y-2">
                  {message.recommendations.map((rec) => (
                    <Link key={rec.item_id} href={`/products/${rec.item_id}`} className="block">
                      <Card className="p-2 hover:bg-accent transition-colors">
                        <div className="text-xs font-medium line-clamp-2">{rec.title}</div>
                        <div className="flex items-center gap-2 mt-1 text-[11px]">
                          <span>⭐ {rec.rating.toFixed(1)}</span>
                          <span className="font-semibold text-primary">${rec.price}</span>
                        </div>
                      </Card>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="mr-auto">
              <div className="bg-[rgba(241,245,249,.85)] rounded-[14px] p-2.5 border border-[rgba(228,234,242,.9)]">
                <div className="flex gap-1">
                  <div className="h-1 w-1 bg-[var(--muted-foreground)] rounded-full animate-bounce" />
                  <div className="h-1 w-1 bg-[var(--muted-foreground)] rounded-full animate-bounce [animation-delay:0.2s]" />
                  <div className="h-1 w-1 bg-[var(--muted-foreground)] rounded-full animate-bounce [animation-delay:0.4s]" />
                </div>
              </div>
            </div>
          )}
        </div>

        {quickChips.length > 0 && (
          <div className="px-3 py-2.5 border-t border-[rgba(228,234,242,.9)] flex flex-wrap gap-2 bg-white/98">
            {quickChips.map((chip, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(chip.text)}
                className="border border-[var(--line)] bg-[rgba(241,245,249,.9)] rounded-full px-2.5 py-1.5 text-[12.5px] text-[var(--muted-foreground)] cursor-pointer transition-colors select-none hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.28)]"
              >
                {chip.label}
              </button>
            ))}
          </div>
        )}

        <div className="flex gap-2.5 px-3 py-2.5 pb-3 border-t border-[rgba(228,234,242,.9)] bg-white/98">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type a refinement request…"
            className="flex-1 border border-[rgba(228,234,242,.95)] outline-none text-[13.5px] px-3 py-2.5 rounded-[14px] bg-[rgba(241,245,249,.55)] text-[var(--text)] focus:bg-white/98 focus:border-[rgba(167,139,250,.35)] focus:shadow-[0_0_0_4px_rgba(167,139,250,.10)]"
            disabled={isLoading}
          />
          <Button
            onClick={() => handleSend()}
            disabled={isLoading || !input.trim()}
            className="bg-[rgba(167,139,250,.14)] border border-[rgba(167,139,250,.35)] rounded-[14px] px-3 py-2.5 cursor-pointer font-extrabold text-[13px] transition-colors whitespace-nowrap select-none hover:bg-[rgba(167,139,250,.20)]"
          >
            Send
          </Button>
        </div>
      </div>
    </div>
  );
}
