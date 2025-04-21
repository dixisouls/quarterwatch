import { Navbar } from "./Navbar";
import { cn } from "@/lib/utils";

interface LayoutProps {
  children: React.ReactNode;
  className?: string;
  maxWidth?: "sm" | "md" | "lg" | "xl" | "full";
}

const maxWidthMap = {
  sm: "max-w-xl",
  md: "max-w-2xl",
  lg: "max-w-4xl",
  xl: "max-w-6xl",
  full: "max-w-full",
};

export function Layout({ children, className, maxWidth = "xl" }: LayoutProps) {
  return (
    <div className="min-h-screen bg-stone-25">
      <Navbar />
      <main
        className={cn(
          "mx-auto px-6 pt-24 pb-16",
          maxWidthMap[maxWidth],
          className
        )}
      >
        {children}
      </main>
    </div>
  );
}
