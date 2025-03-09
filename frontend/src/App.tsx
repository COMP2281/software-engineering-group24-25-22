import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Overview } from './pages/upload';
import { DashBoard } from './pages/dashboard';
import { Login } from './pages/login';
import { Layout } from './component/layout/Layout';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public route */}
        <Route path="/login" element={<Login />} />
        
        {/* Protected routes */}
        <Route element={<Layout />}>
          <Route path="/upload" element={<Overview />} />
          <Route path="/dashboard/:id" element={<DashBoard />} />
          <Route path="/dashboard" element={<DashBoard />} />
          <Route path="/" element={<Navigate to="/upload" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
