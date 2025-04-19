import { useState, useEffect } from "react";
import { useRouter } from "next/router";
import { getUser, isAuthenticated, clearSession } from "@/lib/auth";
import type { User } from "@/types";

interface UseAuthResult {
  user: User | null;
  isLoggedIn: boolean;
  logout: () => void;
}

export function useAuth(requireAuth = false): UseAuthResult {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const loggedIn = isAuthenticated();
    const currentUser = getUser();
    setIsLoggedIn(loggedIn);
    setUser(currentUser);

    if (requireAuth && !loggedIn) {
      router.replace("/auth/login");
    }
  }, [requireAuth, router]);

  const logout = () => {
    clearSession();
    setUser(null);
    setIsLoggedIn(false);
    router.push("/auth/login");
  };

  return { user, isLoggedIn, logout };
}
