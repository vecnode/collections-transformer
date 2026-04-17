// @ts-nocheck
import { useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';

const UserConnectionTracker = () => {
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;

    let isPageVisible = true;
    let lastActivityTime = Date.now();
    const ACTIVITY_TIMEOUT = 5 * 60 * 1000; // 5 minutes

    // Track page visibility changes
    const handleVisibilityChange = () => {
      if (document.hidden) {
        // Page became hidden (user switched tabs or minimized)
        isPageVisible = false;
        recordConnection('page_hidden');
      } else {
        // Page became visible again
        isPageVisible = true;
        lastActivityTime = Date.now();
        recordConnection('page_visible');
      }
    };

    // Track user activity
    const handleUserActivity = () => {
      if (isPageVisible) {
        lastActivityTime = Date.now();
      }
    };

    const handleBeforeUnload = () => {
      recordConnection('page_unload');
    };

    const recordConnection = async (eventType) => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_SERVER_URL || ''}/backend/user/record_connection`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ 
            user_id: user.user_id || user.sub,
            event_type: eventType,
            timestamp: new Date().toISOString()
          })
        });
        
        if (response.ok) {
          console.log(`User connection recorded: ${eventType}`);
        }
      } catch (error) {
        console.error('Failed to record user connection:', error);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('mousemove', handleUserActivity);
    document.addEventListener('keydown', handleUserActivity);
    document.addEventListener('click', handleUserActivity);
    document.addEventListener('scroll', handleUserActivity);
    window.addEventListener('beforeunload', handleBeforeUnload);

    const activityInterval = setInterval(() => {
      if (isPageVisible && Date.now() - lastActivityTime > ACTIVITY_TIMEOUT) {
        recordConnection('user_inactive');
      }
    }, 60000); // Check every minute

    recordConnection('page_load');

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('mousemove', handleUserActivity);
      document.removeEventListener('keydown', handleUserActivity);
      document.removeEventListener('click', handleUserActivity);
      document.removeEventListener('scroll', handleUserActivity);
      window.removeEventListener('beforeunload', handleBeforeUnload);
      clearInterval(activityInterval);
      
      recordConnection('component_unmount');
    };
  }, [user]);

  return null;  
};

export default UserConnectionTracker;
