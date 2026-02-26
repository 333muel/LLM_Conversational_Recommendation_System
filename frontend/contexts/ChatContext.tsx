"use client";

import React, { createContext, useContext, useState } from "react";

interface ChatContextType {
  isOpen: boolean;
  openChat: (initialMessage?: string) => void;
  closeChat: () => void;
  setIsOpen: (open: boolean) => void;
  initialMessage: string | null;
  setInitialMessage: (msg: string | null) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [initialMessage, setInitialMessage] = useState<string | null>(null);

  const openChat = (message?: string) => {
    if (message) {
      setInitialMessage(message);
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
