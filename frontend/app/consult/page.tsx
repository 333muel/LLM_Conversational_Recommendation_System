"use client";

import React, { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser } from "@/contexts/UserContext";
import { TopNav } from "@/components/TopNav";
import { ChatSidebar } from "@/components/ChatSidebar";
import { ProductCard } from "@/components/ProductCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchProducts, fetchRecommendations, fetchProduct } from "@/lib/api";
import { Product, Recommendation } from "@/lib/types";

const QUICK_CHIPS = [
  { text: "Cheaper options please", label: "Cheaper" },
  { text: "Fragrance-free only", label: "Fragrance-free" },
  { text: "Show me more hydrating options", label: "More hydrating" },
  { text: "Replace the not relevant item(s)", label: "Replace not relevant" },
];

const CONSTRAINT_CHIPS = [
  { text: "Under $20 please", label: "Under $20" },
  { text: "Fragrance-free only", label: "Fragrance-free" },
  { text: "Sensitive skin", label: "Sensitive skin" },
  { text: "Show cleansers", label: "Show cleansers" },
];

function ConsultContent() {
  const { isAuthenticated, userId } = useUser();
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "I need something for dry skin, fragrance-free under $20.";
  
  const [products, setProducts] = useState<Product[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  const loadRecommendations = async () => {
    try {
      setLoading(true);
      if (!userId) return;

      const response = await fetchRecommendations({
        message: query,
        conversation_id: conversationId,
        user_id: userId,
        top_k: 10,
      });

      setRecommendations(response.recommendations);
      if (response.conversation_id) {
        setConversationId(response.conversation_id);
      }
      
      // Fetch product details for recommendations
      if (response.recommendations.length > 0) {
        const productPromises = response.recommendations.map((rec) =>
          fetchProduct(rec.item_id).catch(() => null)
        );
        const productData = await Promise.all(productPromises);
        setProducts(productData.filter((p) => p !== null));
      }
    } catch (err) {
      setError("Failed to load recommendations. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    loadRecommendations();
  }, [isAuthenticated, router, query, userId]);

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="max-w-[1120px] mx-auto px-5 py-5.5 pb-[70px]">
        <div className="grid grid-cols-[1.55fr_1fr] gap-4.5 items-start max-[980px]:grid-cols-1">
          {/* Left: Recommendations with rationales */}
          <Card className="border border-[var(--line)] bg-white/95 rounded-[var(--radius2)] shadow-[var(--shadow)] p-4.5">
            <div className="flex items-start justify-between gap-3 mb-3.5">
              <div>
                <h1 className="text-lg m-0 tracking-wide font-extrabold">Consult mode — Recommendations</h1>
                <p className="text-[var(--muted-foreground)] text-[13px] leading-[1.5] mt-1.5 mb-0">
                  Results include short rationales. Refine by replying in the chat.
                </p>
              </div>
              <div className="flex items-center gap-2.5 flex-wrap justify-end">
                <Button
                  onClick={() => router.push("/onboarding")}
                  variant="outline"
                  className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted-foreground)] transition-colors flex items-center gap-2 select-none hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
                >
                  ✎ New query
                </Button>
                <Button
                  onClick={() => router.push("/products")}
                  variant="outline"
                  className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted-foreground)] transition-colors flex items-center gap-2 select-none hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
                >
                  ⟲ Reset
                </Button>
              </div>
            </div>

            <Card className="border border-[rgba(228,234,242,.95)] bg-[rgba(241,245,249,.65)] rounded-[var(--radius)] p-3 mb-3.5">
              <p className="text-xs text-[var(--muted-foreground)] m-0 mb-1.5">Your request</p>
              <p className="m-0 text-[13.5px] leading-[1.45] font-semibold text-[rgba(24,34,48,.92)]">
                {query}
              </p>
              <div className="flex flex-wrap gap-2 mt-2.5" aria-label="Quick constraint chips">
                {CONSTRAINT_CHIPS.map((chip, idx) => (
                  <button
                    key={idx}
                    onClick={() => router.push(`/consult?q=${encodeURIComponent(chip.text)}`)}
                    className="border border-[var(--line)] bg-white/90 rounded-full px-2.5 py-1.5 text-[12.5px] text-[var(--muted-foreground)] cursor-pointer transition-colors select-none hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(167,139,250,.28)]"
                  >
                    {chip.label}
                  </button>
                ))}
              </div>
            </Card>

            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-[var(--muted-foreground)]">Loading recommendations...</p>
              </div>
            )}

            {error && (
              <div className="bg-destructive/10 text-destructive p-4 rounded-lg mb-6">
                {error}
              </div>
            )}

            {!loading && !error && (
              <>
                {products.length === 0 ? (
                  <div className="text-[var(--muted-foreground)] text-[13.5px] leading-[1.5]">
                    No items to show. Try resetting or ask the assistant to relax constraints.
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-3.5 max-[980px]:grid-cols-2 max-[560px]:grid-cols-1" aria-label="Recommended products">
                    {products.map((product, idx) => {
                      const rec = recommendations.find((r) => r.item_id === product.asin);
                      return (
                        <div key={product.asin} className="border border-[var(--line)] bg-white/98 rounded-[var(--radius)] overflow-hidden shadow-[0_8px_18px_rgba(15,23,42,.05)] flex flex-col min-h-[320px]">
                          {product.product_image_url ? (
                            <div className="w-full aspect-[16/10] bg-gradient-to-br from-[rgba(45,212,191,.14)] to-[rgba(167,139,250,.12)] flex items-center justify-center border-b border-[rgba(228,234,242,.8)] relative">
                              <img
                                src={product.product_image_url}
                                alt={product.product_title || "Product"}
                                className="w-full h-full object-contain p-4"
                              />
                            </div>
                          ) : (
                            <div className="w-full aspect-[16/10] bg-gradient-to-br from-[rgba(45,212,191,.14)] to-[rgba(167,139,250,.12)] flex items-center justify-center border-b border-[rgba(228,234,242,.8)]">
                              <span className="text-[26px] text-[rgba(24,34,48,.55)] select-none">🧴</span>
                            </div>
                          )}
                          
                          <div className="p-3 flex flex-col gap-2 flex-1">
                            <h3 className="text-[13.5px] font-extrabold leading-[1.35] m-0 text-[var(--text)]">
                              {product.product_title || "Untitled Product"}
                            </h3>
                            
                            <div className="flex items-center justify-between gap-2.5 flex-wrap text-[var(--muted-foreground)] text-[12.5px]">
                              <span className="font-extrabold text-[rgba(24,34,48,.85)]">
                                {product.product_price ? `$${product.product_price}` : "—"}
                              </span>
                              {product.product_avg_rating && (
                                <div className="flex items-center gap-1.5">
                                  <span>⭐</span>
                                  <span>{product.product_avg_rating.toFixed(1)}</span>
                                </div>
                              )}
                            </div>

                            {rec && (
                              <div className="border-l-[3px] border-[rgba(45,212,191,.35)] bg-[rgba(241,245,249,.7)] rounded-xl p-2.5 text-[12.5px] leading-[1.4] text-[rgba(24,34,48,.82)]">
                                {rec.description || "Recommended based on your preferences."}
                              </div>
                            )}

                            <div className="flex gap-2 flex-wrap mt-1">
                              <Button
                                variant="outline"
                                className="border border-[var(--line)] bg-[rgba(241,245,249,.9)] px-2.5 py-1.5 rounded-full text-[12.5px] text-[var(--muted-foreground)] transition-colors hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
                              >
                                ⭐ Save
                              </Button>
                              <Button
                                className="bg-[rgba(45,212,191,.14)] border border-[rgba(45,212,191,.28)] px-2.5 py-1.5 rounded-full text-[12.5px] text-[rgba(15,23,42,.85)] transition-colors hover:bg-[rgba(45,212,191,.22)]"
                              >
                                🛒 Cart
                              </Button>
                              <Button
                                variant="outline"
                                className="border border-[var(--line)] bg-[rgba(241,245,249,.9)] px-2.5 py-1.5 rounded-full text-[12.5px] text-[var(--muted-foreground)] transition-colors hover:bg-[var(--btnHover)] hover:text-[rgba(185,28,28,.95)] hover:border-[rgba(239,68,68,.25)]"
                              >
                                ❌ Not relevant
                              </Button>
                              <Button
                                variant="outline"
                                className="border border-[var(--line)] bg-[rgba(241,245,249,.9)] px-2.5 py-1.5 rounded-full text-[12.5px] text-[var(--muted-foreground)] transition-colors hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
                              >
                                Why this?
                              </Button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </>
            )}
          </Card>

          {/* Right: Expanded chat */}
          <ChatSidebar
            initialMessage={`Thanks — here are a few options, each with a short rationale. You can refine by budget, ingredients, or product type.`}
            quickChips={QUICK_CHIPS}
            initialConversationId={conversationId}
          />
        </div>
      </main>
    </div>
  );
}

export default function ConsultPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ConsultContent />
    </Suspense>
  );
}
