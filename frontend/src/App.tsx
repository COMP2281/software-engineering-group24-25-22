import React, { useState, useEffect } from "react";

import { UploadConfiguration } from './pages/upload_configuration';
import { DashBoard } from './pages/dashboard'
import { Header } from './component/header';

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
        return <UploadConfiguration />
      case "#dashboard":
        return <DashBoard />
      default:
        return <UploadConfiguration />
    }
  }

  return (
    <div className="h-screen flex flex-col">
        <Header />
        
      
      <div className="h-[70%] ">
        {renderPage()}
      </div>
    </div>
  );
};

export default App;
