import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Overview } from './pages/overview';
import { DashBoard } from './pages/dashboard';
import { Login } from './pages/login';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/upload" element={<Overview />} />
        <Route path="/dashboard/:id" element={<DashBoard />} />
        <Route path="/dashboard" element={<DashBoard />} />
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Navigate to="/upload" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
