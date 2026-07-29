import { Routes, Route } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import OverviewPage from "./pages/OverviewPage";
import SendPage from "./pages/SendPage";
import ReceivePage from "./pages/ReceivePage";
import HistoryPage from "./pages/HistoryPage";
import MasternodesPage from "./pages/MasternodesPage";
import GovernancePage from "./pages/GovernancePage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/send" element={<SendPage />} />
        <Route path="/receive" element={<ReceivePage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/masternodes" element={<MasternodesPage />} />
        <Route path="/governance" element={<GovernancePage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
