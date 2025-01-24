import React from 'react'

import { PendingUploadBox } from './component/box/pending_upload_box.tsx'
import { PreviosUploadBox } from './component/box/previous_upload_box.tsx'


const App: React.FC = () => {
  return (
    <div>
      <PendingUploadBox/>
      <PreviosUploadBox/>
    </div>
    
  )
}

export default App;