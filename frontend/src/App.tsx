import { Navigate, Route, Routes } from "react-router-dom";

import { DashboardPage } from "./pages/DashboardPage";
import { ExplorerPage } from "./pages/ExplorerPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardPage />} />
      <Route path="/explorer/:documentationId" element={<ExplorerPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
