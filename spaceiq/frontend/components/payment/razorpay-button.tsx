"use client";

import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useInitPayment, useVerifyPayment } from "@/hooks/use-bookings";
import { loadRazorpayScript } from "@/lib/razorpay";
import { useAuthStore } from "@/store/auth-store";

export function RazorpayButton({
  holdId,
  label = "Proceed to Payment",
  onSuccess,
  redirectOnSuccess = true,
}: {
  holdId: string;
  label?: string;
  onSuccess?: (bookingId: string) => void;
  redirectOnSuccess?: boolean;
}) {
  const [loading, setLoading] = useState(false);
  const initPayment = useInitPayment();
  const verifyPayment = useVerifyPayment();
  const user = useAuthStore((state) => state.user);
  const router = useRouter();

  async function handlePay() {
    setLoading(true);
    try {
      const init = await initPayment.mutateAsync(holdId);
      if (init.mode === "demo") {
        const paymentId =
          typeof crypto !== "undefined" && "randomUUID" in crypto
            ? `pay_demo_${crypto.randomUUID().replace(/-/g, "").slice(0, 18)}`
            : `pay_demo_${Date.now()}`;
        const booking = await verifyPayment.mutateAsync({
          hold_id: holdId,
          razorpay_order_id: init.order_id,
          razorpay_payment_id: paymentId,
          razorpay_signature: "demo_signature",
        });
        toast.success("Demo payment completed and booking confirmed.");
        onSuccess?.(booking.id);
        if (redirectOnSuccess) {
          router.push(`/my-bookings?success=${booking.id}`);
        }
        return;
      }

      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded || !window.Razorpay) {
        toast.error("Razorpay checkout could not be loaded.");
        return;
      }

      const razorpay = new window.Razorpay({
        key: init.key_id,
        amount: init.amount,
        currency: init.currency,
        order_id: init.order_id,
        name: "SpaceIQ",
        description: init.booking_summary.space_name,
        prefill: {
          name: user?.full_name ?? "",
          email: user?.email ?? "",
          contact: user?.phone ?? "",
        },
        handler: async (response: {
          razorpay_order_id: string;
          razorpay_payment_id: string;
          razorpay_signature: string;
        }) => {
          const booking = await verifyPayment.mutateAsync({
            hold_id: holdId,
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          toast.success("Payment verified and booking confirmed.");
          onSuccess?.(booking.id);
          if (redirectOnSuccess) {
            router.push(`/my-bookings?success=${booking.id}`);
          }
        },
        theme: {
          color: "#F97316",
        },
      });
      razorpay.open();
    } catch (error) {
      const detail = error && typeof error === "object" && "detail" in error ? String(error.detail) : "Payment could not be started.";
      toast.error(detail);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Button className="w-full" disabled={loading} onClick={handlePay} size="lg" type="button">
      {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
      {label}
    </Button>
  );
}
