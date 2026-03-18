"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
} from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { MessageCircle, Send, X, Star } from "lucide-react";
import { useUser } from "@/contexts/UserContext";
import { useChat } from "@/contexts/ChatContext";
import { fetchRecommendations, fetchBaselineRecommendations } from "@/lib/api";
import { ChatMessage, Recommendation } from "@/lib/types";
import Link from "next/link";

export function Chatbot() {
  const { 
    isOpen, 
    setIsOpen, 
    initialMessage, 
    setInitialMessage, 
    agentType, 
    setAgentType,
    llmProvider
  } = useChat();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const { userId } = useUser();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Handle initial message from context
  useEffect(() => {
    if (initialMessage && isOpen) {
      setInput(initialMessage);
      setInitialMessage(null);
      // We don't auto-send because the user might want to edit it
      // or we can auto-send if that's preferred.
      // Given the user query "linked to this chat dialogue", 
      // let's auto-send if it's coming from the search bar.
      handleSend(initialMessage);
    }
  }, [initialMessage, isOpen]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (overrideInput?: string) => {
    const messageText = overrideInput || input.trim();
    if (!messageText || !userId) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: messageText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!overrideInput) setInput("");
    setIsLoading(true);

    try {
      let response;
      if (agentType === "baseline") {
        const baselineResult = await fetchBaselineRecommendations({
          message: messageText,
          conversation_id: conversationId,
          user_id: userId,
          top_k: 5,
          llm_provider: llmProvider,
        });
        response = {
          response: baselineResult.response,
          recommendations: baselineResult.products,
          conversation_id: baselineResult.conversation_id
        };
      } else {
        response = await fetchRecommendations({
          message: messageText,
          conversation_id: conversationId,
          user_id: userId,
          top_k: 5,
          llm_provider: llmProvider,
        });
      }

      // Update conversation ID for subsequent messages
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
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
    <>
      {/* Assistant A Button (teal) */}
      <button
        onClick={() => {
          setAgentType("recbole");
          setIsOpen(true);
        }}
        className="fixed right-[18px] bottom-[18px] z-50 w-14 h-14 rounded-[18px] border border-[rgba(45,212,191,.45)] bg-[rgba(45,212,191,.22)] shadow-[var(--shadow2)] cursor-pointer flex items-center justify-center transition-all duration-150 hover:-translate-y-0.5 hover:bg-[rgba(45,212,191,.28)]"
        aria-label="Open Assistant B"
      >
        <span className="text-xl">💬</span>
      </button>

      {/* Assistant B Button (purple) */}
      <button
        onClick={() => {
          setAgentType("baseline");
          setIsOpen(true);
        }}
        className="fixed right-[82px] bottom-[18px] z-50 w-14 h-14 rounded-[18px] border border-[rgba(167,139,250,.45)] bg-[rgba(167,139,250,.22)] shadow-[var(--shadow2)] cursor-pointer flex items-center justify-center transition-all duration-150 hover:-translate-y-0.5 hover:bg-[rgba(167,139,250,.28)]"
        aria-label="Open Assistant A"
      >
        <span className="text-xl">💬</span>
      </button>

      <Drawer open={isOpen} onOpenChange={setIsOpen}>
        <DrawerContent className="h-[80vh] border border-[var(--line)] bg-white/98 rounded-t-[var(--radius2)]">
          <DrawerHeader className="border-b border-[var(--line)] p-3.5">
            <div className="flex items-center justify-between gap-2.5">
              <div>
                <DrawerTitle className="text-sm font-extrabold">
                  {agentType === "baseline" ? "Assistant A" : "Assistant B"}
                </DrawerTitle>
                <DrawerDescription className="text-[13px] text-[var(--muted-foreground)] leading-[1.45] mt-0.5">
                  Product recommendation assistant
                </DrawerDescription>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsOpen(false)}
                className="bg-[rgba(241,245,249,.9)] border border-[var(--line)] rounded-xl p-2 hover:bg-[var(--btnHover)] hover:border-[rgba(45,212,191,.30)]"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </DrawerHeader>

          <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2.5">
            {messages.length === 0 && (
              <div className="text-center text-[var(--muted-foreground)] py-8">
                <MessageCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p className="text-[13px]">Start a conversation to get product recommendations!</p>
              </div>
            )}

            {messages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[92%] p-2.5 rounded-[14px] text-[13px] leading-[1.35] border ${
                  message.role === "user"
                    ? "ml-auto bg-[rgba(45,212,191,.14)] border-[rgba(45,212,191,.28)]"
                    : "mr-auto bg-[rgba(241,245,249,.85)] border-[rgba(228,234,242,.9)]"
                }`}
              >
                <p className="whitespace-pre-wrap m-0">{message.content}</p>
                
                {message.recommendations && message.recommendations.length > 0 && (
                  <div className="mt-2 space-y-2">
                    {message.recommendations.map((rec) => (
                      <Link
                        key={rec.item_id}
                        href={`/products/${rec.item_id}`}
                        className="block"
                        onClick={() => setIsOpen(false)}
                      >
                        <Card className="p-2 hover:bg-accent transition-colors border border-[var(--line)]">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <h4 className="font-medium text-xs line-clamp-2">
                                {rec.title}
                              </h4>
                              <div className="flex items-center gap-2 mt-1">
                                <div className="flex items-center gap-1">
                                  <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                                  <span className="text-[11px]">{rec.rating.toFixed(1)}</span>
                                </div>
                                <span className="text-[11px] font-semibold text-primary">
                                  ${rec.price}
                                </span>
                              </div>
                            </div>
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

            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-[rgba(228,234,242,.9)] p-3 pb-3 bg-white/98">
            <div className="flex gap-2.5">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask about products…"
                disabled={isLoading}
                className="flex-1 border border-[rgba(228,234,242,.95)] outline-none text-[13.5px] px-3 py-2.5 rounded-[14px] bg-[rgba(241,245,249,.55)] text-[var(--text)] focus:bg-white/98 focus:border-[rgba(167,139,250,.35)] focus:shadow-[0_0_0_4px_rgba(167,139,250,.10)] placeholder:text-[rgba(91,103,119,.75)]"
              />
              <Button
                onClick={() => handleSend()}
                disabled={isLoading || !input.trim()}
                className="bg-[rgba(167,139,250,.14)] border border-[rgba(167,139,250,.35)] rounded-[14px] px-3 py-2.5 cursor-pointer font-extrabold text-[13px] transition-colors whitespace-nowrap select-none hover:bg-[rgba(167,139,250,.20)] disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DrawerContent>
      </Drawer>
    </>
  );
}
