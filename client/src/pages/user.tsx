import Head from 'next/head'
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from "@/contexts/AuthContext";




const User = () => {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const title = "User Profile - Collections Transformer (TaNC UAL)"

  const [accountInfo, setAccountInfo] = useState({
    firstConnection: null,
    lastConnection: null
  });
  const [userProfile, setUserProfile] = useState({
    role: '',
    affiliation: ''
  });
  const [isEditing, setIsEditing] = useState(false);
  
  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);

  useEffect(() => {
    if (user) {
      getUserAccountInfo();
      getUserProfile();
    }
  }, [user]);

  if (isLoading || !user) {
    return <div>Loading...</div>;
  }

  const displayName = user.name === user.email ? user.nickname : user.name

  const getUserAccountInfo = () => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/user/last_connection?" + new URLSearchParams({
      user_id: user.user_id || user.sub
    }), requestOptions)
    .then(response => response.json())
    .then(res => {
      if (res.status === "200") {
        setAccountInfo({
          firstConnection: res.data.first_connection ? new Date(res.data.first_connection) : null,
          lastConnection: res.data.last_connection ? new Date(res.data.last_connection) : null
        });
      }
    })
    .catch(error => {
      console.error('Error fetching user account info:', error);
    });
  };

  const getUserProfile = () => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/user/profile?" + new URLSearchParams({
      user_id: user.user_id || user.sub
    }), requestOptions)
    .then(response => response.json())
    .then(res => {
      if (res.status === "200") {
        setUserProfile({
          role: res.data.role || '',
          affiliation: res.data.affiliation || ''
        });
      }
    })
    .catch(error => {
      console.error('Error fetching user profile:', error);
    });
  };

  const handleProfileChange = (field, value) => {
    setUserProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSaveProfile = () => {
    const requestOptions = {
      method: 'POST',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    
    const params = new URLSearchParams({
      user_id: user.user_id || user.sub,
      role: userProfile.role,
      affiliation: userProfile.affiliation
    });
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/user/profile?" + params, requestOptions)
    .then(response => response.json())
    .then(res => {
      if (res.status === "200") {
        console.log("Profile saved successfully");
        setIsEditing(false);
      } else {
        console.error('Error saving profile:', res.error);
        alert('Error saving profile: ' + (res.error || 'Unknown error'));
      }
    })
    .catch(error => {
      console.error('Error saving profile:', error);
      alert('Error saving profile. Please try again.');
    });
  };

  return (
    <>
      <Head>
        <title>{title}</title>
      </Head>
      <main>
        <div className="container">
          <section className="home-hero">
            <p className="home-kicker">Account</p>
            <h1>User Profile</h1>
            <p className="home-subtitle">Manage your identity and profile details in a clean, focused workspace.</p>
          </section>

          <div className="agent-shell">
            <section className="agent-card">
              <div className="agent-card-header">
                <span className="agent-card-icon material-symbols-outlined">badge</span>
                <div>
                  <h2 className="agent-card-title">Account Information</h2>
                  <p className="agent-card-subtitle">Core account metadata sourced from your authenticated session.</p>
                </div>
              </div>

              <div className="agent-card-body">
                <div className="agent-field">
                  <label className="agent-label">Name</label>
                  <div className="agent-input">{displayName}</div>
                </div>

                <div className="agent-field">
                  <label className="agent-label">Email</label>
                  <div className="agent-input">{user.email}</div>
                </div>

                <div className="agent-field">
                  <label className="agent-label">User ID</label>
                  <div className="agent-input">{user.sub}</div>
                </div>

                <div className="agent-field">
                  <label className="agent-label">Account Created</label>
                  <div className="agent-input">{accountInfo.firstConnection ? accountInfo.firstConnection.toLocaleDateString() : 'Unknown'}</div>
                </div>

                <div className="agent-field">
                  <label className="agent-label">Last Connection</label>
                  <div className="agent-input">{accountInfo.lastConnection ? accountInfo.lastConnection.toLocaleDateString() + ' ' + accountInfo.lastConnection.toLocaleTimeString() : 'Unknown'}</div>
                </div>
              </div>
            </section>

            <section className="agent-card">
              <div className="agent-card-header">
                <span className="agent-card-icon material-symbols-outlined">edit_square</span>
                <div>
                  <h2 className="agent-card-title">Profile Details</h2>
                  <p className="agent-card-subtitle">Set the role and affiliation you want displayed in the platform.</p>
                </div>
              </div>

              <div className="agent-card-body">
                <div className="agent-field">
                  <label className="agent-label">Role</label>
                  {isEditing ? (
                    <input
                      type="text"
                      className="agent-input"
                      value={userProfile.role}
                      onChange={(e) => handleProfileChange('role', e.target.value)}
                      placeholder="Enter your role"
                    />
                  ) : (
                    <div className="agent-input">{userProfile.role || 'Not specified'}</div>
                  )}
                </div>

                <div className="agent-field">
                  <label className="agent-label">Affiliation</label>
                  {isEditing ? (
                    <input
                      type="text"
                      className="agent-input"
                      value={userProfile.affiliation}
                      onChange={(e) => handleProfileChange('affiliation', e.target.value)}
                      placeholder="Enter your affiliation"
                    />
                  ) : (
                    <div className="agent-input">{userProfile.affiliation || 'Not specified'}</div>
                  )}
                </div>

                <section className="agent-submit-row" style={{ marginTop: '0.5rem' }}>
                  {isEditing ? (
                    <>
                      <button className="agent-submit-btn" onClick={handleSaveProfile}>
                        <span className="material-symbols-outlined">save</span>
                        Save Profile
                      </button>
                      <button className="agent-submit-btn" onClick={() => setIsEditing(false)}>
                        <span className="material-symbols-outlined">close</span>
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button className="agent-submit-btn" onClick={() => setIsEditing(true)}>
                      <span className="material-symbols-outlined">edit</span>
                      Edit Profile
                    </button>
                  )}
                </section>
              </div>
            </section>
          </div>
        </div>
      </main>
    </>
  )
}

export default User

