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
