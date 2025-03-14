import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Dashboard } from './pages/dashboard';
import { Upload } from './pages/upload';
import { Login } from './pages/login';
import { Layout } from './component/layout/Layout';
import { DashBoardView } from './pages/dashboard_view';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route */}
        <Route path="/login" element={<Login />} />
        
        {/* Protected routes */}
        <Route element={<Layout />}>
          <Route path="/upload" element={<Upload />} />
          <Route path="/upload/:id" element={<Upload />} />
          <Route path="/dashboard/:id" element={<DashBoardView />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/" element={<Navigate to="/dashbaord" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
