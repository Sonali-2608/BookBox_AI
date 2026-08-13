import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  BookOpen,
  LayoutDashboard,
  Search,
  Heart,
  BookMarked,
  ScanLine,
  MessageCircleHeart,
  BarChart3,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth.js";

const navItems = [
  { label: "Overview", icon: LayoutDashboard, to: "/dashboard", enabled: true },
  { label: "Search", icon: Search, to: "/search", enabled: true },
  { label: "Wishlist", icon: Heart, to: "/wishlist", enabled: false },
  { label: "Reading tracker", icon: BookMarked, to: "/reading", enabled: false },
  { label: "Scanner", icon: ScanLine, to: "/scanner", enabled: false },
  { label: "Ask Lexora", icon: MessageCircleHeart, to: "/chat", enabled: false },
  { label: "Analytics", icon: BarChart3, to: "/analytics", enabled: false },
];

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen bg-ink">
      <aside className="hidden w-64 shrink-0 border-r border-ink-line/60 bg-ink-deep md:flex md:flex-col">
        <Link to="/" className="flex items-center gap-2 px-6 py-6">
          <BookOpen className="h-5 w-5 text-brass" strokeWidth={1.75} />
          <span className="font-display text-xl italic text-parchment">Lexora</span>
        </Link>

        <nav className="flex-1 space-y-1 px-3">
          {navItems.map((item) =>
            item.enabled ? (
              <NavLink
                key={item.label}
                to={item.to}
                end={item.to === "/dashboard"}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                    isActive
                      ? "bg-brass/15 text-brass"
                      : "text-parchment/70 hover:bg-parchment/5 hover:text-parchment"
                  }`
                }
              >
                <item.icon className="h-4 w-4" strokeWidth={1.75} />
                {item.label}
              </NavLink>
            ) : (
              <div
                key={item.label}
                className="flex cursor-not-allowed items-center justify-between gap-3 rounded-lg px-3 py-2.5 text-sm text-parchment/30"
                title="Coming in a later phase"
              >
                <span className="flex items-center gap-3">
                  <item.icon className="h-4 w-4" strokeWidth={1.75} />
                  {item.label}
                </span>
                <span className="call-number !text-parchment/25">soon</span>
              </div>
            )
          )}
        </nav>

        <div className="border-t border-ink-line/60 p-4">
          <div className="flex items-center gap-3">
            {user?.profile_image ? (
              <img
                src={user.profile_image}
                alt={user.name}
                className="h-9 w-9 rounded-full border border-brass/40"
                referrerPolicy="no-referrer"
              />
            ) : (
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brass/20 font-mono text-xs text-brass">
                {user?.name?.[0]?.toUpperCase() ?? "?"}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-parchment">{user?.name}</p>
              <p className="truncate text-xs text-parchment/50">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={async () => {
              await logout();
              navigate("/");
            }}
            className="mt-4 w-full text-left text-xs text-parchment/50 hover:text-parchment"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 items-center justify-between border-b border-ink-line/60 px-6 md:hidden">
          <Link to="/" className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-brass" strokeWidth={1.75} />
            <span className="font-display text-xl italic text-parchment">Lexora</span>
          </Link>
          <button
            onClick={async () => {
              await logout();
              navigate("/");
            }}
            className="text-xs text-parchment/60"
          >
            Sign out
          </button>
        </header>

        <main className="flex-1 px-6 py-8 md:px-10 md:py-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
