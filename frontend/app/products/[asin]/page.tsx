"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Image from "next/image";
import { useUser } from "@/contexts/UserContext";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Star, ShoppingBag } from "lucide-react";
import { TopNav } from "@/components/TopNav";
import { fetchProduct } from "@/lib/api";
import { Product } from "@/lib/types";

export default function ProductDetailPage() {
  const { isAuthenticated } = useUser();
  const router = useRouter();
  const params = useParams();
  const asin = params.asin as string;
  
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    if (asin) {
      loadProduct();
    }
  }, [asin, isAuthenticated, router]);

  const loadProduct = async () => {
    try {
      setLoading(true);
      const data = await fetchProduct(asin);
      setProduct(data);
    } catch (err: any) {
      setError(err.message || "Failed to load product");
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen">
      <TopNav />

      <main className="max-w-[1120px] mx-auto px-5 py-8">
        <Button
          variant="ghost"
          onClick={() => router.back()}
          className="mb-6"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Products
        </Button>

        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-4 text-muted-foreground">Loading product...</p>
          </div>
        )}

        {error && (
          <Card className="max-w-2xl mx-auto">
            <CardContent className="pt-6">
              <div className="text-center text-destructive">
                <p>{error}</p>
                <Button onClick={() => router.push("/products")} className="mt-4">
                  Go to Products
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {!loading && !error && product && (
          <Card className="max-w-4xl mx-auto">
            {product.product_image_url ? (
              <div className="relative w-full h-96 bg-muted rounded-t-lg overflow-hidden">
                <Image
                  src={product.product_image_url}
                  alt={product.product_title || "Product"}
                  fill
                  className="object-contain p-4"
                  sizes="(max-width: 768px) 100vw, 1024px"
                  priority
                />
              </div>
            ) : (
              <div className="relative w-full h-96 bg-muted rounded-t-lg flex items-center justify-center">
                <span className="text-muted-foreground">No Image Available</span>
              </div>
            )}
            <CardHeader>
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <CardTitle className="text-3xl mb-2">
                    {product.product_title || "Untitled Product"}
                  </CardTitle>
                  {product.product_store && (
                    <CardDescription className="text-lg">
                      Sold by {product.product_store}
                    </CardDescription>
                  )}
                </div>
                {product.product_price && (
                  <div className="text-right">
                    <div className="text-4xl font-bold text-primary mb-2">
                      ${product.product_price}
                    </div>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              {(product.product_avg_rating != null && product.product_avg_rating > 0) && (
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Star className="h-5 w-5 fill-yellow-400 text-yellow-400" />
                    <span className="text-xl font-semibold">
                      {product.product_avg_rating.toFixed(1)}
                    </span>
                  </div>
                  {product.product_review_count != null && product.product_review_count > 0 && (
                    <span className="text-muted-foreground">
                      ({product.product_review_count.toLocaleString()} reviews)
                    </span>
                  )}
                </div>
              )}

              {product.product_categories && (
                <div>
                  <h3 className="font-semibold mb-2">Categories</h3>
                  <div className="flex flex-wrap gap-2">
                    {product.product_categories.split(";").filter(cat => cat.trim()).map((cat, idx) => (
                      <Badge key={idx} variant="secondary">
                        {cat.trim()}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {product.product_description && (
                <div>
                  <h3 className="font-semibold mb-2">Description</h3>
                  <p className="text-muted-foreground whitespace-pre-wrap">
                    {product.product_description}
                  </p>
                </div>
              )}

              <div className="pt-4 border-t">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">ASIN:</span>
                    <p className="font-mono">{product.asin}</p>
                  </div>
                  {product.parent_asin && (
                    <div>
                      <span className="text-muted-foreground">Parent ASIN:</span>
                      <p className="font-mono">{product.parent_asin}</p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}
