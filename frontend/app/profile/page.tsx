"use client";

import { TopNav } from "@/components/TopNav";
import { useUser } from "@/contexts/UserContext";

export default function ProfilePage() {
  const { userId } = useUser();
  
  return (
    <div className="min-h-screen">
      <TopNav />
      <main className="max-w-[1120px] mx-auto px-5 py-8">
        <h1 className="text-2xl font-bold mb-4">Profile</h1>
        <p className="text-[var(--muted-foreground)] mb-2">User ID: {userId}</p>
        <p className="text-[var(--muted-foreground)]">This feature is coming soon.</p>
      </main>
    </div>
  );
}
