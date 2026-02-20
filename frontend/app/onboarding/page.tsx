"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@/contexts/UserContext";
import { TopNav } from "@/components/TopNav";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";

const SUGGESTED_PROMPTS = [
  {
    prompt: "My skin feels dry. Recommend something fragrance-free under $20.",
    title: "Dry skin",
    description: '"My skin feels dry. Recommend something fragrance-free under $20."',
  },
  {
    prompt: "Recommend a gentle cleanser for sensitive skin.",
    title: "Sensitive skin",
    description: '"Recommend a gentle cleanser for sensitive skin."',
  },
  {
    prompt: "I'm breaking out. Suggest products for acne-prone skin.",
    title: "Acne / breakouts",
    description: '"I\'m breaking out. Suggest products for acne-prone skin."',
  },
  {
    prompt: "Recommend a face sunscreen. I prefer minimal white cast.",
    title: "Sunscreen",
    description: '"Recommend a face sunscreen. I prefer minimal white cast."',
  },
];

export default function OnboardingPage() {
  const { isAuthenticated } = useUser();
  const router = useRouter();
  const [quickInput, setQuickInput] = useState("");

  if (!isAuthenticated) {
    router.push("/login");
    return null;
  }

  const goBrowse = () => {
    router.push("/browse");
  };

  const goConsult = (query?: string) => {
    if (query) {
      router.push(`/consult?q=${encodeURIComponent(query)}`);
    } else {
      router.push("/consult");
    }
  };

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="max-w-[1120px] mx-auto px-5 py-7 pb-[90px]">
        <div className="grid grid-cols-[1.05fr_0.95fr] gap-4.5 items-start max-[980px]:grid-cols-1">
          {/* Left: Welcome + mode selection */}
          <Card className="border border-[var(--line)] bg-white/95 rounded-[var(--radius2)] shadow-[var(--shadow)] p-4.5">
            <div className="flex items-start justify-between gap-3 mb-2">
              <div>
                <h1 className="text-xl m-0 tracking-wide font-extrabold">
                  Welcome to the Digital Sales Assistant
                </h1>
                <p className="text-[var(--muted)] text-sm leading-[1.5] mt-1.5 mb-0">
                  You can start by browsing, or ask a needs-based question (e.g., "dry skin, fragrance-free under $20").
                </p>
              </div>
            </div>

            <div className="flex gap-3 items-start p-3 rounded-[var(--radius)] bg-[rgba(241,245,249,.85)] border border-[var(--line)] mt-3">
              <div className="w-10 h-10 rounded-[14px] bg-[rgba(45,212,191,.20)] border border-[rgba(45,212,191,.35)] flex items-center justify-center text-lg flex-shrink-0">
                💬
              </div>
              <p className="m-0 text-[var(--muted)] text-[13px] leading-[1.45]">
                I can recommend products and help you refine results. You can also mark items as not relevant, save them,
                or ask "why this item?" to see a short explanation.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-[14px] mt-3.5 max-[680px]:grid-cols-1">
              <Card className="border border-[var(--line)] bg-white/98 rounded-[var(--radius)] p-3.5 shadow-[0_8px_18px_rgba(15,23,42,.05)]">
                <h2 className="text-sm font-extrabold m-0 mb-1.5">Browse freely</h2>
                <p className="m-0 mb-3 text-[12.5px] leading-[1.45] text-[var(--muted)]">
                  See product recommendations first with minimal explanation. You can still chat anytime to refine.
                </p>
                <Button
                  onClick={goBrowse}
                  className="w-full bg-[var(--btn)] border border-[var(--line)] px-3 py-2.5 rounded-[14px] cursor-pointer font-semibold text-[13px] transition-colors flex items-center justify-center gap-2 select-none hover:bg-[var(--btnHover)] hover:border-[rgba(45,212,191,.35)]"
                >
                  🧭 Enter browse mode
                </Button>
              </Card>

              <Card className="border border-[var(--line)] bg-white/98 rounded-[var(--radius)] p-3.5 shadow-[0_8px_18px_rgba(15,23,42,.05)]">
                <h2 className="text-sm font-extrabold m-0 mb-1.5">Help me find something</h2>
                <p className="m-0 mb-3 text-[12.5px] leading-[1.45] text-[var(--muted)]">
                  Ask a question and get recommendations with short rationales. You can refine results in multiple turns.
                </p>
                <Button
                  onClick={() => goConsult(quickInput.trim() || undefined)}
                  className="w-full bg-[rgba(45,212,191,.16)] border border-[rgba(45,212,191,.35)] px-3 py-2.5 rounded-[14px] cursor-pointer font-semibold text-[13px] transition-colors flex items-center justify-center gap-2 select-none hover:bg-[rgba(45,212,191,.22)]"
                >
                  ✨ Enter consult mode
                </Button>
              </Card>
            </div>

            <div className="flex items-center justify-between gap-2.5 mt-3.5 pt-3.5 border-t border-[rgba(228,234,242,.8)]">
              <Button
                onClick={() => router.push("/products")}
                variant="outline"
                className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted)] transition-colors flex items-center gap-2 hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
              >
                ← Back to store
              </Button>
              <Button
                onClick={() => {
                  setQuickInput("");
                  router.push("/products");
                }}
                variant="outline"
                className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted)] transition-colors flex items-center gap-2 hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
              >
                ⟲ Reset / start over
              </Button>
            </div>
          </Card>

          {/* Right: Suggested prompts */}
          <Card className="border border-[var(--line)] bg-white/95 rounded-[var(--radius2)] shadow-[var(--shadow)] p-4.5">
            <div className="flex items-baseline justify-between gap-3 mb-2.5">
              <h3 className="text-sm font-extrabold m-0">Suggested starters</h3>
              <span className="text-[var(--muted)] text-xs">Click to auto-fill</span>
            </div>

            <div className="flex flex-col gap-2.5 mt-2.5">
              {SUGGESTED_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuickInput(item.prompt);
                    goConsult(item.prompt);
                  }}
                  className="border border-[var(--line)] bg-white/98 rounded-[var(--radius)] p-3 cursor-pointer transition-colors text-left hover:bg-[var(--panel2)] hover:border-[rgba(167,139,250,.35)]"
                >
                  <strong className="block text-[13px] mb-1">{item.title}</strong>
                  <p className="m-0 text-[var(--muted)] text-[12.5px] leading-[1.4]">{item.description}</p>
                </button>
              ))}
            </div>

            <div className="flex gap-2.5 mt-3 border border-[var(--line)] bg-white/98 rounded-[var(--radius)] p-2.5">
              <Input
                value={quickInput}
                onChange={(e) => setQuickInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && goConsult(quickInput.trim() || undefined)}
                placeholder="Type your question here…"
                className="flex-1 border-none outline-none text-[13.5px] px-2.5 py-2 bg-transparent text-[var(--text)] placeholder:text-[rgba(91,103,119,.75)]"
              />
              <Button
                onClick={() => goConsult(quickInput.trim() || undefined)}
                className="bg-[rgba(167,139,250,.14)] border border-[rgba(167,139,250,.35)] rounded-[14px] px-3 py-2.5 cursor-pointer font-semibold text-[13px] transition-colors whitespace-nowrap hover:bg-[rgba(167,139,250,.20)]"
              >
                Ask
              </Button>
            </div>
          </Card>
        </div>
      </main>
    </div>
  );
}
