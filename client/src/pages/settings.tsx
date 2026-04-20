'use client'

import Head from 'next/head'
import React, { useState, useEffect } from 'react'
import { useAuth } from "@/contexts/AuthContext";
import { withAuth } from "@/components/withAuth";

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
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/user/preferences?" + new URLSearchParams({
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
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/user/preferences", requestOptions)
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
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/ollama/models", requestOptions)
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
        <div className="container settings-shell">
          <h1>Settings</h1>
          <hr/>
          
          <div className="settings-row">
            <span className="settings-label">LLM Provider:</span>
            <span>Ollama</span>
          </div>

          <div className="settings-row">
            <span className="settings-label">Ollama Backend:</span>
            <select
              value={ollamaBackend}
              onChange={(e) => setOllamaBackend(e.target.value)}
              disabled={loadingModels}
              className={`settings-input ${loadingModels ? 'is-disabled' : ''}`}
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

          <div className="settings-actions">
            {saveMessage && (
              <span className={`settings-message ${saveMessage.includes('successfully') ? 'is-success' : 'is-error'}`}>
                {saveMessage}
              </span>
            )}
            <button
              onClick={handleSavePreferences}
              disabled={saving}
              className={`settings-save-btn ${saving ? 'is-saving' : ''}`}
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
