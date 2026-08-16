import { Suspense, lazy } from "react";
import { Routes, Route } from "react-router-dom";
import AppLayout from "./layouts/AppLayout.jsx";
import DashboardLayout from "./layouts/DashboardLayout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Landing from "./pages/Landing.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Search from "./pages/Search.jsx";
import BookDetails from "./pages/BookDetails.jsx";
import Chat from "./pages/Chat.jsx";
import Scanner from "./pages/Scanner.jsx";
import Wishlist from "./pages/Wishlist.jsx";
import ReadingTracker from "./pages/ReadingTracker.jsx";
import Preferences from "./pages/Preferences.jsx";
import NotFound from "./pages/NotFound.jsx";

// recharts pulls in a sizeable dependency tree — only load it when the
// user actually visits the analytics page, not on every route.
const Analytics = lazy(() => import("./pages/Analytics.jsx"));

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Landing />} />
      </Route>

      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/search" element={<Search />} />
        <Route path="/books/:id" element={<BookDetails />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/scanner" element={<Scanner />} />
        <Route path="/wishlist" element={<Wishlist />} />
        <Route path="/reading" element={<ReadingTracker />} />
        <Route
          path="/analytics"
          element={
            <Suspense
              fallback={<p className="text-sm text-parchment/40">Loading analytics…</p>}
            >
              <Analytics />
            </Suspense>
          }
        />
        <Route path="/preferences" element={<Preferences />} />
      </Route>

      <Route
        element={
          <AppLayout />
        }
      >
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
