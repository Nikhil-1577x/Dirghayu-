import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Medications from './pages/Medications';
import Reports from './pages/Reports';
import Alerts from './pages/Alerts';
import Appointments from './pages/Appointments';
import { useApi } from './api/useApi';
import { useWebSocket } from './api/useWebSocket';

function AppLayout({ children }: { children: React.ReactNode }) {
  useApi();
  useWebSocket();
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'linear-gradient(180deg, #fafbfd 0%, #f1f5f9 100%)' }}>
      <Sidebar />
      <div
        style={{
          flex: 1,
          marginLeft: 'var(--sidebar-width)',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
        }}
      >
        <Navbar />
        <main
          style={{
            flex: 1,
            padding: '32px 40px 48px',
            maxWidth: 1640,
            width: '100%',
            margin: '0 auto',
            overflowX: 'hidden',
          }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/medications" element={<Medications />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/appointments" element={<Appointments />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}

export default App;
