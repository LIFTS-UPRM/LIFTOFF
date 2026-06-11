"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import styles from "./page.module.css";

type AuthMode = "signin" | "signup";

function LoadingSpinner() {
  return <span className={styles.spinner} aria-hidden="true" />;
}

export default function Home() {
  const router = useRouter();
  const [mode, setMode] = useState<AuthMode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    setIsLoading(true);

    const supabase = createClient();

    try {
      if (mode === "signup") {
        const { error: signUpError } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { display_name: displayName || email.split("@")[0] } },
        });
        if (signUpError) throw signUpError;
        setSuccessMsg("Account created — check your email to confirm, then sign in.");
        setMode("signin");
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInError) throw signInError;
        router.push("/chat");
        router.refresh();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.overlay} />
      <section className={styles.loginCard} aria-label="Login panel">
        <div className={styles.authPanel}>
          <div className={styles.brandLockup}>
            <Image
              src="/assets/STRATOS_LOGO_PNG_NO_BG/Color_text.png"
              alt="STRATOS"
              width={438}
              height={365}
              priority
              className={styles.brandLogo}
            />
          </div>
          <p className={styles.subtitle}>
            {mode === "signin"
              ? "Sign in to access mission chat and flight operations."
              : "Create your STRATOS account to get started."}
          </p>
        </div>

        <form className={styles.form} onSubmit={handleSubmit} noValidate>
          {mode === "signup" && (
            <div className={styles.formField}>
              <label className={styles.formLabel} htmlFor="displayName">
                Display name
              </label>
              <input
                id="displayName"
                className={styles.formInput}
                type="text"
                autoComplete="name"
                placeholder="Your name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </div>
          )}

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="email">
              Email
            </label>
            <input
              id="email"
              className={styles.formInput}
              type="email"
              autoComplete="email"
              placeholder="you@lifts-uprm.com"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className={styles.formField}>
            <label className={styles.formLabel} htmlFor="password">
              Password
            </label>
            <input
              id="password"
              className={styles.formInput}
              type="password"
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              placeholder={mode === "signup" ? "At least 6 characters" : "••••••••"}
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && <p className={styles.formError} role="alert">{error}</p>}
          {successMsg && <p className={styles.formSuccess} role="status">{successMsg}</p>}

          <button
            className={styles.formSubmit}
            type="submit"
            disabled={isLoading}
            aria-busy={isLoading}
          >
            {isLoading ? (
              <>
                <LoadingSpinner />
                {mode === "signin" ? "Signing in…" : "Creating account…"}
              </>
            ) : mode === "signin" ? (
              "Sign in"
            ) : (
              "Create account"
            )}
          </button>

          <p className={styles.formToggle}>
            {mode === "signin" ? (
              <>
                No account?{" "}
                <button
                  type="button"
                  className={styles.formToggleLink}
                  onClick={() => { setMode("signup"); setError(null); setSuccessMsg(null); }}
                >
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{" "}
                <button
                  type="button"
                  className={styles.formToggleLink}
                  onClick={() => { setMode("signin"); setError(null); setSuccessMsg(null); }}
                >
                  Sign in
                </button>
              </>
            )}
          </p>
        </form>
      </section>
    </main>
  );
}
