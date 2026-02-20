"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

interface UserContextType {
  userId: string | null;
  login: (userId: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserId] = useState<string | null>(null);

  useEffect(() => {
    // Load user ID from localStorage on mount
    const storedUserId = localStorage.getItem("userId");
    if (storedUserId) {
      setUserId(storedUserId);
    }
  }, []);

  const login = (userId: string) => {
    setUserId(userId);
    localStorage.setItem("userId", userId);
  };

  const logout = () => {
    setUserId(null);
    localStorage.removeItem("userId");
  };

  return (
    <UserContext.Provider
      value={{
        userId,
        login,
        logout,
        isAuthenticated: !!userId,
      }}
    >
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
}
