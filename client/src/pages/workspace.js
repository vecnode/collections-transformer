import Head from 'next/head'
import React, {useEffect, useState} from 'react'

import AnalyserList from '../_components/analyserList'
import DatasetList from '../_components/datasetList'
import LabelsetsList from '../_components/labelsetsList'
import AgentList from '../_components/agentList'
import StatusBox from '@/_components/statusBox';
import AnalysisDetailsModal from '@/_components/analysisDetailsModal';
import { useAuth } from "@/_contexts/AuthContext";
import { withAuth } from "@/_components/withAuth";






const Workspace = () => {
    const { user } = useAuth();

    const title = "Workspace - Collections Transformer (TaNC UAL)"

    const [datasets, setDatasets] = useState([{id:"Loading...",name:" ",status:""}])
    const [analysers, setAnalysers] = useState([{id:"Loading...",name:" ",dataset_id:"",category_id:"",dataset_name:"",category_name:""}])
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
    const [showAnalyserDeleteModal, setShowAnalyserDeleteModal] = useState(false)
    const [analyserToDelete, setAnalyserToDelete] = useState(null)
    const [selectedItemsDetails, setSelectedItemsDetails] = useState([])
    const [showDatasetDeleteModal, setShowDatasetDeleteModal] = useState(false)
    const [datasetToDelete, setDatasetToDelete] = useState(null)
    const [showLabelsetDeleteModal, setShowLabelsetDeleteModal] = useState(false)
    const [labelsetToDelete, setLabelsetToDelete] = useState(null)
    const [showAgentDeleteModal, setShowAgentDeleteModal] = useState(false)
    const [agentToDelete, setAgentToDelete] = useState(null)
    const [showTasks, setShowTasks] = useState(false)
    const [showModels, setShowModels] = useState(false)
    const [showAgents, setShowAgents] = useState(false)
    const [showDatasets, setShowDatasets] = useState(false)
    const [showAnnotations, setShowAnnotations] = useState(false)

    useEffect(() => {
      getAnalysers()
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

    const getAnalysers = () => {
      const requestOptions = {
        method: 'GET',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
  
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/analysers?" + new URLSearchParams({
        user_id:user.user_id || user.sub,
        include_names:true // Returns names of dataset and categories not just IDs
      }), requestOptions)
      .then(
        response =>  response.json()
      ).then(
        res => {
          console.log(res)
          if (res.status == 200)
            setAnalysers(res.data)
        }
      )
    }

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

    const confirmDeleteAnalyser = (analyser) => {
      setAnalyserToDelete(analyser);
      setShowAnalyserDeleteModal(true);
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

    const executeDeleteAnalyser = () => {
      if (!analyserToDelete) return;
      
      setStatus("Deleting analyser...")
      const requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
      
      fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/classifier_delete?" + new URLSearchParams({
        analyser_id: analyserToDelete._id
      }), requestOptions)
      .then(response => response.json())
      .then(data => {
        setStatus("Analyser deleted")
        console.log(data)
        getAnalysers()
        setShowAnalyserDeleteModal(false)
        setAnalyserToDelete(null)
      })
      .catch(error => {
        console.error('Error deleting analyser:', error);
        setStatus("Error deleting analyser")
        setShowAnalyserDeleteModal(false)
        setAnalyserToDelete(null)
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
    
    return (
      <>
      <Head>
        <title>{title}</title>
      </Head>
        <main>
            <div className="container">
              <h1>Workspace</h1>
              <hr/>

              <h5>Username: {user.name === user.email ? user.nickname : user.name}</h5>
              {lastConnection && (
                <div style={{marginTop: "5px", fontSize: "0.9em", color: "#666"}}>
                  Last connection: {new Date(lastConnection).toLocaleTimeString('en-GB', {
                    day: '2-digit',
                    month: '2-digit',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                  })}
                </div>
              )}

              <br></br>

              <div style={{ border: '1px solid black', borderRadius: '5px', padding: '20px', marginBottom: '2rem' }}>
                <h3>Analytics</h3>

                <hr></hr>
                
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <h5 style={{ margin: 0 }}>Tasks</h5>
                  <button
                    onClick={() => setShowTasks(!showTasks)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: 'white',
                      color: 'black',
                      border: '1px solid black',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                  >
                    {showTasks ? 'Hide' : 'Show'}
                  </button>
                </div>
                {showTasks && (
                <div style={{ marginBottom: '2rem' }}>
                  <table id="analysis-history" className="table table-striped">
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
                      {analysisHistory.length > 0 ? (
                        analysisHistory.map((analysis) => {
                          const analysisDate = new Date(analysis.created_at);
                          const formattedDate = analysisDate.toLocaleDateString('en-GB', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          });
                          
                          return (
                            <tr key={analysis._id}>
                              <td>{formattedDate}</td>
                              <td>{analysis.analyser_name || 'Unknown'}</td>
                              <td>{analysis.dataset_name || 'Unknown'}</td>
                              <td>{analysis.status || 'Completed'}</td>
                              <td>
                                
                                <button 
                                  onClick={() => viewAnalysisDetails(analysis)}
                                  style={{
                                    padding: '4px 8px',
                                    backgroundColor: 'white',
                                    color: 'black',
                                    border: '1px solid black',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '12px',
                                    marginRight: '5px',
                                  }}
                                  onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                                  onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                                >
                                  View
                                </button>
                                <button 
                                  onClick={() => confirmDeleteAnalysis(analysis)}
                                  style={{
                                    padding: '4px 8px',
                                    backgroundColor: 'white',
                                    color: 'black',
                                    border: '1px solid black',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '12px',
                                  }}
                                  onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                                  onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                                >
                                  Delete
                                </button>
                                
                              </td>
                            </tr>
                          );
                        })
                      ) : (
                        <tr>
                          <td colSpan="5" style={{ textAlign: 'center', color: '#666' }}>
                            No saved analysis history yet. Save your first analysis from the Tasks page.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
                )}

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', marginTop: '20px' }}>
                  <h5 style={{ margin: 0 }}>Agents</h5>
                  <button
                    onClick={() => setShowAgents(!showAgents)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: 'white',
                      color: 'black',
                      border: '1px solid black',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                  >
                    {showAgents ? 'Hide' : 'Show'}
                  </button>
                </div>
                {showAgents && (
                <AgentList user_id={user.user_id || user.sub} agents={agents} onDeleteHandler={confirmDeleteAgent}/>
                )}
              </div>

              <div style={{ border: '1px solid black', borderRadius: '5px', padding: '20px', marginBottom: '2rem' }}>
                <h3>Media</h3>
                
                <hr></hr>
                
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <h5 style={{ margin: 0 }}>Datasets</h5>
                  <button
                    onClick={() => setShowDatasets(!showDatasets)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: 'white',
                      color: 'black',
                      border: '1px solid black',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                  >
                    {showDatasets ? 'Hide' : 'Show'}
                  </button>
                </div>
                {showDatasets && (
                <DatasetList user_id={user.user_id || user.sub} datasets={datasets} onDeleteHandler={confirmDeleteDataset}/>
                )}

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px', marginTop: '20px' }}>
                  <h5 style={{ margin: 0 }}>Annotations</h5>
                  <button
                    onClick={() => setShowAnnotations(!showAnnotations)}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: 'white',
                      color: 'black',
                      border: '1px solid black',
                      borderRadius: '5px',
                      cursor: 'pointer',
                      fontSize: '1rem'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = 'white'}
                  >
                    {showAnnotations ? 'Hide' : 'Show'}
                  </button>
                </div>
                {showAnnotations && (
                <LabelsetsList user={user} labelsets={labelsets} onDeleteHandler={confirmDeleteLabelset}/>
                )}
              </div>
              {status != "Unknown" ? (
                <StatusBox text={status}></StatusBox>
              ) : (<></>)}

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

        {/* Analyser Delete Confirmation Modal */}
        {showAnalyserDeleteModal && analyserToDelete && (
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
                onClick={() => setShowAnalyserDeleteModal(false)}
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
                Are you sure you want to delete the analyser "{analyserToDelete.name}"?
                {"\n\n"}Note: Any associated datasets and labelsets will NOT be removed.
              </div>

              <div style={{
                marginTop: '20px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <button 
                  onClick={executeDeleteAnalyser}
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
                  onClick={() => setShowAnalyserDeleteModal(false)}
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
                {"\n\n"}Note: Any analysers that use this annotation set may become unusable.
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
