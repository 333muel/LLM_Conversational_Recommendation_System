"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@/contexts/UserContext";
import { ProductCard } from "@/components/ProductCard";
import { TopNav } from "@/components/TopNav";
import { Chatbot } from "@/components/Chatbot";
import { Button } from "@/components/ui/button";
import { fetchProducts, fetchAvailableCategories } from "@/lib/api";
import { Product } from "@/lib/types";

export default function ProductsPage() {
  const { isAuthenticated } = useUser();
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showAllCategories, setShowAllCategories] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    loadCategories();
    loadProducts();
  }, [isAuthenticated, router, selectedCategory]);

  const loadCategories = async () => {
    try {
      const data = await fetchAvailableCategories();
      setCategories(data.categories);
    } catch (err) {
      console.error("Failed to load categories:", err);
    }
  };

  const loadProducts = async () => {
    try {
      setLoading(true);
      const data = await fetchProducts(20, 0, selectedCategory || undefined);
      setProducts(data.products);
    } catch (err) {
      setError("Failed to load products. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAskSubmit = (query: string) => {
    router.push(`/consult?q=${encodeURIComponent(query)}`);
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen">
      <TopNav showAskRow onAskSubmit={handleAskSubmit} />

      <main className="max-w-[1120px] mx-auto px-5 py-4.5 pb-[110px]">
        <div className="flex gap-4.5 items-start justify-between pt-4.5 pb-2.5">
          <div>
            <h1 className="text-[22px] font-extrabold tracking-wide mb-1.5">
              Discover skincare, haircare, and cosmetics
            </h1>
            <p className="text-[var(--muted-foreground)] text-sm leading-[1.45] m-0">
              Browse products freely, or use the Digital Sales Assistant for needs-based discovery and refinement.
            </p>
          </div>
        </div>

        {/* Category chips */}
        <div className="flex gap-2.5 flex-wrap pt-3 pb-1.5" role="list" aria-label="Category filters">
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-2 rounded-full border text-[13px] cursor-pointer transition-colors select-none ${
              selectedCategory === null
                ? "border-[rgba(45,212,191,.45)] bg-[rgba(45,212,191,.14)] text-[var(--text)]"
                : "border-[var(--line)] bg-white/95 text-[#1f2937] hover:bg-[var(--panel2)] hover:border-[rgba(167,139,250,.35)] hover:text-[var(--text)]"
            }`}
            role="listitem"
          >
            All
          </button>
          {(showAllCategories ? categories : categories.slice(0, 10)).map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-2 rounded-full border text-[13px] cursor-pointer transition-colors select-none ${
                selectedCategory === cat
                  ? "border-[rgba(45,212,191,.45)] bg-[rgba(45,212,191,.14)] text-[var(--text)]"
                  : "border-[var(--line)] bg-white/95 text-[#1f2937] hover:bg-[var(--panel2)] hover:border-[rgba(167,139,250,.35)] hover:text-[var(--text)]"
              }`}
              role="listitem"
            >
              {cat}
            </button>
          ))}
          {categories.length > 10 && (
            <button
              onClick={() => setShowAllCategories(!showAllCategories)}
              className="px-3 py-2 rounded-full border border-dashed border-[var(--line)] text-[13px] text-[var(--muted-foreground)] cursor-pointer transition-colors hover:bg-[var(--panel2)] hover:border-[rgba(45,212,191,.35)]"
            >
              {showAllCategories ? "Show less" : `+${categories.length - 10} more`}
            </button>
          )}
        </div>

        <div className="flex items-baseline justify-between gap-3 mt-4 mb-2.5">
          <h2 className="text-base m-0 tracking-wide font-semibold">Featured today</h2>
          <div className="flex items-center gap-2">
            <span className="text-[var(--muted-foreground)] text-[13px]">Browse, then ask the assistant to refine.</span>
            <Button
              onClick={() => router.push("/onboarding")}
              variant="outline"
              className="border border-[var(--line)] bg-white/90 px-3 py-2 rounded-full text-[13px] text-[var(--muted-foreground)] transition-colors hover:bg-[var(--panel2)] hover:text-[var(--text)] hover:border-[rgba(45,212,191,.35)]"
            >
              Get Started
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
              <div className="text-center py-12">
                <p className="text-[var(--muted-foreground)]">No products found.</p>
              </div>
            ) : (
              <div className="grid grid-cols-4 gap-4 max-[1020px]:grid-cols-3 max-[720px]:grid-cols-2" aria-label="Product grid">
                {products.map((product) => (
                  <ProductCard key={product.asin} product={product} hideActions />
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
