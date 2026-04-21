import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

export function Navbar() {
  const { user, isLoggedIn, logout } = useAuth();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-sm border-b border-stone-100">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-7 h-7 rounded-lg bg-stone-900 flex items-center justify-center">
            <span className="text-amber-400 text-xs font-bold font-mono">Q</span>
          </div>
          <span className="font-display font-semibold text-stone-900 text-base tracking-tight">
            QuarterWatch
          </span>
        </Link>

        <nav className="flex items-center gap-1">
          {isLoggedIn ? (
            <>
              <Link
                href="/dashboard"
                className="text-sm text-stone-600 hover:text-stone-900 px-3 py-1.5 rounded-lg hover:bg-stone-50 transition-colors"
              >
                Dashboard
              </Link>
              <div className="w-px h-4 bg-stone-200 mx-1" />
              <div className="flex items-center gap-2.5 pl-2">
                {user?.avatar_url ? (
                  <Image
                    src={user.avatar_url}
                    alt={user.name ?? user.email}
                    width={28}
                    height={28}
                    className="rounded-full ring-1 ring-stone-200"
                  />
                ) : (
                  <div className="w-7 h-7 rounded-full bg-amber-100 flex items-center justify-center">
                    <span className="text-amber-700 text-xs font-semibold">
                      {(user?.name ?? user?.email ?? "U")[0].toUpperCase()}
                    </span>
                  </div>
                )}
                <button
                  onClick={logout}
                  className="text-sm text-stone-500 hover:text-stone-800 transition-colors"
                >
                  Sign out
                </button>
              </div>
            </>
          ) : (
            <>
              <Link
                href="/auth/login"
                className="text-sm text-stone-600 hover:text-stone-900 px-3 py-1.5 rounded-lg hover:bg-stone-50 transition-colors"
              >
                Sign in
              </Link>
              <Link href="/auth/register" className="btn-primary text-sm">
                Get started
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
