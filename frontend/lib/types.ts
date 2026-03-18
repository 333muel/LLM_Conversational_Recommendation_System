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
  main_category?: string;
  image?: string;
  score: number;
  rank: number;
}

export interface RecommendationResponse {
  response: string;
  conversation_id: string;
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
  conversation_id?: string;
  user_id?: string;
  top_k?: number;
  model?: string;
  llm_provider?: string;
  algorithm?: string;
}

export interface BrowseRequest {
  message: string;
  conversation_id?: string;
  user_id?: string;
  llm_provider?: string;
  algorithm?: string;
}

export interface BrowseResponse {
  response: string;
  conversation_id: string;
  products: Recommendation[];
  constraints: Record<string, any>;
  metadata: Record<string, any>;
  success: boolean;
  error?: string;
}

export interface ExtractRequest {
  message: string;
  user_id?: string;
  llm_provider?: string;
}

export interface ExtractResponse {
  constraints: Record<string, any>;
  intent: string;
  success: boolean;
}

export interface FilterRequest {
  constraints: Record<string, any>;
  user_id?: string;
  algorithm?: string;
  exclude_item_ids?: string[];
  limit?: number;
}

export interface FilterResponse {
  products: Recommendation[];
  metadata: Record<string, any>;
  success: boolean;
}

export interface RespondRequest {
  message: string;
  conversation_id: string;
  user_id: string;
  product_details: any[];
  llm_provider?: string;
  metadata?: Record<string, any>;
}

export interface RespondResponse {
  response: string;
  conversation_id: string;
  success: boolean;
}

export interface ExplainRequest {
  item_id: string;
  conversation_id: string;
  user_id: string;
  message?: string;
  llm_provider?: string;
}

export interface ExplainResponse {
  explanation: string;
  product_id: string;
  attribute_scores?: Record<string, number>;
  success: boolean;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  recommendations?: Recommendation[];
  timestamp: Date;
}
