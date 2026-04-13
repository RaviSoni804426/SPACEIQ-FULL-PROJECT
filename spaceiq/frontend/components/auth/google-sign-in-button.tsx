"use client";

import { useEffect, useId, useRef } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { useGoogleLogin } from "@/hooks/use-auth";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (options: {
            client_id: string;
            callback: (response: { credential?: string }) => void;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            options: {
              theme?: "outline" | "filled_blue" | "filled_black";
              size?: "large" | "medium" | "small";
              shape?: "rectangular" | "pill" | "circle" | "square";
              text?: "signin_with" | "signup_with" | "continue_with" | "signin";
              width?: number;
              logo_alignment?: "left" | "center";
            },
          ) => void;
        };
      };
    };
  }
}

function getErrorDetail(error: unknown) {
  if (error && typeof error === "object" && "detail" in error && typeof error.detail === "string") {
    return error.detail;
  }
  return "Google sign-in could not be completed.";
}

export function GoogleSignInButton({ mode = "signin" }: { mode?: "signin" | "signup" }) {
  const router = useRouter();
  const googleLogin = useGoogleLogin();
  const buttonId = useId().replace(/:/g, "");
  const containerRef = useRef<HTMLDivElement | null>(null);
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID;

  useEffect(() => {
    if (!clientId || !containerRef.current) {
      return;
    }

    const safeClientId = clientId;
    const container = containerRef.current;

    async function renderGoogleButton() {
      if (!window.google?.accounts?.id) {
        await loadGoogleScript();
      }
      if (!window.google?.accounts?.id || !container) {
        return;
      }

      container.innerHTML = "";
      window.google.accounts.id.initialize({
        client_id: safeClientId,
        callback: async (response) => {
          if (!response.credential) {
            toast.error("Google did not return a valid credential.");
            return;
          }
          try {
            await googleLogin.mutateAsync({ id_token: response.credential });
            toast.success(mode === "signup" ? "Account created with Google." : "Signed in with Google.");
            router.push("/dashboard");
          } catch (error) {
            toast.error(getErrorDetail(error));
          }
        },
      });
      window.google.accounts.id.renderButton(container, {
        theme: "outline",
        size: "large",
        shape: "pill",
        text: mode === "signup" ? "signup_with" : "signin_with",
        width: 360,
        logo_alignment: "left",
      });
    }

    void renderGoogleButton();
  }, [buttonId, clientId, googleLogin, mode, router]);

  if (!clientId) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-slate-200" />
        <span className="text-xs font-medium uppercase tracking-[0.2em] text-slate-400">or</span>
        <div className="h-px flex-1 bg-slate-200" />
      </div>
      <div className="flex justify-center">
        <div id={`google-signin-${buttonId}`} ref={containerRef} />
      </div>
    </div>
  );
}

async function loadGoogleScript() {
  const existing = document.querySelector<HTMLScriptElement>('script[data-google-identity="true"]');
  if (existing) {
    if (window.google?.accounts?.id) {
      return;
    }
    await waitForGoogle();
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Failed to load Google Identity Services"));
    document.head.appendChild(script);
  });
  await waitForGoogle();
}

async function waitForGoogle() {
  await new Promise<void>((resolve, reject) => {
    let attempts = 0;
    const interval = window.setInterval(() => {
      attempts += 1;
      if (window.google?.accounts?.id) {
        window.clearInterval(interval);
        resolve();
        return;
      }
      if (attempts > 50) {
        window.clearInterval(interval);
        reject(new Error("Google Identity Services did not initialize"));
      }
    }, 100);
  });
}
