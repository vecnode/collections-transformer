import Head from 'next/head'
import React, {useEffect, useState} from 'react'

import DatasetList from '../components/datasetList'
import LabelsetsList from '../components/labelsetsList'
import AgentList from '../components/agentList'
import StatusBox from '@/components/statusBox';
import AnalysisDetailsModal from '@/components/analysisDetailsModal';
import { useAuth } from "@/contexts/AuthContext";
import { withAuth } from "@/components/withAuth";






const Workspace = () => {
    const { user } = useAuth();

    const title = "Workspace - Collections Transformer (TaNC UAL)"

    const [datasets, setDatasets] = useState([{id:"Loading...",name:" ",status:""}])
    const [labelsets, setLabelsets] = useState([{id:"Loading...",name:" "}])
    const [agents, setAgents] = useState([{_id:"Loading...",name:" "}])
    const [analysisHistory, setAnalysisHistory] = useState([])
    const [status, setStatus] = useState("Unknown")
    const [lastConnection, setLastConnection] = useState(null)
    const [lastEventType, setLastEventType] = useState(null)
    const [lastEventTime, setLastEventTime] = useState(null)
    const [showAnalysisModal, setShowAnalysisModal] = useState(false)
    const [selectedAnalysis, setSelectedAnalysis] = useState(null)
    const [showDeleteModal, setShowDeleteModal] = useState(false)
    const [analysisToDelete, setAnalysisToDelete] = useState(null)
    const [selectedItemsDetails, setSelectedItemsDetails] = useState([])
    const [showDatasetDeleteModal, setShowDatasetDeleteModal] = useState(false)
    const [datasetToDelete, setDatasetToDelete] = useState(null)
    const [showLabelsetDeleteModal, setShowLabelsetDeleteModal] = useState(false)
    const [labelsetToDelete, setLabelsetToDelete] = useState(null)
    const [showAgentDeleteModal, setShowAgentDeleteModal] = useState(false)
    const [agentToDelete, setAgentToDelete] = useState(null)
    const [activeTab, setActiveTab] = useState('history')

    useEffect(() => {
      getDatasets()
      getLabelsets()
      getAgents()
      getAnalysisHistory()
      getLastConnection()
    },[])

    const getLastConnection = () => {
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
        if (res.status === "200" && res.data.last_connection) {
          const connectionDate = new Date(res.data.last_connection);
          setLastConnection(connectionDate);
          setLastEventType(res.data.last_event_type);
          setLastEventTime(res.data.last_event_time ? new Date(res.data.last_event_time) : null);
        }
      });
    };

    const getAgents = () => {
      const requestOptions = {
        method: 'GET',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
  
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/agents?" + new URLSearchParams({
        user_id:user.user_id || user.sub
      }), requestOptions)
      .then(
        response =>  response.json()
      ).then(
        res => {
          console.log('Agents response:', res)
          if (res.status == 200 || res.status == "200")
            setAgents(res.data || [])
        }
      )
    }

    const getDatasets = () => {
      const requestOptions = {
        method: 'GET',
        mode: 'cors',  
        headers: {'Content-Type': 'application/json'}
      };
  
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/datasets?" + new URLSearchParams({
        user_id:user.user_id || user.sub
      }), requestOptions)
      .then(
        response => response.json()
      ).then(
        res => {
          console.log(res)
          if (res.status == 200)
            setDatasets(res.data)
        }
      )
    }

    const getLabelsets = () => {
      console.log("getting labelsets")
      const requestOptions = {
        method: 'GET',
        mode: 'cors', 
        headers: {'Content-Type': 'application/json'}
      };
  
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/labelsets?" + new URLSearchParams({
        user_id:user.user_id || user.sub,
        includeCount:true,
        includeNames:true
      }), requestOptions)
      .then(
        response => response.json()
      ).then(
        res => {
          console.log(res)
          if (res.status == 200)
            setLabelsets(res.data)
        }
      )
    }

    const getAnalysisHistory = () => {
      const requestOptions = {
        method: 'GET',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
  
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/analysis/history?" + new URLSearchParams({
        user_id: user.user_id || user.sub
      }), requestOptions)
      .then(response => response.json())
      .then(res => {
        if (res.status === "200") {
          setAnalysisHistory(res.data);
        } else {
          console.error('Failed to fetch analysis history:', res.error);
        }
      })
      .catch(error => {
        console.error('Error fetching analysis history:', error);
      });
    };



    const confirmDeleteAnalysis = (analysis) => {
      setAnalysisToDelete(analysis);
      setShowDeleteModal(true);
    };

    const confirmDeleteDataset = (dataset) => {
      setDatasetToDelete(dataset);
      setShowDatasetDeleteModal(true);
    };

    const confirmDeleteLabelset = (labelset) => {
      setLabelsetToDelete(labelset);
      setShowLabelsetDeleteModal(true);
    };

    const confirmDeleteAgent = (agent) => {
      setAgentToDelete(agent);
      setShowAgentDeleteModal(true);
    };

    const executeDeleteAnalysis = () => {
      if (!analysisToDelete) return;
      
      setStatus("Deleting analysis...")
      const requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ analysis_id: analysisToDelete._id })
      };
      
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/analysis/delete", requestOptions)
      .then(response => response.json())
      .then(data => {
        setStatus("Analysis deleted")
        console.log(data)
        getAnalysisHistory()
        setShowDeleteModal(false)
        setAnalysisToDelete(null)
      })
      .catch(error => {
        console.error('Error deleting analysis:', error);
        setStatus("Error deleting analysis")
        setShowDeleteModal(false)
        setAnalysisToDelete(null)
      });
    };

    const executeDeleteDataset = () => {
      if (!datasetToDelete) return;
      
      setStatus("Deleting dataset (this can take a few minutes)...")
      const requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
      
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/dataset_delete?" + new URLSearchParams({
        dataset_id: datasetToDelete._id
      }), requestOptions)
      .then(response => response.json())
      .then(data => {
        setStatus("Dataset deleted")
        console.log(data)
        getDatasets()
        setShowDatasetDeleteModal(false)
        setDatasetToDelete(null)
      })
      .catch(error => {
        console.error('Error deleting dataset:', error);
        setStatus("Error deleting dataset")
        setShowDatasetDeleteModal(false)
        setDatasetToDelete(null)
      });
    };

    const executeDeleteLabelset = () => {
      if (!labelsetToDelete) return;
      
      setStatus("Deleting labelset...")
      const requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
      
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/labelset_delete?" + new URLSearchParams({
        labelset_id: labelsetToDelete._id
      }), requestOptions)
      .then(response => response.json())
      .then(data => {
        setStatus("Labelset deleted")
        console.log(data)
        getLabelsets()
        setShowLabelsetDeleteModal(false)
        setLabelsetToDelete(null)
      })
      .catch(error => {
        console.error('Error deleting labelset:', error);
        setStatus("Error deleting labelset")
        setShowLabelsetDeleteModal(false)
        setLabelsetToDelete(null)
      });
    };

    const executeDeleteAgent = () => {
      if (!agentToDelete) return;
      
      setStatus("Deleting agent...")
      const requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ agent_id: agentToDelete._id })
      };
      
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/agent_delete", requestOptions)
      .then(response => response.json())
      .then(data => {
        setStatus("Agent deleted")
        console.log(data)
        getAgents()
        setShowAgentDeleteModal(false)
        setAgentToDelete(null)
      })
      .catch(error => {
        console.error('Error deleting agent:', error);
        setStatus("Error deleting agent")
        setShowAgentDeleteModal(false)
        setAgentToDelete(null)
      });
    };

    const getItemDetails = async (itemIds) => {
      if (!itemIds || itemIds.length === 0) return;
      
      try {
        const requestOptions = {
          method: 'GET',
          mode: 'cors',
          headers: {'Content-Type': 'application/json'}
        };
        
        // Fetch items individually for instant loading
        const details = await Promise.all(
          itemIds.map(async (itemId) => {
            try {
              console.log(`Fetching item with ID: ${itemId}`);
              const response = await fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/item?" + new URLSearchParams({
                item_id: itemId
              }), requestOptions);
              
              if (!response.ok) {
                console.error(`HTTP error for item ${itemId}: ${response.status}`);
                return null;
              }
              
              const data = await response.json();
              console.log(`Response for item ${itemId}:`, data);
              
              if (data.status === "200" && data.data) {
                return data.data;
              } else {
                console.error(`API error for item ${itemId}:`, data.error || 'Unknown error');
                return null;
              }
            } catch (error) {
              console.error(`Error fetching item ${itemId}:`, error);
              return null;
            }
          })
        );
        
        const validDetails = details.filter(item => item !== null);
        console.log('Valid item details:', validDetails);
        setSelectedItemsDetails(validDetails);
      } catch (error) {
        console.error('Error fetching item details:', error);
      }
    };

    const viewAnalysisDetails = (analysis) => {
      setSelectedAnalysis(analysis);
      setShowAnalysisModal(true);
      if (analysis.selected_items && analysis.selected_items.length > 0) {
        getItemDetails(analysis.selected_items);
      }
    };
    
    const displayName = user.name === user.email ? user.nickname : user.name;
    const hasAgentLoadingPlaceholder = agents.some(agent => agent && agent._id === 'Loading...');
    const realAgentsCount = agents.filter(agent => agent && agent._id && agent._id !== 'Loading...').length;
    const hasDatasetLoadingPlaceholder = datasets.some(dataset => dataset && dataset.id === 'Loading...');
    const realDatasetsCount = datasets.filter(dataset => dataset && dataset.id !== 'Loading...').length;
    const hasLabelsetLoadingPlaceholder = labelsets.some(labelset => labelset && labelset.id === 'Loading...');
    const realLabelsetsCount = labelsets.filter(labelset => labelset && labelset.id !== 'Loading...').length;

    return (
      <>
      <Head>
        <title>{title}</title>
      </Head>

        <main className="ws-main">
          <div className="container ws-shell">

            <section className="home-hero">
              <span className="home-kicker">Operations Dashboard</span>
              <h1 className="home-title">Workspace</h1>
              <p className="home-subtitle">
                Signed in as <strong>{displayName}</strong>
                {lastConnection && (
                  <> &mdash; last active {new Date(lastConnection).toLocaleString('en-GB', {
                    day: '2-digit', month: '2-digit', year: 'numeric',
                    hour: '2-digit', minute: '2-digit', hour12: false
                  })}</>
                )}
              </p>
            </section>

            {/* Stat strip */}
            <div className="ws-stat-strip" style={{ animationDelay: '60ms' }}>
              <div className="ws-stat">
                <span className="ws-stat-value">{analysisHistory.length}</span>
                <span className="ws-stat-label">Analysis runs</span>
              </div>
              <div className="ws-stat">
                <span className="ws-stat-value">{agents.length}</span>
                <span className="ws-stat-label">Agents</span>
              </div>
              <div className="ws-stat">
                <span className="ws-stat-value">{datasets.length}</span>
                <span className="ws-stat-label">Datasets</span>
              </div>
              <div className="ws-stat">
                <span className="ws-stat-value">{labelsets.length}</span>
                <span className="ws-stat-label">Annotations</span>
              </div>
            </div>

            {/* Tab bar */}
            <div className="ws-tabs">
              {[
                { id: 'history',     icon: 'task_alt',    label: 'Analysis History',  sub: 'Saved runs from the Tasks page' },
                { id: 'agents',      icon: 'smart_toy',   label: 'Agents',            sub: 'Ollama model configurations' },
                { id: 'datasets',    icon: 'folder_open', label: 'Datasets',          sub: 'Uploaded media collections' },
                { id: 'annotations', icon: 'label',       label: 'Annotations',       sub: 'Label schemas and category sets' },
              ].map(tab => (
                <button
                  key={tab.id}
                  className={`ws-tab${activeTab === tab.id ? ' ws-tab--active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  <span className="material-symbols-outlined ws-tab-icon">{tab.icon}</span>
                  <span className="ws-tab-label">{tab.label}</span>
                  <span className="ws-tab-sub">{tab.sub}</span>
                </button>
              ))}
            </div>

            {/* Tab panel */}
            <div className="agent-card ws-panel-card">
              <div className="agent-card-body ws-panel-body">
                {activeTab === 'history' && (
                  analysisHistory.length === 0 ? (
                    <div className="ws-empty">No saved analysis history yet. Save your first analysis from the Tasks page.</div>
                  ) : (
                    <div className="ws-table-wrap">
                      <table className="ws-table">
                        <thead>
                          <tr>
                            <th>Date</th>
                            <th>Task</th>
                            <th>Dataset</th>
                            <th>Status</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {analysisHistory.map((analysis) => {
                            const formattedDate = new Date(analysis.created_at).toLocaleDateString('en-GB', {
                              day: '2-digit', month: '2-digit', year: 'numeric',
                              hour: '2-digit', minute: '2-digit'
                            });
                            return (
                              <tr key={analysis._id}>
                                <td>{formattedDate}</td>
                                <td>{analysis.agent_name || analysis.analyser_name || 'Unknown'}</td>
                                <td>{analysis.dataset_name || 'Unknown'}</td>
                                <td>
                                  <span className={`ws-badge ws-badge--${(analysis.status || 'completed').toLowerCase()}`}>
                                    {analysis.status || 'Completed'}
                                  </span>
                                </td>
                                <td>
                                  <div className="ws-action-row">
                                    <button className="ws-btn ws-btn--ghost" onClick={() => viewAnalysisDetails(analysis)}>View</button>
                                    <button className="ws-btn ws-btn--danger" onClick={() => confirmDeleteAnalysis(analysis)}>Delete</button>
                                  </div>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )
                )}
                {activeTab === 'agents' && (
                  <div className="ws-list-body">
                    {!hasAgentLoadingPlaceholder && realAgentsCount === 0 ? (
                      <div className="ws-empty">No agents yet. Create your first agent from the New Agent page.</div>
                    ) : (
                      <AgentList user_id={user.user_id || user.sub} agents={agents} onDeleteHandler={confirmDeleteAgent}/>
                    )}
                  </div>
                )}
                {activeTab === 'datasets' && (
                  <div className="ws-list-body">
                    {!hasDatasetLoadingPlaceholder && realDatasetsCount === 0 ? (
                      <div className="ws-empty">No datasets yet. Upload your first dataset to get started.</div>
                    ) : (
                      <DatasetList user_id={user.user_id || user.sub} datasets={datasets} onDeleteHandler={confirmDeleteDataset}/>
                    )}
                  </div>
                )}
                {activeTab === 'annotations' && (
                  <div className="ws-list-body">
                    {!hasLabelsetLoadingPlaceholder && realLabelsetsCount === 0 ? (
                      <div className="ws-empty">No annotation sets yet. Create a label schema to begin annotating.</div>
                    ) : (
                      <LabelsetsList user={user} labelsets={labelsets} onDeleteHandler={confirmDeleteLabelset}/>
                    )}
                  </div>
                )}
              </div>
            </div>

            {status !== 'Unknown' && (
              <div style={{ marginTop: '1rem' }}>
                <StatusBox text={status} />
              </div>
            )}

          </div>
        </main>

        {/* Analysis Details Modal */}
        {showAnalysisModal && selectedAnalysis && (
          <AnalysisDetailsModal
            showModal={showAnalysisModal}
            selectedAnalysis={selectedAnalysis}
            selectedItemsDetails={selectedItemsDetails}
            onClose={() => setShowAnalysisModal(false)}
          />
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && analysisToDelete && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999
          }}>
            <div style={{
              maxWidth: '60vw',
              maxHeight: '90vh',
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              <button 
                onClick={() => setShowDeleteModal(false)}
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '15px',
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666',
                  zIndex: 10000
                }}
              >
                ×
              </button>
              
              <h3 style={{ marginBottom: '1rem', marginRight: '2rem' }}>Confirm Deletion</h3>
              
              <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '1rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                border: '1px solid #dee2e6',
                fontSize: '0.9rem',
                lineHeight: '1.4',
                whiteSpace: 'pre-wrap'
              }}>
                Are you sure you want to delete this analysis?
              </div>

              <div style={{
                marginTop: '20px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <button 
                  onClick={executeDeleteAnalysis}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Delete
                </button>
                <button 
                  onClick={() => setShowDeleteModal(false)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Dataset Delete Confirmation Modal */}
        {showDatasetDeleteModal && datasetToDelete && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999
          }}>
            <div style={{
              maxWidth: '60vw',
              maxHeight: '90vh',
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              <button 
                onClick={() => setShowDatasetDeleteModal(false)}
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '15px',
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666',
                  zIndex: 10000
                }}
              >
                ×
              </button>
              
              <h3 style={{ marginBottom: '1rem', marginRight: '2rem' }}>Confirm Deletion</h3>
              
              <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '1rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                border: '1px solid #dee2e6',
                fontSize: '0.9rem',
                lineHeight: '1.4',
                whiteSpace: 'pre-wrap'
              }}>
                Are you sure you want to delete the dataset "{datasetToDelete.name}"?
                {"\n\n"}Note: Any associated labelsets will also be removed.
              </div>

              <div style={{
                marginTop: '20px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <button 
                  onClick={executeDeleteDataset}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Delete
                </button>
                <button 
                  onClick={() => setShowDatasetDeleteModal(false)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Labelset Delete Confirmation Modal */}
        {showLabelsetDeleteModal && labelsetToDelete && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999
          }}>
            <div style={{
              maxWidth: '60vw',
              maxHeight: '90vh',
              backgroundColor: 'white',
              borderRadius: '8px',
              padding: '20px',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}>
              <button 
                onClick={() => setShowLabelsetDeleteModal(false)}
                style={{
                  position: 'absolute',
                  top: '10px',
                  right: '15px',
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#666',
                  zIndex: 10000
                }}
              >
                ×
              </button>
              
              <h3 style={{ marginBottom: '1rem', marginRight: '2rem' }}>Confirm Deletion</h3>
              
              <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '1rem',
                backgroundColor: '#f8f9fa',
                borderRadius: '4px',
                border: '1px solid #dee2e6',
                fontSize: '0.9rem',
                lineHeight: '1.4',
                whiteSpace: 'pre-wrap'
              }}>
                Are you sure you want to delete the annotation set"{labelsetToDelete.name}"?
                {"\n\n"}Note: Any agents that use this annotation set may become unusable.
              </div>

              <div style={{
                marginTop: '20px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <button 
                  onClick={executeDeleteLabelset}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Delete
                </button>
                <button 
                  onClick={() => setShowLabelsetDeleteModal(false)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Agent Delete Confirmation Modal */}
        {showAgentDeleteModal && agentToDelete && (
          <div style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
          }}>
            <div style={{
              backgroundColor: 'white',
              padding: '20px',
              borderRadius: '8px',
              maxWidth: '400px',
              width: '90%'
            }}>
              <h3>Delete Agent</h3>
              <p>Are you sure you want to delete the agent "{agentToDelete.name}"? This action cannot be undone.</p>
              <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px' }}>
                <button 
                  onClick={executeDeleteAgent}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Delete
                </button>
                <button 
                  onClick={() => setShowAgentDeleteModal(false)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: 'black',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </>
  )
}

export default withAuth(Workspace)
