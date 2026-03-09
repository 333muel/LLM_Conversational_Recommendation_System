"use client";

import React, { createContext, useContext, useState } from "react";

interface ChatContextType {
  isOpen: boolean;
  openChat: (initialMessage?: string, agentType?: "recbole" | "baseline") => void;
  closeChat: () => void;
  setIsOpen: (open: boolean) => void;
  initialMessage: string | null;
  setInitialMessage: (msg: string | null) => void;
  agentType: "recbole" | "baseline";
  setAgentType: (type: "recbole" | "baseline") => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [initialMessage, setInitialMessage] = useState<string | null>(null);
  const [agentType, setAgentType] = useState<"recbole" | "baseline">("recbole");

  const openChat = (message?: string, type?: "recbole" | "baseline") => {
    if (message) {
      setInitialMessage(message);
    }
    if (type) {
      setAgentType(type);
    }
    setIsOpen(true);
  };

  const closeChat = () => {
    setIsOpen(false);
    setInitialMessage(null);
  };

  return (
    <ChatContext.Provider
      value={{
        isOpen,
        openChat,
        closeChat,
        setIsOpen,
        initialMessage,
        setInitialMessage,
        agentType,
        setAgentType,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
