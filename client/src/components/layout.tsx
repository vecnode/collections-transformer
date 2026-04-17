'use client'

import SideBar from './sidebar'
import UserConnectionTracker from './userConnectionTracker'

const RootLayout = ({ children }) => {
  return (
    <>
    <UserConnectionTracker />
    <div style={{ display: 'flex', height: '100%' }}>
      <SideBar />
      <div className="page-content">{children}</div>
    </div>
    </>
  );
};

export default RootLayout;
