"use client";

import Link from "next/link";
import Image from "next/image";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Product } from "@/lib/types";
import { Star } from "lucide-react";

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const imageUrl = product.product_image_url;
  const title = product.product_title || "Untitled Product";
  const store = product.product_store || "Unknown Store";
  const price = product.product_price || "N/A";
  const rating = product.product_avg_rating;
  const reviewCount = product.product_review_count;
  const category = product.product_main_category || "Uncategorized";
  
  return (
    <Link href={`/products/${product.asin}`}>
      <Card className="border border-[var(--line)] bg-white/95 rounded-[var(--radius)] overflow-hidden shadow-none transition-all duration-[180ms] flex flex-col min-h-[240px] hover:-translate-y-0.5 hover:shadow-[var(--shadow)] hover:border-[rgba(45,212,191,.28)]">
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
              <>
                <Badge className="border border-[var(--line)] bg-[rgba(241,245,249,.9)] px-2 py-0.5 rounded-full text-[11px] text-[rgba(24,34,48,.82)]">
                  ⭐ {rating.toFixed(1)}
                </Badge>
                {reviewCount != null && reviewCount > 0 && (
                  <span className="text-xs">({reviewCount.toLocaleString()} reviews)</span>
                )}
              </>
            )}
            {category && (
              <Badge className="border border-[var(--line)] bg-[rgba(241,245,249,.9)] px-2 py-0.5 rounded-full text-[11px] text-[rgba(24,34,48,.82)]">
                {category}
              </Badge>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}
