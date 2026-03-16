import { 
  Product, ProductsResponse, RecommendationResponse, RecommendationRequest, 
  BrowseRequest, BrowseResponse,
  ExtractRequest, ExtractResponse,
  FilterRequest, FilterResponse,
  RespondRequest, RespondResponse, 
  ExplainResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchProducts(
  limit: number = 20,
  skip: number = 0,
  category?: string
): Promise<ProductsResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    skip: skip.toString(),
  });
  
  if (category) {
    params.append("category", category);
  }
  
  const response = await fetch(`${API_BASE_URL}/api/products?${params}`);
  
  if (!response.ok) {
    throw new Error("Failed to fetch products");
  }
  
  return response.json();
}

export async function fetchProduct(asin: string): Promise<Product> {
  const response = await fetch(`${API_BASE_URL}/api/products/${asin}`);
  
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Product not found");
    }
    throw new Error("Failed to fetch product");
  }
  
  return response.json();
}

export async function fetchRecommendations(
  request: RecommendationRequest
): Promise<RecommendationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error("Failed to get recommendations");
  }
  
  return response.json();
}

export async function fetchBaselineRecommendations(
  request: RecommendationRequest
): Promise<BrowseResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/baseline`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error("Failed to get baseline recommendations");
  }
  
  return response.json();
}

export async function fetchAvailableAlgorithms(): Promise<{ algorithms: string[]; count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/algorithms/available`);
  
  if (!response.ok) {
    throw new Error("Failed to fetch algorithms");
  }
  
  return response.json();
}

export async function fetchAvailableCategories(): Promise<{ categories: string[]; count: number }> {
  const response = await fetch(`${API_BASE_URL}/api/products/categories/list`);
  
  if (!response.ok) {
    throw new Error("Failed to fetch categories");
  }
  
  return response.json();
}

export async function fetchBrowseDiscovery(
  request: BrowseRequest
): Promise<BrowseResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/browse`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error("Failed to get browse discovery");
  }
  
  return response.json();
}

export async function extractConstraints(
  request: ExtractRequest
): Promise<ExtractResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error("Failed to extract constraints");
  return response.json();
}

export async function filterProducts(
  request: FilterRequest
): Promise<FilterResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/filter`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error("Failed to filter products");
  return response.json();
}

export async function respondToProducts(
  request: RespondRequest
): Promise<RespondResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error("Failed to generate response");
  return response.json();
}

export async function selectProduct(asin: string, conversationId: string, userId: string): Promise<void> {
  await fetch(`${API_BASE_URL}/api/conversation/select_item`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: asin, conversation_id: conversationId, user_id: userId }),
  });
}

export async function submitFeedback(
  asin: string, 
  conversationId: string, 
  userId: string, 
  feedbackType: "like" | "dislike"
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: asin, conversation_id: conversationId, user_id: userId, feedback_type: feedbackType }),
  });
  if (!response.ok) throw new Error("Failed to submit feedback");
}

export async function explainRecommendation(
  asin: string, 
  conversationId: string, 
  userId: string,
  llmProvider?: string
): Promise<ExplainResponse> {
  const response = await fetch(`${API_BASE_URL}/api/conversation/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ 
      item_id: asin, 
      conversation_id: conversationId, 
      user_id: userId,
      llm_provider: llmProvider
    }),
  });
  if (!response.ok) throw new Error("Failed to explain recommendation");
  return response.json();
}
