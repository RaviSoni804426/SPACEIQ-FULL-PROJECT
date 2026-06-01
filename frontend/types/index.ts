export type UserRole = "user" | "partner" | "admin";
export type SpaceType = "coworking" | "sports" | "meeting_room" | "studio";
export type SlotStatus = "available" | "held" | "booked";
export type BookingStatus = "pending" | "confirmed" | "cancelled" | "completed";

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string | null;
  avatar_url?: string | null;
  role: UserRole;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface TimeSlot {
  id: string;
  date: string;
  start_time: string;
  end_time: string;
  status: SlotStatus;
  held_until?: string | null;
}

export interface Space {
  id: string;
  google_place_id?: string | null;
  name: string;
  type: SpaceType;
  description?: string | null;
  address?: string | null;
  city: string;
  locality?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  price_per_hour: number;
  rating?: number | null;
  total_reviews: number;
  amenities: string[];
  images: string[];
  is_active: boolean;
  website_url?: string | null;
  phone_number?: string | null;
  source: string;
  operating_hours?: Record<string, string[]>;
  availability_count?: number | null;
  available_slots?: TimeSlot[];
}

export interface HoldResponse {
  hold_id: string;
  expires_at: string;
  total_amount: number;
  slot_ids: string[];
  booking_date: string;
}

export interface Booking {
  id: string;
  user_id: string;
  space_id: string;
  slot_id?: string | null;
  booking_date: string;
  start_time: string;
  end_time: string;
  total_amount: number;
  status: BookingStatus;
  razorpay_order_id?: string | null;
  razorpay_payment_id?: string | null;
  cancellation_reason?: string | null;
  created_at: string;
  space_name?: string;
  locality?: string | null;
  image_url?: string | null;
  review_submitted?: boolean;
  review_rating?: number | null;
}

export interface Review {
  id: string;
  user_id: string;
  space_id: string;
  booking_id: string;
  rating: number;
  comment?: string | null;
  created_at: string;
}

export interface ApiError {
  detail: string;
  code: string;
}

export interface AIRevenueDailyPoint {
  date: string;
  revenue: number;
  bookings: number;
}

export interface AIRevenueMonthlyPoint {
  month: string;
  revenue: number;
  bookings: number;
  growth_pct: number | null;
}

export interface AIForecastPoint {
  date: string;
  predicted_revenue: number;
  lower: number;
  upper: number;
}

export interface AIRevenueSegment {
  segment: string;
  revenue: number;
  bookings: number;
  share_pct: number;
}

export interface AICustomerTier {
  segment: string;
  users: number;
  revenue: number;
  avg_recency_days: number;
  avg_successful_bookings: number;
}

export interface AIKeyword {
  keyword: string;
  count: number;
}

export interface AITopicMention {
  topic: string;
  mentions: number;
}

export interface AIChatSpaceCard {
  id: string;
  name: string;
  type: string;
  locality: string | null;
  price_per_hour: number;
  rating: number | null;
  amenities: string[];
  image_url: string | null;
}

export type AIChatAction = "chat" | "show_spaces" | "book_space";

export interface AIChatResponse {
  reply: string;
  action: AIChatAction;
  spaces: AIChatSpaceCard[];
  book_space_id: string | null;
}

export interface AIChatMessage {
  role: "user" | "ai" | "system";
  content: string;
  action?: AIChatAction;
  spaces?: AIChatSpaceCard[];
  book_space_id?: string | null;
}

export interface AIAnalyticsOverview {
  total_bookings: number;
  successful_bookings: number;
  total_revenue: number;
  avg_booking_value: number;
  cancellation_rate_pct: number;
  repeat_customer_rate_pct: number;
  search_to_booking_conversion_pct: number;
  month_over_month_growth_pct: number | null;
  projected_next_30d_revenue: number;
  forecast_confidence: "low" | "medium" | "high";
}

export interface AIAnalyticsPayload {
  generated_at: string;
  overview: AIAnalyticsOverview;
  revenue: {
    daily: AIRevenueDailyPoint[];
    monthly: AIRevenueMonthlyPoint[];
    forecast_next_14_days: AIForecastPoint[];
  };
  segmentation: {
    by_space_type: AIRevenueSegment[];
    by_locality: AIRevenueSegment[];
    customer_tiers: AICustomerTier[];
  };
  nlp: {
    review_sentiment: {
      positive_pct: number;
      neutral_pct: number;
      negative_pct: number;
      sample_size: number;
      average_rating: number;
    };
    top_keywords: AIKeyword[];
    topic_breakdown: AITopicMention[];
  };
  recommendations: string[];
}
