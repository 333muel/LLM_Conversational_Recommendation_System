"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@/contexts/UserContext";
import { TopNav } from "@/components/TopNav";
import { ChatSidebar } from "@/components/ChatSidebar";
import { ProductCard } from "@/components/ProductCard";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { fetchProducts } from "@/lib/api";
import { Product } from "@/lib/types";

const QUICK_CHIPS = [
  { text: "Cheaper options please", label: "Cheaper" },
  { text: "Show fragrance-free options", label: "Fragrance-free" },
  { text: "More hydrating options", label: "More hydrating" },
  { text: "Show cleansers", label: "Show cleansers" },
];

export default function BrowsePage() {
  const { isAuthenticated } = useUser();
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    loadProducts();
  }, [isAuthenticated, router]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await fetchProducts(20, 0);
      setProducts(data.products);
    } catch (err) {
      setError("Failed to load products. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadProducts();
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
                <p className="text-[var(--muted)] text-[13px] leading-[1.5] mt-1.5 mb-0">
                  Browse your recommended items. Use the assistant to refine or refresh suggestions.
                </p>
              </div>

              <div className="flex items-center gap-2.5 flex-wrap justify-end">
                <Button
                  onClick={handleRefresh}
                  variant="outline"
                  className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted)] transition-colors flex items-center gap-2 select-none hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
                >
                  ↻ Refresh
                </Button>
                <Button
                  onClick={() => router.push("/products")}
                  variant="outline"
                  className="border border-[var(--line)] bg-[rgba(241,245,249,.85)] rounded-full px-3 py-2 text-[12.5px] text-[var(--muted)] transition-colors flex items-center gap-2 select-none hover:bg-[var(--btnHover)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.30)]"
                >
                  ⟲ Reset filters
                </Button>
              </div>
            </div>

            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-[var(--muted)]">Loading products...</p>
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
                  <div className="text-[var(--muted)] text-[13.5px] leading-[1.5]">
                    No items match the current filters. Try resetting or ask the assistant to relax constraints.
                  </div>
                ) : (
                  <div className="grid grid-cols-3 gap-3.5 max-[980px]:grid-cols-2 max-[560px]:grid-cols-1" aria-label="Recommended products">
                    {products.map((product) => (
                      <ProductCard key={product.asin} product={product} />
                    ))}
                  </div>
                )}
              </>
            )}
          </Card>

          {/* Right: Compact chat widget */}
          <ChatSidebar
            initialMessage="Here are your recommendations. Tell me if you want cheaper options, fragrance-free items, or a different product type."
            quickChips={QUICK_CHIPS}
          />
        </div>
      </main>
    </div>
  );
}
