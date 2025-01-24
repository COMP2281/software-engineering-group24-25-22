import React from 'react'

import { PendingUploadBox } from './component/box/pending_upload_box.tsx'
import { PreviosUploadBox } from './component/box/previous_upload_box.tsx'


const App: React.FC = () => {
  return (
    <div className="flex flex-col lg:flex-row lg:h-screen">
      <div className="lg:w-1/2 w-full">
        <PendingUploadBox />
      </div>
      <div className="lg:w-1/2 w-full">
        <PreviosUploadBox />
      </div>
    </div>
  );
};


export default App;