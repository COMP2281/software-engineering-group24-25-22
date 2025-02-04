import React from 'react';
import { UploadConfiguration } from './pages/upload_configuration';
import { Header } from './component/header';

const App: React.FC = () => {
  return (
    <div className="h-screen flex flex-col">
        <Header />
        
      
      <div className="h-[70%] ">
        <UploadConfiguration />
      </div>
    </div>
  );
};

export default App;
