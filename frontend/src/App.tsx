import React, { useState, useEffect } from "react";

import { Overview } from './pages/overview';
import { DashBoard } from './pages/dashboard'
import { Header } from './component/header';
import { Login } from "./pages/login";

const App: React.FC = () => {
  const [hash, setHash] = useState(window.location.hash)

  useEffect(() => {
    const handleHashChange = () => {
      setHash(window.location.hash)
    }
    window.addEventListener("hashchange", handleHashChange);

    return() => {
      window.removeEventListener("hashchange", handleHashChange)
    }
  })

  const renderPage = () => {
    switch (hash){
      case "#upload":
        return <Overview />
      case "#dashboard":
        return <DashBoard />
      case "#login":
        return <Login />
      default:
        return <Overview />
    }
  }

  return (
    <div className="h-fill flex flex-col">
        <Header />
        
      
      <div className="">
        {renderPage()}
      </div>
    </div>
  );
};

export default App;
