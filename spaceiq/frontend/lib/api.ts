import axios from "axios";

import { getAuthSnapshot } from "@/store/auth-store";
import type {
  Booking,
  HoldResponse,
  Review,
  Space,
  TokenPair,
  User,
} from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = getAuthSnapshot().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => Promise.reject(error.response?.data ?? error),
);

export const apiClient = {
  login: async (payload: { email: string; password: string }) => {
    const { data } = await api.post<TokenPair>("/api/auth/login", payload);
    return data;
  },
  register: async (payload: { email: string; password: string; full_name: string; phone?: string }) => {
    const { data } = await api.post<TokenPair>("/api/auth/register", payload);
    return data;
  },
  me: async () => {
    const { data } = await api.get<User>("/api/auth/me");
    return data;
  },
  updateProfile: async (payload: { full_name: string; phone?: string | null; avatar_url?: string | null }) => {
    const { data } = await api.put<User>("/api/auth/me", payload);
    return data;
  },
  spaces: async (params?: Record<string, string | number | string[] | undefined | null>) => {
    const { data } = await api.get<Space[]>("/api/spaces", { params });
    return data;
  },
  space: async (spaceId: string, date?: string) => {
    const { data } = await api.get<Space>(`/api/spaces/${spaceId}`, {
      params: date ? { date } : undefined,
    });
    return data;
  },
  holdBooking: async (payload: { space_id: string; date: string; slot_ids: string[] }) => {
    const { data } = await api.post<HoldResponse>("/api/bookings/hold", payload);
    return data;
  },
  initPayment: async (holdId: string) => {
    const { data } = await api.post<{
      order_id: string;
      key_id: string;
      amount: number;
      currency: string;
      mode: "razorpay" | "demo";
      hold_id: string;
      booking_summary: Record<string, string | number>;
    }>("/api/payments/init", { hold_id: holdId });
    return data;
  },
  verifyPayment: async (payload: {
    hold_id: string;
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
  }) => {
    const { data } = await api.post<Booking>("/api/payments/verify", payload);
    return data;
  },
  myBookings: async () => {
    const { data } = await api.get<Booking[]>("/api/bookings/my");
    return data;
  },
  booking: async (bookingId: string) => {
    const { data } = await api.get<Booking>(`/api/bookings/${bookingId}`);
    return data;
  },
  cancelBooking: async (bookingId: string, reason: string) => {
    const { data } = await api.put<Booking>(`/api/bookings/${bookingId}/cancel`, { reason });
    return data;
  },
  createReview: async (payload: { booking_id: string; rating: number; comment?: string }) => {
    const { data } = await api.post<Review>("/api/reviews", payload);
    return data;
  },
};
