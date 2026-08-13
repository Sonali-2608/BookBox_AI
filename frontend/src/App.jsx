import { Routes, Route } from "react-router-dom";
import AppLayout from "./layouts/AppLayout.jsx";
import DashboardLayout from "./layouts/DashboardLayout.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Landing from "./pages/Landing.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Search from "./pages/Search.jsx";
import BookDetails from "./pages/BookDetails.jsx";
import NotFound from "./pages/NotFound.jsx";

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
