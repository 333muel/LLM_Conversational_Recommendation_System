"use client";

import Link from "next/link";
import Image from "next/image";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Product, ExplainResponse } from "@/lib/types";
import { Star, ThumbsUp, ThumbsDown, Info, X } from "lucide-react";
import { useState } from "react";
import { submitFeedback, explainRecommendation } from "@/lib/api";
import { useUser } from "@/contexts/UserContext";

interface ProductCardProps {
  product: Product;
  conversationId?: string;
}

export function ProductCard({ product, conversationId }: ProductCardProps) {
  const { userId } = useUser();
  const [feedback, setFeedback] = useState<"like" | "dislike" | null>(null);
  const [explanation, setExplanation] = useState<ExplainResponse | null>(null);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [showExplain, setShowExplain] = useState(false);

  const handleFeedback = async (e: React.MouseEvent, type: "like" | "dislike") => {
    e.preventDefault();
    e.stopPropagation();
    if (!userId || !conversationId) return;
    
    try {
      await submitFeedback(product.asin, conversationId, userId, type);
      setFeedback(type);
    } catch (err) {
      console.error("Failed to submit feedback", err);
    }
  };

  const handleExplain = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!userId || !conversationId) return;

    setLoadingExplain(true);
    setShowExplain(true);
    try {
      const res = await explainRecommendation(product.asin, conversationId, userId);
      setExplanation(res);
    } catch (err) {
      console.error("Failed to get explanation", err);
    } finally {
      setLoadingExplain(false);
    }
  };

  const imageUrl = product.product_image_url;
  const title = product.product_title || "Untitled Product";
  const store = product.product_store || "Unknown Store";
  const price = product.product_price || "N/A";
  const rating = product.product_avg_rating;
  const reviewCount = product.product_review_count;
  const category = product.product_main_category || "Uncategorized";
  
  return (
    <div className="relative group">
      <Card className="border border-[var(--line)] bg-white/95 rounded-[var(--radius)] overflow-hidden shadow-none transition-all duration-[180ms] flex flex-col min-h-[280px] hover:shadow-[var(--shadow)] hover:border-[rgba(45,212,191,.28)]">
        <Link href={`/products/${product.asin}`} className="flex-1 flex flex-col">
          {imageUrl ? (
            <div className="relative w-full h-32 bg-[rgba(241,245,249,.95)]">
              <div className="absolute inset-0 bg-gradient-radial from-[rgba(45,212,191,.16)] via-transparent to-transparent opacity-90" style={{ background: "radial-gradient(220px 120px at 30% 30%, rgba(45,212,191,.16), transparent 65%)" }} />
              <Image
                src={imageUrl}
                alt={title}
                fill
                className="object-contain p-2"
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 25vw"
              />
            </div>
          ) : (
            <div className="relative w-full h-32 bg-[rgba(241,245,249,.95)] flex items-center justify-center">
              <div className="absolute inset-0 bg-gradient-radial from-[rgba(45,212,191,.16)] via-transparent to-transparent opacity-90" style={{ background: "radial-gradient(220px 120px at 30% 30%, rgba(45,212,191,.16), transparent 65%)" }} />
              <span className="text-muted-foreground text-sm">No Image</span>
            </div>
          )}
          
          <div className="p-3 flex flex-col gap-2 flex-1">
            <h3 className="font-bold text-[13px] leading-tight text-[var(--text)] line-clamp-2 min-h-[32px]">
              {title}
            </h3>
            
            <div className="flex gap-2.5 flex-wrap items-center text-[#1f2937] text-xs">
              <span className="font-extrabold tracking-wide text-[rgba(24,34,48,.92)]">
                {price !== "N/A" ? `$${price}` : "Price unavailable"}
              </span>
              {rating != null && rating > 0 && (
                <Badge className="border border-[var(--line)] bg-[rgba(241,245,249,.9)] px-2 py-0.5 rounded-full text-[11px] text-[rgba(24,34,48,.82)]">
                  ⭐ {rating.toFixed(1)}
                </Badge>
              )}
            </div>
          </div>
        </Link>

        {/* Action Buttons */}
        <div className="px-3 pb-3 pt-1 flex items-center justify-between border-t border-[var(--line)]/50 bg-slate-50/30">
          <div className="flex items-center gap-1.5">
            <button
              onClick={(e) => handleFeedback(e, "like")}
              className={`p-1.5 rounded-lg border transition-all ${
                feedback === "like" 
                  ? "bg-green-100 border-green-300 text-green-700" 
                  : "bg-white border-[var(--line)] text-slate-400 hover:text-green-600 hover:border-green-200"
              }`}
              title="More like this"
            >
              <ThumbsUp className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={(e) => handleFeedback(e, "dislike")}
              className={`p-1.5 rounded-lg border transition-all ${
                feedback === "dislike" 
                  ? "bg-red-100 border-red-300 text-red-700" 
                  : "bg-white border-[var(--line)] text-slate-400 hover:text-red-600 hover:border-red-200"
              }`}
              title="Less like this"
            >
              <ThumbsDown className="w-3.5 h-3.5" />
            </button>
          </div>
          
          <button
            onClick={handleExplain}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--line)] bg-white text-[11px] font-bold text-slate-600 transition-all hover:bg-slate-50 hover:border-[rgba(167,139,250,.35)] hover:text-[rgba(167,139,250,1)]"
          >
            <Info className="w-3.5 h-3.5" />
            Tell me more
          </button>
        </div>
      </Card>

      {/* Explanation Modal Overlay */}
      {showExplain && (
        <div className="absolute inset-0 z-20 bg-white/98 flex flex-col p-4 rounded-[var(--radius)] shadow-xl animate-in fade-in zoom-in duration-200 border border-[var(--line)]">
          <div className="flex justify-between items-start mb-3">
            <h4 className="font-extrabold text-[13px] text-[var(--text)]">Why this product?</h4>
            <button onClick={() => setShowExplain(false)} className="text-slate-400 hover:text-slate-600">
              <X className="w-4 h-4" />
            </button>
          </div>
          
          {loadingExplain ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[rgba(167,139,250,1)]"></div>
              <p className="text-[11px] text-slate-400">Analyzing fit...</p>
            </div>
          ) : explanation ? (
            <div className="flex-1 flex flex-col gap-3 overflow-y-auto pr-1">
              <p className="text-[12px] leading-relaxed text-slate-600">
                {explanation.explanation}
              </p>
              
              {explanation.attribute_scores && (
                <div className="space-y-2.5 mt-2 pt-2 border-t border-[var(--line)]/50">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Match Scores</p>
                  {Object.entries(explanation.attribute_scores).map(([key, score]) => (
                    <div key={key} className="space-y-1">
                      <div className="flex justify-between text-[10px]">
                        <span className="capitalize">{key.replace("_", " ")}</span>
                        <span className="font-bold">{Math.round(score * 100)}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all duration-700 ${
                            key === 'preference_alignment' ? 'bg-[rgba(167,139,250,1)]' : 'bg-[rgba(45,212,191,1)]'
                          }`}
                          style={{ width: `${score * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <p className="text-[11px] text-red-500">Failed to load explanation.</p>
          )}
        </div>
      )}
    </div>
  );
}
