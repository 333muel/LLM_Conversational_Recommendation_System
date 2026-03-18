"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useUser } from "@/contexts/UserContext";
import { useChat } from "@/contexts/ChatContext";
import { TopNav } from "@/components/TopNav";
import { ChatSidebar } from "@/components/ChatSidebar";
import { ProductCard } from "@/components/ProductCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchProducts, extractConstraints, filterProducts, respondToProducts } from "@/lib/api";
import { Product, Recommendation } from "@/lib/types";

const QUICK_CHIPS = [
  { text: "Cheaper options please", label: "Cheaper" },
  { text: "Show fragrance-free options", label: "Fragrance-free" },
  { text: "More hydrating options", label: "More hydrating" },
  { text: "Show cleansers", label: "Show cleansers" },
];

function BrowseContent() {
  const { isAuthenticated, userId } = useUser();
  const { llmProvider } = useChat();
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get("q");
  
  const [productState, setProductState] = useState<{ display: Product[]; buffer: Product[] }>({ display: [], buffer: [] });
  const [dislikedIds, setDislikedIds] = useState<Set<string>>(new Set());
  const products = productState.display;
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);
  const [assistantResponse, setAssistantResponse] = useState<string>("");
  const [constraints, setConstraints] = useState<Record<string, any>>({});

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    // Load initial recommendations or handle search from query param
    loadDiscovery(query || undefined);
  }, [isAuthenticated, router, query]);

  const loadDiscovery = async (query?: string) => {
    try {
      setLoading(true);
      if (!userId) return;

      const currentConvId = conversationId || (typeof crypto !== 'undefined' && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString());
      if (!conversationId) setConversationId(currentConvId);

      const userMessage = query || "Show me some recommendations";
      const isGeneric = !userMessage || ["show me some recommendations", "recommend some products", "browse"].includes(userMessage.toLowerCase().trim() || userMessage.toLowerCase());

      // Define a function to trigger filtering and response once we have constraints
      const runFilterAndRespond = (extractedConstraints: any) => {
        // Filter call - request 25 for buffer (20 displayed + 5 buffer)
        filterProducts({
          constraints: extractedConstraints,
          user_id: userId,
          limit: 25
        }).then(filterRes => {
          if (filterRes.success) {
            const allFormatted: Product[] = filterRes.products.map(toProduct);
            setProductState({ display: allFormatted.slice(0, 20), buffer: allFormatted.slice(20, 25) });
            setDislikedIds(new Set());
            
            // Generate response once products are ready (use first 20 for response text)
            respondToProducts({
              message: userMessage,
              conversation_id: currentConvId,
              user_id: userId,
              product_details: filterRes.products.slice(0, 20),
              llm_provider: llmProvider,
              metadata: filterRes.metadata
            }).then(respondRes => {
              if (respondRes.success) {
                setAssistantResponse(respondRes.response);
                if (respondRes.conversation_id) setConversationId(respondRes.conversation_id);
              }
            });
          }
        });
      };

      if (!isGeneric) {
        // Trigger extraction but don't AWAIT it here for the whole function
        extractConstraints({ message: userMessage, user_id: userId, llm_provider: llmProvider })
          .then(extractRes => {
            setConstraints(extractRes.constraints);
            runFilterAndRespond(extractRes.constraints);
          })
          .catch(err => {
            console.error("Extraction failed", err);
            runFilterAndRespond({}); // Fallback to generic if extraction fails
          });
      } else {
        setConstraints({});
        runFilterAndRespond({});
      }

    } catch (err) {
      setError("Failed to load discovery. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadDiscovery();
  };

  const toProduct = (p: { item_id: string; title?: string; description?: string; rating?: number; price?: string; categories?: string; main_category?: string; image?: string }): Product => ({
    asin: p.item_id,
    product_title: p.title,
    product_description: p.description,
    product_avg_rating: p.rating,
    product_price: p.price,
    product_categories: p.categories,
    product_main_category: p.main_category,
    product_image_url: p.image
  });

  const handleDislike = async (productId: string) => {
    if (!userId || !conversationId) return;
    const newDisliked = new Set([...dislikedIds, productId]);
    setDislikedIds(newDisliked);

    setProductState((prev) => {
      const dislikedIndex = prev.display.findIndex((p) => p.asin === productId);
      if (dislikedIndex === -1) return prev;

      if (prev.buffer.length > 0) {
        const [replacement, ...restBuffer] = prev.buffer;
        const newDisplay = [...prev.display];
        newDisplay[dislikedIndex] = replacement;
        return { display: newDisplay, buffer: restBuffer };
      }
      // Buffer empty - refill in background, then replace in place
      const idxToReplace = dislikedIndex;
      filterProducts({
        constraints,
        user_id: userId,
        exclude_item_ids: Array.from(newDisliked),
        limit: 5
      })
        .then((filterRes) => {
          if (filterRes.success && filterRes.products.length > 0) {
            const newProducts = filterRes.products.map(toProduct);
            const [first, ...rest] = newProducts;
            setProductState((p) => {
              const newDisplay = [...p.display];
              newDisplay.splice(idxToReplace, 0, first);
              return {
                display: newDisplay,
                buffer: rest.slice(0, 4)
              };
            });
          }
        })
        .catch(console.error);
      // Temporarily remove until replacement arrives
      const filtered = prev.display.filter((p) => p.asin !== productId);
      return { display: filtered, buffer: prev.buffer };
    });
  };

  const handleRecommendationsUpdate = (recs: Recommendation[]) => {
    const formattedProducts: Product[] = recs.map(p => ({
      asin: p.item_id,
      product_title: p.title,
      product_description: p.description || "",
      product_avg_rating: p.rating || 0,
      product_price: p.price || "",
      product_categories: p.categories || "",
      product_main_category: p.main_category || "",
      product_image_url: p.image || ""
    }));
    setProductState({ display: formattedProducts, buffer: [] });
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="max-w-[1120px] mx-auto px-5 py-5.5 pb-[70px]">
        <div className="grid grid-cols-[2fr_1fr] gap-4.5 items-start max-[980px]:grid-cols-1">
          {/* Left: Product feed */}
          <Card className="border border-[var(--line)] bg-white/95 rounded-[var(--radius2)] shadow-[var(--shadow)] p-4.5">
            <div className="flex items-start justify-between gap-3 mb-3.5">
              <div>
                <h1 className="text-lg m-0 tracking-wide font-extrabold">Browse mode — Your picks</h1>
                <p className="text-[var(--muted-foreground)] text-[13px] leading-[1.5] mt-1.5 mb-0">
                  Browse your recommended items. Use the assistant to refine or refresh suggestions.
                </p>
                {Object.keys(constraints).length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {constraints.category && (
                      <Badge variant="secondary" className="bg-[rgba(45,212,191,.1)] text-[rgba(45,212,191,1)] border-[rgba(45,212,191,.2)]">
                        Category: {constraints.category}
                      </Badge>
                    )}
                    {constraints.max_price && (
                      <Badge variant="secondary" className="bg-[rgba(167,139,250,.1)] text-[rgba(167,139,250,1)] border-[rgba(167,139,250,.2)]">
                        Max: ${constraints.max_price}
                      </Badge>
                    )}
                    {constraints.min_rating && (
                      <Badge variant="secondary" className="bg-yellow-50 text-yellow-600 border-yellow-100">
                        {constraints.min_rating}+ Stars
                      </Badge>
                    )}
                    {constraints.keywords && constraints.keywords.map((kw: string) => (
                      <Badge key={kw} variant="outline" className="text-[11px]">
                        {kw}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex items-center gap-2.5 flex-wrap justify-end">
                <Button
                  onClick={handleRefresh}
                  variant="outline"
                  className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted-foreground)] transition-colors flex items-center gap-2 select-none hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
                >
                  ↻ Refresh
                </Button>
                <Button
                  onClick={() => router.push("/products")}
                  variant="outline"
                  className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted-foreground)] transition-colors flex items-center gap-2 select-none hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
                >
                  ⟲ Reset filters
                </Button>
              </div>
            </div>

            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-[var(--muted-foreground)]">Loading products...</p>
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
                    No items match the current filters. Try resetting or ask the assistant to relax constraints.
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-3.5 max-[980px]:grid-cols-2 max-[560px]:grid-cols-1" aria-label="Recommended products">
                    {products.map((product) => (
                      <ProductCard 
                        key={product.asin} 
                        product={product} 
                        conversationId={conversationId}
                        onDislike={handleDislike}
                      />
                    ))}
                  </div>
                )}
              </>
            )}
          </Card>

          {/* Right: Compact chat widget */}
          <ChatSidebar
            initialMessage={assistantResponse || "Here are your recommendations. Tell me if you want cheaper options, fragrance-free items, or a different product type."}
            quickChips={QUICK_CHIPS}
            initialConversationId={conversationId}
            onRecommendationsUpdate={handleRecommendationsUpdate}
            hideProductCards
          />
        </div>
      </main>
    </div>
  );
}

export default function BrowsePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <BrowseContent />
    </Suspense>
  );
}
