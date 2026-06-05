import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './components/Dashboard';
import { ApprovalScreen } from './components/ApprovalScreen';
import { AnalyticsDashboard } from './components/AnalyticsDashboard';
import { ChatAssistant } from './components/ChatAssistant';

export default function App() {
  return (
    <Router>
      <div className="size-full flex">
        <Sidebar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/approval" element={<ApprovalScreen />} />
          <Route path="/analytics" element={<AnalyticsDashboard />} />
          <Route path="/chat" element={<ChatAssistant />} />
        </Routes>
      </div>
    </Router>
  );
}