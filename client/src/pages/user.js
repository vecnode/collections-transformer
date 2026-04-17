import Head from 'next/head'
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from "@/_contexts/AuthContext";




const User = () => {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  
  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/login');
    }
  }, [user, isLoading, router]);
  
  if (isLoading || !user) {
    return <div>Loading...</div>;
  }
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
    if (user) {
      getUserAccountInfo();
      getUserProfile();
    }
  }, [user]);

  const getUserAccountInfo = () => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/user/last_connection?" + new URLSearchParams({
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
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/user/profile?" + new URLSearchParams({
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
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/user/profile?" + params, requestOptions)
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
          <h1>User Profile</h1>
          <hr/>

          <div style={{
            width: '100%',
            margin: '2rem 0',
            lineHeight: '1.6',
            padding: '2rem',
            border: '1px solid black',
            borderRadius: '5px',
            backgroundColor: '#f5f5f5'
          }}>
            <div>
                <strong><u>Account Information</u></strong> <br></br>

            </div>
            
            
            <ul style={{ marginTop: '1rem', paddingLeft: '1.5rem' }}>
              <li><strong>Name:</strong> {user.name === user.email ? user.nickname : user.name}</li>
              <li><strong>Email:</strong> {user.email}</li>
              <li><strong>User ID:</strong> {user.sub}</li>
              <li><strong>Account Created:</strong> {accountInfo.firstConnection ? accountInfo.firstConnection.toLocaleDateString() : 'Unknown'}</li>
              <li><strong>Last Connection:</strong> {accountInfo.lastConnection ? accountInfo.lastConnection.toLocaleDateString() + ' ' + accountInfo.lastConnection.toLocaleTimeString() : 'Unknown'}</li>
              <li>
                <strong>Role:</strong> 
                {isEditing ? (
                  <input
                    type="text"
                    value={userProfile.role}
                    onChange={(e) => handleProfileChange('role', e.target.value)}
                    style={{
                      marginLeft: '10px',
                      padding: '2px 6px',
                      border: '1px solid #ccc',
                      borderRadius: '3px',
                      fontSize: 'inherit'
                    }}
                    placeholder="Enter your role"
                  />
                ) : (
                  <span style={{ marginLeft: '10px' }}>
                    {userProfile.role || 'Not specified'}
                  </span>
                )}
              </li>
              <li>
                <strong>Affiliation:</strong> 
                {isEditing ? (
                  <input
                    type="text"
                    value={userProfile.affiliation}
                    onChange={(e) => handleProfileChange('affiliation', e.target.value)}
                    style={{
                      marginLeft: '10px',
                      padding: '2px 6px',
                      border: '1px solid #ccc',
                      borderRadius: '3px',
                      fontSize: 'inherit'
                    }}
                    placeholder="Enter your affiliation"
                  />
                ) : (
                  <span style={{ marginLeft: '10px' }}>
                    {userProfile.affiliation || 'Not specified'}
                  </span>
                )}
              </li>
            </ul>
            
            <div style={{ marginTop: '1rem', textAlign: 'center' }}>
              {isEditing ? (
                <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
                  <button
                    onClick={handleSaveProfile}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: 'black',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setIsEditing(false)}
                    style={{
                      padding: '8px 16px',
                      backgroundColor: 'black',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setIsEditing(true)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px'
                  }}
                >
                  Edit Profile
                </button>
              )}
            </div>
          </div>







        </div>
      </main>
    </>
  )
}

export default User

