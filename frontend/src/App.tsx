import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Overview } from './pages/upload';
import { DashBoard } from './pages/dashboard';
import { Login } from './pages/login';
import { Layout } from './component/layout/Layout';

interface pendingItem {
  id: string;
  title: string;
  merchant: string;
  time: string;
  address: string;
  ref: string;
  cost: string;
  description: string;
  tax: string;
  category: string;
  edit: boolean;
}


const pendingItems: pendingItem[] = [
  {
      id: '1',
      title: 'Receipt1',
      merchant: 'Walmart',
      time: '10:00 AM',
      address: '123 Main St, Anytown, USA',
      ref: '1234567890',
      cost: '100.00',
      description: 'Weekly grocery shopping including fresh produce, dairy products, and household essentials',
      tax: '10.00',
      category: 'Groceries',
      edit: true,
  },
  {
      id: '2',
      title: 'Receipt2',
      merchant: 'Target',
      time: '11:30 AM',
      address: '456 Oak St, Anytown, USA',
      ref: '2345678901',
      cost: '75.50',
      description: 'Home organization items: storage bins, hangers, and bathroom accessories',
      tax: '7.55',
      category: 'Home Goods',
      edit: true,
  },
  {
      id: '3',
      title: 'Receipt3',
      merchant: 'Best Buy',
      time: '2:15 PM',
      address: '789 Tech Blvd, Anytown, USA',
      ref: '3456789012',
      cost: '299.99',
      description: 'New laptop accessories: wireless mouse, keyboard, and external monitor',
      tax: '30.00',
      category: 'Electronics',
      edit: true,
  },
  {
      id: '4',
      title: 'Receipt4',
      merchant: 'Costco',
      time: '3:45 PM',
      address: '321 Bulk Ave, Anytown, USA',
      ref: '4567890123',
      cost: '250.00',
      description: 'Bulk office supplies: printer paper, ink cartridges, and cleaning supplies',
      tax: '25.00',
      category: 'Bulk Supplies',
      edit: false,
  },
  {
      id: '5',
      title: 'Receipt5',
      merchant: 'Whole Foods',
      time: '5:00 PM',
      address: '654 Health Way, Anytown, USA',
      ref: '5678901234',
      cost: '150.75',
      description: 'Organic produce and specialty items for weekly meal prep',
      tax: '15.08',
      category: 'Groceries',
      edit: false,
  },
];

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
