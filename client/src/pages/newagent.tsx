import React, { useState } from 'react';

import { useAuth } from "@/contexts/AuthContext";
import { withAuth } from "@/components/withAuth";

const NewAgent = () => {
  const { user } = useAuth();

  const [aiName, setAiName] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskType, setTaskType] = useState('Text Detection (T/F)');

  // Create a new Agent
  const handleCreateClick = async (e) => {
    e.preventDefault();

    // Validate required fields
    if (!aiName.trim()) {
      alert('Please enter a name for your Agent');
      return;
    }
    if (!taskDescription.trim()) {
      alert('Please enter an agent description');
      return;
    }
    if (!taskType) {
      alert('Please select a task type');
      return;
    }
    const requestOptions = {
      method: 'POST',
      mode: 'cors',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: aiName,
        description: taskDescription,
        task_type: taskType,
        user_id: user.user_id || user.sub
      })
    };

    try {
      const response = await fetch(
        (process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/agent_new",
        requestOptions
      );

      const data = await response.json();
      if (response.ok && data.ok) {
        alert(data.message || 'Agent created successfully!');
        // Reset form
        setAiName('');
        setTaskDescription('');
        setTaskType('Text Detection (T/F)');
        return;
      }

      const errorMessage =
        data?.error?.message ||
        data?.message ||
        'Unknown error';

      alert('Error creating Agent: ' + errorMessage);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      alert('Error creating Agent: ' + errorMessage);
    }
  };

  return (
    <main>
      <div className="container">

        {/* Hero — full width, same as home */}
        <section className="home-hero">
          <p className="home-kicker">Ollama · Local Inference</p>
          <h1>Create Agent</h1>
          <p className="home-subtitle">
            Define an agent that runs a structured analysis task over a dataset using a local language model.
          </p>
        </section>

        <div className="agent-shell">

        {/* Identity card */}
        <section className="agent-card">
          <div className="agent-card-header">
            <span className="agent-card-icon material-symbols-outlined">psychology</span>
            <div>
              <h2 className="agent-card-title">Agent Identity</h2>
              <p className="agent-card-subtitle">Give the agent a clear name and the type of task it will perform.</p>
            </div>
          </div>

          <div className="agent-field">
            <label className="agent-label">Name</label>
            <input
              type="text"
              className="agent-input"
              value={aiName}
              onChange={(e) => setAiName(e.target.value)}
              placeholder="e.g. Abstract Art Detector"
            />
          </div>

          <div className="agent-field">
            <label className="agent-label">Task Type</label>
            <select
              className="agent-input agent-select"
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
            >
              <option value="Text Detection (T/F)">Text Detection (T/F)</option>
              <option value="Text Detection (text)">Text Detection (text)</option>
              <option value="Image Detection (T/F)">Image Detection (T/F)</option>
              <option value="Image Detection (text)">Image Detection (text)</option>
            </select>
            <p className="agent-hint">
              <strong>T/F</strong> tasks return a boolean decision. <strong>text</strong> tasks return a free-form answer.
            </p>
          </div>
        </section>

        {/* Objective card */}
        <section className="agent-card">
          <div className="agent-card-header">
            <span className="agent-card-icon material-symbols-outlined">target</span>
            <div>
              <h2 className="agent-card-title">Agent Objective</h2>
              <p className="agent-card-subtitle">Describe precisely what the agent should look for or decide.</p>
            </div>
          </div>

          <div className="agent-field">
            <label className="agent-label">Objective</label>
            <textarea
              className="agent-input agent-textarea"
              value={taskDescription}
              onChange={(e) => setTaskDescription(e.target.value)}
              placeholder="e.g. Analyse the image(s) for the presence of human figures. Return true if any human figure is visible."
            />
          </div>
        </section>

        {/* Submit row */}
        <section className="agent-submit-row">
          <button className="agent-submit-btn" onClick={handleCreateClick}>
            <span className="material-symbols-outlined">add_circle</span>
            Create Agent
          </button>
          <p className="agent-submit-note">
            The agent will be stored in your workspace and can be assigned to analysis runs from there.
          </p>
        </section>

        </div>{/* /agent-shell */}
      </div>

    </main>
  );
};

export default withAuth(NewAgent);
