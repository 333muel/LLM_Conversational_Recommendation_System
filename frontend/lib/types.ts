export interface Product {
  asin: string;
  parent_asin?: string;
  product_title?: string;
  product_description?: string;
  product_avg_rating?: number | null;
  product_review_count?: number | null;
  product_price?: string;
  product_store?: string;
  product_categories?: string;
  product_main_category?: string;
  product_image_url?: string;
  product_images?: Array<{
    thumb?: string;
    large?: string;
    hi_res?: string;
    variant?: string;
  }>;
}

export interface ProductsResponse {
  products: Product[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface Recommendation {
  item_id: string;
  title: string;
  description: string;
  rating: number;
  price: string;
  categories: string;
  score: number;
  rank: number;
}

export interface RecommendationResponse {
  response: string;
  recommendations: Recommendation[];
  user_id: string;
  success: boolean;
  debug?: {
    raw_recommendations_count: number;
    product_details_count: number;
    has_final_response: boolean;
    algorithm_used: string;
    model_used: string;
  };
}

export interface RecommendationRequest {
  message: string;
  user_id?: string;
  top_k?: number;
  model?: string;
  algorithm?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  recommendations?: Recommendation[];
  timestamp: Date;
}
