'use client'

import Head from 'next/head'
import React, { useState, useEffect } from 'react'
import { useAuth } from "@/_contexts/AuthContext";
import { withAuth } from "@/_components/withAuth";

const Settings = () => {
  const { user, isLoading } = useAuth();
  const [ollamaBackend, setOllamaBackend] = useState('');
  const [ollamaModels, setOllamaModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  
  useEffect(() => {
    if (user) {
      fetchOllamaModels();
      fetchUserPreferences();
    }
  }, [user]);
  
  const fetchUserPreferences = () => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/user/preferences?" + new URLSearchParams({
      user_id: user.user_id || user.sub
    }), requestOptions)
      .then(response => response.json())
      .then(res => {
        if (res.status !== 200) {
          console.error('Failed to load preferences:', res.error);
        }
      })
      .catch(error => {
        console.error('Error fetching preferences:', error);
      });
  };
  
  const handleSavePreferences = () => {
    setSaving(true);
    setSaveMessage('');
    
    const requestOptions = {
      method: 'POST',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        user_id: user.user_id || user.sub,
        text_provider: 'ollama'
      })
    };
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/user/preferences", requestOptions)
      .then(response => response.json())
      .then(res => {
        if (res.status === 200) {
          setSaveMessage('Settings saved successfully!');
          setTimeout(() => setSaveMessage(''), 3000);
        } else {
          setSaveMessage(res.error || 'Failed to save settings');
        }
        setSaving(false);
      })
      .catch(error => {
        console.error('Error saving preferences:', error);
        setSaveMessage('Error saving settings');
        setSaving(false);
      });
  };

  const fetchOllamaModels = () => {
    setLoadingModels(true);
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/ollama/models", requestOptions)
      .then(response => response.json())
      .then(res => {
        console.log('Ollama models response:', res);
        if ((res.status === 200 || res.status === "200") && res.data && res.data.models) {
          const models = res.data.models;
          console.log('Setting models:', models);
          setOllamaModels(models);
          // Set default to first model if available, or empty string
          if (models.length > 0 && !ollamaBackend) {
            setOllamaBackend(models[0]);
          }
        } else {
          console.log('No models found or error in response:', res);
          setOllamaModels([]);
        }
        setLoadingModels(false);
      })
      .catch(error => {
        console.error('Error fetching Ollama models:', error);
        setOllamaModels([]);
        setLoadingModels(false);
      });
  };
  
  if (isLoading || !user) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <Head>
        <title>Settings - Collections Transformer</title>
      </Head>
      <main>
        <div className="container">
          <h1>Settings</h1>
          <hr/>
          
          <div style={{ border: '1px solid grey', borderRadius: '5px', padding: '10px', paddingLeft: '20px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 'bold' }}>LLM Provider:</span>
            <span>Ollama</span>
          </div>

          <div style={{ border: '1px solid grey', borderRadius: '5px', padding: '10px', paddingLeft: '20px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontWeight: 'bold' }}>Ollama Backend:</span>
            <select
              value={ollamaBackend}
              onChange={(e) => setOllamaBackend(e.target.value)}
              disabled={loadingModels}
              style={{
                border: '1px solid grey',
                borderRadius: '5px',
                padding: '8px 12px',
                minWidth: '200px',
                fontSize: '1rem',
                opacity: loadingModels ? 0.6 : 1
              }}
            >
              {loadingModels ? (
                <option value="">Loading models...</option>
              ) : ollamaModels.length > 0 ? (
                ollamaModels.map((model) => (
                  <option key={model} value={model}>{model}</option>
                ))
              ) : (
                <option value="">No models available</option>
              )}
            </select>
          </div>

          <div style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '10px' }}>
            {saveMessage && (
              <span style={{ color: saveMessage.includes('successfully') ? 'green' : 'red', fontSize: '0.9rem' }}>
                {saveMessage}
              </span>
            )}
            <button
              onClick={handleSavePreferences}
              disabled={saving}
              style={{
                border: '1px solid grey',
                borderRadius: '5px',
                padding: '8px 20px',
                fontSize: '1rem',
                backgroundColor: saving ? '#f5f5f5' : 'transparent',
                color: 'black',
                cursor: saving ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s ease',
                opacity: saving ? 0.6 : 1
              }}
              onMouseEnter={(e) => !saving && (e.target.style.backgroundColor = '#f5f5f5')}
              onMouseLeave={(e) => !saving && (e.target.style.backgroundColor = 'transparent')}
            >
              {saving ? 'Saving' : 'Save'}
            </button>
          </div>
        </div>
      </main>
    </>
  )
}

export default withAuth(Settings)
