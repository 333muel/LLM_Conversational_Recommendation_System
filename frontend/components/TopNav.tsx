"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useUser } from "@/contexts/UserContext";
import { Button } from "@/components/ui/button";

interface TopNavProps {
  showAskRow?: boolean;
  onAskSubmit?: (query: string) => void;
}

export function TopNav({ showAskRow = false, onAskSubmit }: TopNavProps) {
  const { userId, logout, isAuthenticated } = useUser();
  const router = useRouter();
  const [askInput, setAskInput] = useState("");

  const handleAskSubmit = () => {
    if (askInput.trim() && onAskSubmit) {
      onAskSubmit(askInput.trim());
      setAskInput("");
    } else if (askInput.trim()) {
      router.push(`/consult?q=${encodeURIComponent(askInput.trim())}`);
    }
  };

  return (
    <div className="sticky top-0 z-30 bg-white/86 backdrop-blur-md border-b border-[var(--line)]">
      <div className="max-w-[1120px] mx-auto px-5">
        <div className="flex items-center justify-between gap-3.5 h-16">
          <Link href="/products" className="flex items-center gap-2.5 font-semibold tracking-wide">
            <div className="w-[34px] h-[34px] rounded-xl bg-[rgba(45,212,191,.18)] border border-[rgba(45,212,191,.35)] flex items-center justify-center">
              <span className="text-base text-[rgba(24,34,48,.75)]">✿</span>
            </div>
            <div>BeautyShop</div>
          </Link>

          <div className="flex items-center gap-2.5 flex-wrap justify-end">
            {isAuthenticated ? (
              <>
                <Link href="/saved" className="border border-[var(--line)] bg-white/90 px-3 py-2 rounded-full text-[13px] text-[#1f2937] transition-colors hover:bg-[var(--panel2)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.35)]">
                  <strong className="text-[var(--text)] font-semibold">★</strong> Saved
                </Link>
                <Link href="/cart" className="border border-[var(--line)] bg-white/90 px-3 py-2 rounded-full text-[13px] text-[#1f2937] transition-colors hover:bg-[var(--panel2)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.35)]">
                  <strong className="text-[var(--text)] font-semibold">🛒</strong> Cart
                </Link>
                <Link href="/profile" className="border border-[var(--line)] bg-white/90 px-3 py-2 rounded-full text-[13px] text-[#1f2937] transition-colors hover:bg-[var(--panel2)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.35)]">
                  <strong className="text-[var(--text)] font-semibold">👤</strong> Profile
                </Link>
                <Link href="/help" className="border border-[var(--line)] bg-white/90 px-3 py-2 rounded-full text-[13px] text-[#1f2937] transition-colors hover:bg-[var(--panel2)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.35)]">
                  <strong className="text-[var(--text)] font-semibold">?</strong> Help
                </Link>
                <Button
                  variant="outline"
                  onClick={() => {
                    logout();
                    router.push("/login");
                  }}
                  className="border border-[var(--line)] bg-white/90 px-3 py-2 rounded-full text-[13px] text-[#1f2937] transition-colors hover:bg-[var(--panel2)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.35)]"
                >
                  Logout
                </Button>
              </>
            ) : (
              <Link href="/login" className="border border-[var(--line)] bg-white/90 px-3 py-2 rounded-full text-[13px] text-[#1f2937] transition-colors hover:bg-[var(--panel2)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.35)]">
                Login
              </Link>
            )}
          </div>
        </div>

        {showAskRow && (
          <div className="pt-3.5 pb-4.5 border-t border-[rgba(228,234,242,.6)]">
            <div className="flex gap-2.5 items-center bg-white/95 border border-[var(--line)] rounded-[var(--radius)] p-2.5 shadow-[0_6px_18px_rgba(15,23,42,.05)]">
              <input
                type="text"
                value={askInput}
                onChange={(e) => setAskInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAskSubmit()}
                placeholder="Ask the assistant… e.g., 'dry skin, fragrance-free under $20'"
                className="flex-1 bg-transparent border-none outline-none text-[var(--text)] text-sm px-2.5 py-2 placeholder:text-[rgba(91,103,119,.75)]"
              />
              <Button
                onClick={handleAskSubmit}
                className="bg-[rgba(45,212,191,.16)] border border-[rgba(45,212,191,.35)] px-3 py-2.5 rounded-[14px] cursor-pointer font-semibold text-[13px] transition-colors hover:bg-[rgba(45,212,191,.22)] whitespace-nowrap"
              >
                ✨ Ask assistant
              </Button>
              <Button
                onClick={() => router.push("/browse")}
                variant="outline"
                className="bg-[var(--btn)] border border-[var(--line)] px-3 py-2.5 rounded-[14px] cursor-pointer font-semibold text-[13px] transition-colors hover:bg-[var(--btnHover)] hover:border-[rgba(45,212,191,.35)] whitespace-nowrap"
              >
                🧭 Browse with assistant
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
