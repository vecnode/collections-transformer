// @ts-nocheck
import React, { useEffect, useState, useRef, useLayoutEffect } from 'react';
import DatasetModal from '../components/datasetModal';

import { useAuth } from "@/contexts/AuthContext";
import { withAuth } from "@/components/withAuth";

const RadioList = ({ items, name, selectedId, onChange, getLabel }) => (
  <div>
    {items.map(item => (
      <label
        key={item._id || item.id}
        style={{
          display: 'block',
          marginBottom: '0px',
          fontSize: 'small'
        }}
      >
        <input
          type="radio"
          name={name}
          value={item._id || item.id}
          checked={selectedId === (item._id || item.id)}
          onChange={() => onChange(item._id || item.id)}
        />
        <span style={{ marginLeft: '3px' }}>{getLabel(item)}</span>
      </label>
    ))}
  </div>
)

// Custom Image Thumbnail Component for Table
const ImageThumbnail = ({ itemId, imageStorageId }) => {
  const [loadState, setLoadState] = useState("unknown");
  const [image, setImage] = useState("");
  const [showModal, setShowModal] = useState(false);

  const getImage = async (imgStorageId) => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'},
    };

    setLoadState("loading");

    try {
      const response = await fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/item_image?" + new URLSearchParams({
        item_id: itemId,
        image_storage_id: imgStorageId
      }), requestOptions);
      
      const res = await response.json();
      if (res.status === "200") {
        setImage("data:image/jpeg;base64," + res.data);
        setLoadState("ready");
      } else {
        console.log(res['error']);
        setLoadState("error");
      }
    } catch (error) {
      console.error('Error loading image:', error);
      setLoadState("error");
    }
  };

  useEffect(() => {
    getImage(imageStorageId);
  }, [imageStorageId]);

  const handleImageClick = () => {
    if (loadState === "ready") {
      setShowModal(true);
    }
  };

  return (
    <>
      <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {loadState !== "ready" ? (
          <div className="image-placeholder">
            <div>
              <span className="spinner-border text-primary" role="status" style={{ width: '0.75rem', height: '0.75rem' }}></span>
            </div>
          </div>
        ) : (
          <img 
            className="item-image-thumbnail" 
            src={image} 
            onClick={handleImageClick}
            alt="Thumbnail"
          />
        )}
      </div>

      {/* Image Modal */}
      {showModal && (
        <div className="modal-overlay" style={{
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
          <div className="modal-content" style={{
            maxWidth: '90vw',
            maxHeight: '70vh',
            backgroundColor: 'white',
            borderRadius: '8px',
            padding: '20px',
            position: 'relative',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <button 
              onClick={() => setShowModal(false)}
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
            <img 
              src={image} 
              style={{
                maxWidth: 'calc(90vw - 40px)',
                maxHeight: 'calc(70vh - 40px)',
                width: 'auto',
                height: 'auto',
                objectFit: 'contain',
                display: 'block'
              }}
              alt="Full size"
            />
          </div>
        </div>
      )}
    </>
  );
};

// Text Modal Component
const TextModal = ({ text, onClose }) => {
  return (
    <div className="modal-overlay" style={{
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
      <div className="modal-content" style={{
        maxWidth: '70vw',
        maxHeight: '70vh',
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '20px',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <button 
          onClick={onClose}
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
        <h5 style={{ marginBottom: '1rem', marginRight: '2rem' }}>Text Content</h5>
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px',
          border: '1px solid #dee2e6',
          whiteSpace: 'pre-wrap',
          lineHeight: '1.6',
          fontSize: '0.95rem'
        }}>
          {text}
        </div>
      </div>
    </div>
  );
};

// Selected Items Display Component
const SelectedItemsDisplay = ({ selectedItems, datasetData, onClearAll }) => {
  const [showTextModal, setShowTextModal] = useState(false);
  const [selectedText, setSelectedText] = useState("");

  if (!selectedItems || selectedItems.size === 0 || !datasetData || !datasetData.artworks) {
    return null;
  }

  const getTextContent = (item) => {
    if (item.content) {
      const textContent = item.content.find(c => c.content_type === 'text');
      return textContent ? textContent.content_value.text : 'No text content';
    }
    return 'No content';
  };

  const getImageContent = (item) => {
    if (item.content) {
      const imageContent = item.content.find(c => c.content_type === 'image');
      return imageContent ? imageContent.content_value.image_storage_id : null;
    }
    return null;
  };

  const selectedItemsData = datasetData.artworks.filter(item => selectedItems.has(item._id));

  // Group items by their base ID for multimodal numbering
  const groupedItems = [];
  const processedIds = new Set();

  selectedItemsData.forEach((item, index) => {
    if (processedIds.has(item._id)) return;
    
    const hasImage = getImageContent(item);
    const hasText = getTextContent(item) !== 'No text content';
    
    if (hasImage && hasText) {
      // This is a multimodal item - group image and text together
      groupedItems.push({
        id: item._id,
        type: 'multimodal',
        imageStorageId: hasImage,
        textContent: getTextContent(item),
        baseNumber: index + 1
      });
      processedIds.add(item._id);
    } else if (hasImage) {
      // Image only
      groupedItems.push({
        id: item._id,
        type: 'image',
        imageStorageId: hasImage,
        textContent: null,
        baseNumber: index + 1
      });
      processedIds.add(item._id);
    } else if (hasText) {
      // Text only
      groupedItems.push({
        id: item._id,
        type: 'text',
        imageStorageId: null,
        textContent: getTextContent(item),
        baseNumber: index + 1
      });
      processedIds.add(item._id);
    }
  });

  const handleTextClick = (text) => {
    setSelectedText(text);
    setShowTextModal(true);
  };

  return (
    <>
      <div style={{
        marginTop: '1rem',
        padding: '0.75rem',
        backgroundColor: 'rgb(236, 236, 236)',
        borderRadius: '6px',
        border: '1px solid rgb(185, 185, 185)' 
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <strong>Selected Items: {selectedItems.size}</strong>
          <button 
            className="btn btn-sm btn-outline-secondary" 
            onClick={onClearAll}
          >
            Clear All
          </button>
        </div>
        <small style={{ color: '#666', display: 'block', marginBottom: '0.75rem' }}>
          {selectedItems.size} of {datasetData.artworks.length} items selected
        </small>
        
        <div 
          className="selected-items-container"
          style={{ 
            maxHeight: '200px', 
            overflowY: 'auto', 
            border: '1px solid #dee2e6', 
            borderRadius: '4px',
            backgroundColor: 'white',
            padding: '0.5rem',
            fontFamily: 'var(--bs-font-sans-serif)'
          }}
        >
          {groupedItems.map((item, index) => (
            <div key={item.id}>
              {item.type === 'multimodal' ? (
                // Multimodal item - show image and text separately
                <>
                  <div 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      padding: '0.5rem', 
                      borderBottom: '1px solid #f0f0f0',
                      gap: '0.75rem',
                      height: '50px',
                      maxHeight: '50px',
                      overflow: 'hidden'
                    }}
                  >
                    <span style={{ 
                      fontSize: '0.8rem', 
                      color: '#666', 
                      minWidth: '30px' 
                    }}>
                      {item.baseNumber}.
                    </span>
                    <div style={{ width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <ImageThumbnail itemId={item.id} imageStorageId={item.imageStorageId} />
                    </div>
                    <div style={{ 
                      flex: 1, 
                      fontSize: '0.9rem',
                      color: '#333',
                      lineHeight: '1.2',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      [Image]
                    </div>
                  </div>
                  <div 
                    style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      padding: '0.5rem', 
                      borderBottom: index < groupedItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                      gap: '0.75rem',
                      height: '50px',
                      maxHeight: '50px',
                      overflow: 'hidden',
                      cursor: 'pointer'
                    }}
                    onClick={() => handleTextClick(item.textContent)}
                  >
                    <span style={{ 
                      fontSize: '0.8rem', 
                      color: '#666', 
                      minWidth: '30px' 
                    }}>
                      {item.baseNumber}.1
                    </span>
                    <div style={{ 
                      flex: 1, 
                      fontSize: '0.9rem',
                      color: '#333',
                      lineHeight: '1.2',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {item.textContent.length > 100 
                        ? item.textContent.substring(0, 100) + '...' 
                        : item.textContent
                      }
                    </div>
                  </div>
                </>
              ) : (
                // Single modality item
                <div 
                  style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    padding: '0.5rem', 
                    borderBottom: index < groupedItems.length - 1 ? '1px solid #f0f0f0' : 'none',
                    gap: '0.75rem',
                    height: '50px',
                    maxHeight: '50px',
                    overflow: 'hidden',
                    cursor: item.type === 'text' ? 'pointer' : 'default'
                  }}
                  onClick={item.type === 'text' ? () => handleTextClick(item.textContent) : undefined}
                >
                  <span style={{ 
                    fontSize: '0.8rem', 
                    color: '#666', 
                    minWidth: '30px' 
                  }}>
                    {item.baseNumber}.
                  </span>
                  
                  {item.type === 'image' ? (
                    <div style={{ width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <ImageThumbnail itemId={item.id} imageStorageId={item.imageStorageId} />
                    </div>
                  ) : (
                    <div style={{ 
                      flex: 1, 
                      fontSize: '0.9rem',
                      color: '#333',
                      lineHeight: '1.2',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {item.textContent.length > 100 
                        ? item.textContent.substring(0, 100) + '...' 
                        : item.textContent
                      }
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Text Modal */}
      {showTextModal && (
        <TextModal 
          text={selectedText} 
          onClose={() => setShowTextModal(false)} 
        />
      )}
    </>
  );
};

const Tasks = () => {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [analysers, setAnalysers] = useState([]);
  const [agents, setAgents] = useState([]);
  const [selectedAnalyser, setSelectedAnalyser] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [selectedButtonType, setSelectedButtonType] = useState('boolean'); // Default to first option
  const [selectedDatasetData, setSelectedDatasetData] = useState(null);
  const [loadingDataset, setLoadingDataset] = useState(false);
  const [selectedItems, setSelectedItems] = useState(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [analysisResult, setAnalysisResult] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [chatMessages, setChatMessages] = useState([]); // New state for chat messages
  const [maxSentences, setMaxSentences] = useState(3); // New state for sentence limit
  const [taskType, setTaskType] = useState(null); // 'human', 'ai', or null
  const [serviceProvider, setServiceProvider] = useState('Ollama');
  // Task is now determined by the selected agent's task_type
  const scrollPositionRef = useRef({ container: null, position: 0 });

  // Get selected items for display
  const getSelectedAnalyser = () => {
    return analysers.find(a => a._id === selectedAnalyser) || null;
  };

  const getSelectedDataset = () => {
    return datasets.find(d => d._id === selectedDataset) || null;
  };

  // Handle item selection
  const handleItemSelection = (itemId, event) => {
    // Prevent default behavior to avoid auto-scrolling
    event.preventDefault();
    event.stopPropagation();
    
    // Save scroll position before state update
    const scrollContainer = event.target.closest('.table-responsive');
    if (scrollContainer) {
      scrollPositionRef.current = {
        container: scrollContainer,
        position: scrollContainer.scrollTop
      };
    }
    
    const newSelectedItems = new Set(selectedItems);
    if (newSelectedItems.has(itemId)) {
      newSelectedItems.delete(itemId);
    } else {
      newSelectedItems.add(itemId);
    }
    setSelectedItems(newSelectedItems);
  };

  // Restore scroll position after state updates
  useLayoutEffect(() => {
    if (scrollPositionRef.current.container) {
      scrollPositionRef.current.container.scrollTop = scrollPositionRef.current.position;
    }
  }, [selectedItems]);

  // Select all items on current page
  const handleSelectAllCurrentPage = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    // Save scroll position before state update
    const scrollContainer = event.target.closest('.table-responsive');
    if (scrollContainer) {
      scrollPositionRef.current = {
        container: scrollContainer,
        position: scrollContainer.scrollTop
      };
    }
    
    if (selectedDatasetData && selectedDatasetData.artworks) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      const currentItems = selectedDatasetData.artworks.slice(startIndex, endIndex);
      const currentItemIds = currentItems.map(item => item._id);
      
      const newSelectedItems = new Set(selectedItems);
      currentItemIds.forEach(id => newSelectedItems.add(id));
      setSelectedItems(newSelectedItems);
    }
  };

  // Deselect all items on current page
  const handleDeselectAllCurrentPage = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    // Save scroll position before state update
    const scrollContainer = event.target.closest('.table-responsive');
    if (scrollContainer) {
      scrollPositionRef.current = {
        container: scrollContainer,
        position: scrollContainer.scrollTop
      };
    }
    
    if (selectedDatasetData && selectedDatasetData.artworks) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      const currentItems = selectedDatasetData.artworks.slice(startIndex, endIndex);
      const currentItemIds = currentItems.map(item => item._id);
      
      const newSelectedItems = new Set(selectedItems);
      currentItemIds.forEach(id => newSelectedItems.delete(id));
      setSelectedItems(newSelectedItems);
    }
  };

  // Select all items in entire dataset
  const handleSelectAll = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (selectedDatasetData && selectedDatasetData.artworks) {
      const allItemIds = selectedDatasetData.artworks.map(item => item._id);
      setSelectedItems(new Set(allItemIds));
    }
  };

  // Deselect all items in entire dataset
  const handleDeselectAll = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    setSelectedItems(new Set());
  };
  
  // Fetch dataset data when selected dataset changes
  const fetchDatasetData = async (datasetId) => {
    console.log("fetchDatasetData called with datasetId:", datasetId);
    
    if (!datasetId) {
      console.log("No datasetId provided, clearing data");
      setSelectedDatasetData(null);
      return;
    }

    setLoadingDataset(true);
    try {
      const requestOptions = {
        method: 'GET',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
      

      const url = (process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/dataset?" + new URLSearchParams({
        dataset_id: datasetId,
        include_items: true
      });
      
      console.log("Fetching dataset from URL:", url);
      
      const response = await fetch(url, requestOptions);
      console.log("Response status:", response.status);
      
      const res = await response.json();
      console.log("Response data:", res);
      
      if (res.status === 200 || res.status === '200') {
        console.log("Dataset data loaded successfully:", res.data);
        setSelectedDatasetData(res.data);
      } else {
        console.error('Failed to fetch dataset:', res.error);
        setSelectedDatasetData(null);
      }
    } catch (error) {
      console.error('Error fetching dataset:', error);
      setSelectedDatasetData(null);
    } finally {
      setLoadingDataset(false);
    }
  };

  useEffect(() => {
    if (user) {
      getAnalysers();
      getAgents();
      getDatasets();
    }
  }, [user]);
  
  // When analysers are loaded, select the last one by default
  useEffect(() => {
    if (analysers.length > 0 && !analysers.some(a => a._id === selectedAnalyser)) {
      setSelectedAnalyser(analysers[analysers.length - 1]._id);
    }
  }, [analysers, selectedAnalyser]);

  // When datasets are loaded, select the last one by default
  useEffect(() => {
    console.log("Datasets loaded:", datasets);
    console.log("Current selectedDataset:", selectedDataset);
    
    if (datasets.length > 0 && !datasets.some(d => d._id === selectedDataset)) {
      const newSelection = datasets[datasets.length - 1]._id;
      console.log("Setting default dataset selection to:", newSelection);
      setSelectedDataset(newSelection);
    }
  }, [datasets, selectedDataset]);

  // Fetch dataset data when selected dataset changes
  useEffect(() => {
    console.log("Selected dataset changed to:", selectedDataset);
    fetchDatasetData(selectedDataset);
  }, [selectedDataset]);



  const getAnalysers = () => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/analysers?" + new URLSearchParams({
      user_id:user.user_id || user.sub,
      include_names:true
    }), requestOptions)
    .then(response => response.json())
    .then(res => {
      if (res.status == 200)
        setAnalysers(res.data)
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
    .then(response => response.json())
    .then(res => {
      console.log('Agents response in tasks:', res);
      if (res.status == 200 || res.status == "200")
        setAgents(res.data || [])
    });
  };

  const getDatasets = () => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/datasets?" + new URLSearchParams({
      user_id:user.user_id || user.sub
    }), requestOptions)
    .then(response => response.json())
    .then(res => {
      if (res.status == 200)
        setDatasets(res.data)
    });
  };

  const handleSelectDataElements = () => {
    // This will be handled by the modal
    console.log("Select data elements clicked");
  };

  // Analyze selected items
  const handleAnalyzeClick = async (e) => {
    e.preventDefault();

    setIsAnalyzing(true);
    const newMessageId = Date.now();
    
    // Detect execution mode: Agent Task + Ollama
    const isAgentTask = taskType === 'ai';
    const isOllama = serviceProvider === 'Ollama';
    const useAgentExecution = isAgentTask && isOllama && selectedAgent && selectedDataset && selectedItems.size > 0;
    
    // Add initial analysis message
    const analysisMessage = {
      id: newMessageId,
      type: 'analysis',
      content: useAgentExecution 
        ? "$ Starting agent analysis with Ollama...\n"
        : "$ Starting test analysis...\n",
      timestamp: new Date()
    };
    
    setChatMessages(prev => [...prev, analysisMessage]);

    let requestOptions;
    let endpoint;

    if (useAgentExecution) {
      // Get task from selected agent's task_type
      const selectedAgentData = agents.find(a => a._id === selectedAgent);
      const agentTask = selectedAgentData?.task_type || 'Text Detection (T/F)';
      
      // Agent Task with Ollama - use new endpoint
      endpoint = "/backend/agent_execute_with_images";
      requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user_id: user.user_id || user.sub,
          agent_id: selectedAgent, // This is the agent ID
          dataset_id: selectedDataset,
          selected_items: Array.from(selectedItems),
          service_provider: serviceProvider,
          task: agentTask // Use agent's task_type
        })
      };
    } else {
      // Existing flow for Human Task
      endpoint = "/backend/findpatterns_create?";
      
      // Extract up to 3 annotations from chat messages
      const annotationMessages = chatMessages
        .filter(msg => msg.type === 'annotation' && msg.content.trim() !== '')
        .slice(-3); // Get the last 3 annotations
      
      const annotations = annotationMessages.map((msg, index) => ({
        id: msg.id,
        content: msg.content,
        timestamp: msg.timestamp
      }));

      requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user_id: user.user_id || user.sub,
          test_query: "give me 2x2",
          analyser_id: selectedAnalyser,
          dataset_id: selectedDataset,
          selected_items: selectedItems.size > 0 ? Array.from(selectedItems) : [],
          max_sentences: maxSentences, // Pass max_sentences
          annotations: annotations // Include annotations in the request
        })
      };
    }

    try {
      const response = await fetch(
        (process.env.NEXT_PUBLIC_SERVER_URL || "") + endpoint,
        requestOptions
      );

      console.log("Response status:", response.status);
      const data = await response.json();
      console.log('Backend response:', data);
      
      let resultContent = "";
      if (data.status === 200 || data.status === '200') {
        if (useAgentExecution) {
          // Format agent response
          resultContent = "$ Agent analysis completed!\n\n" +
            "Agent: " + (data.agent_name || "Unknown") + "\n" +
            "Items Analyzed: " + (data.items_analyzed || 0) + "\n\n";
          
          // Show Blip2 description if available
          if (data.blip2_description) {
            resultContent += "Image Description (Blip2):\n" + data.blip2_description + "\n\n";
          }
          
          // Show final Ollama response
          resultContent += "Final Answer:\n" + (data.result || "No response returned.") + "\n";
          
          if (data.token_usage) {
            resultContent += "\nToken Usage:\n";
            if (data.token_usage.blip2) {
              resultContent += "  Blip2:\n" +
                "    Prompt: " + (data.token_usage.blip2.prompt_tokens || 0) + "\n" +
                "    Completion: " + (data.token_usage.blip2.completion_tokens || 0) + "\n" +
                "    Total: " + (data.token_usage.blip2.total_tokens || 0) + "\n";
            }
            if (data.token_usage.ollama) {
              resultContent += "  Ollama:\n" +
                "    Prompt: " + (data.token_usage.ollama.prompt_tokens || 0) + "\n" +
                "    Completion: " + (data.token_usage.ollama.completion_tokens || 0) + "\n" +
                "    Total: " + (data.token_usage.ollama.total_tokens || 0) + "\n";
            }
            // Fallback for old format
            if (!data.token_usage.blip2 && !data.token_usage.ollama) {
              resultContent += "  Prompt: " + (data.token_usage.prompt_tokens || 0) + "\n" +
                "  Completion: " + (data.token_usage.completion_tokens || 0) + "\n" +
                "  Total: " + (data.token_usage.total_tokens || 0) + "\n";
            }
          }
        } else {
          resultContent = "$ Test completed successfully!\n\n" + 
            "Response: " + (data.result || data.message || data.response || "No specific result returned.") + "\n";
        }
      } else {
        resultContent = "\n$ Error: " + (data.error || "Unknown error occurred.");
      }
      
      // Update the analysis message with the result
      setChatMessages(prev => prev.map(msg => 
        msg.id === newMessageId 
          ? { ...msg, content: msg.content + resultContent }
          : msg
      ));
      
    } catch (error) {
      console.error('Error during analysis:', error);
      const errorContent = "\n$ Error: Failed to connect to server. " + error.message;
      
      // Update the analysis message with the error
      setChatMessages(prev => prev.map(msg => 
        msg.id === newMessageId 
          ? { ...msg, content: msg.content + errorContent }
          : msg
      ));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAddAnnotation = () => {
    const newAnnotationId = Date.now();
    const annotationMessage = {
      id: newAnnotationId,
      type: 'annotation',
      content: '',
      timestamp: new Date(),
      isEditing: true
    };
    
    setChatMessages(prev => [...prev, annotationMessage]);
  };

  const handleAnnotationChange = (messageId, newContent) => {
    setChatMessages(prev => prev.map(msg => 
      msg.id === messageId 
        ? { ...msg, content: newContent }
        : msg
    ));
  };

  const handleSaveAnalysis = async () => {
    // Capture all analysis data for saving
    const analysisData = {
      timestamp: new Date().toISOString(),
      user_id: user.user_id || user.sub,
      analyser: getSelectedAnalyser(),
      dataset: getSelectedDataset(),
      selectedItems: Array.from(selectedItems),
      selectedItemsCount: selectedItems.size,
      chatMessages: chatMessages,
      analysisSummary: {
        totalMessages: chatMessages.length,
        analysisMessages: chatMessages.filter(msg => msg.type === 'analysis').length,
        annotationMessages: chatMessages.filter(msg => msg.type === 'annotation').length
      }
    };

    // Send data to backend to save in database
    try {
      const requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: user.user_id || user.sub,
          analyser_id: getSelectedAnalyser()?._id,
          dataset_id: getSelectedDataset()?._id,
          selected_items: Array.from(selectedItems),
          chat_messages: chatMessages,
          analysis_summary: {
            totalMessages: chatMessages.length,
            analysisMessages: chatMessages.filter(msg => msg.type === 'analysis').length,
            annotationMessages: chatMessages.filter(msg => msg.type === 'annotation').length
          }
        })
      };

      const response = await fetch(
        (process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/analysis/save",
        requestOptions
      );

      const data = await response.json();
      
      if (data.status === "200") {
        alert("Analysis saved successfully!");
        console.log("Analysis saved with ID:", data.analysis_id);
      } else {
        alert("Error saving analysis: " + (data.error || "Unknown error"));
        console.error("Backend error:", data.error);
      }
    } catch (error) {
      console.error('Error saving analysis:', error);
      alert("Error saving analysis: " + error.message);
    }
  };

  const handleClearChat = () => {
    setChatMessages([]);
  };

  // Helper function to get annotation count
  const getAnnotationCount = () => {
    return chatMessages.filter(msg => msg.type === 'annotation' && msg.content.trim() !== '').length;
  };

  // Dataset Table Component for Modal
  const DatasetTable = ({ dataset }) => {
    if (!dataset || !dataset.artworks) {
      return <p>No dataset data available.</p>;
    }

    const getTextContent = (item) => {
      if (item.content) {
        const textContent = item.content.find(c => c.content_type === 'text');
        return textContent ? textContent.content_value.text : 'No text content';
      }
      return 'No content';
    };

    const getImageContent = (item) => {
      if (item.content) {
        const imageContent = item.content.find(c => c.content_type === 'image');
        if (imageContent) {
          return (
            <ImageThumbnail itemId={item._id} imageStorageId={imageContent.content_value.image_storage_id} />
          );
        }
        return 'No image';
      }
      return 'No content';
    };

    // Pagination calculations
    const totalPages = Math.ceil(dataset.artworks.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentItems = dataset.artworks.slice(startIndex, endIndex);

    const handlePageChange = (newPage) => {
      setCurrentPage(newPage);
      // Keep selections when changing pages - no longer clearing
    };

    return (
      <div className="dataset-table-container" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div className="dataset-header" style={{ flexShrink: 0 }}>
          <h4>Dataset: {dataset.name}</h4>
          <p><strong>Type:</strong> {dataset.type} | <strong>Items:</strong> {dataset.artworks.length} | <strong>Selected:</strong> {selectedItems.size}</p>
          
          <div className="selection-controls">
            <button 
              className="btn btn-sm" 
              onClick={handleSelectAll}
              style={{ marginRight: '0.5em', backgroundColor: 'white', border: '1px solid #ccc', color: '#333' }}
            >
              Select All Dataset
            </button>
            <button 
              className="btn btn-sm" 
              onClick={handleDeselectAll}
              style={{ marginRight: '0.5em', backgroundColor: 'white', border: '1px solid #ccc', color: '#333' }}
            >
              Deselect All Dataset
            </button>
            <button 
              className="btn btn-sm" 
              onClick={handleSelectAllCurrentPage}
              style={{ marginRight: '0.5em', backgroundColor: 'white', border: '1px solid #ccc', color: '#333' }}
            >
              Select Current Page
            </button>
            <button 
              className="btn btn-sm" 
              onClick={handleDeselectAllCurrentPage}
              style={{ marginRight: '0.5em', backgroundColor: 'white', border: '1px solid #ccc', color: '#333' }}
            >
              Deselect Current Page
            </button>
          </div>
          
        </div>
        
        <div 
          className="table-responsive" 
          style={{ flex: '1 1 auto', minHeight: 0, overflowY: 'auto' }}
        >
          <table className="table table-striped table-sm">
            <thead>
              <tr>
                <th style={{ width: '50px' }}>
                  <input 
                    type="checkbox" 
                    checked={currentItems.length > 0 && currentItems.every(item => selectedItems.has(item._id))}
                    onChange={currentItems.every(item => selectedItems.has(item._id)) ? handleDeselectAllCurrentPage : handleSelectAllCurrentPage}
                    />
                </th>
                <th>#</th>
                <th>ID</th>
                <th>Text Content</th>
                <th>Image</th>
                <th>Position</th>
              </tr>
            </thead>
            <tbody>
              {currentItems.map((item, index) => (
                <tr key={item._id} className={selectedItems.has(item._id) ? 'table-primary' : ''}>
                  <td>
                    <input 
                      type="checkbox" 
                      checked={selectedItems.has(item._id)}
                      onChange={(e) => handleItemSelection(item._id, e)}
                      />
                  </td>
                  <td>{startIndex + index + 1}</td>
                  <td>{item._id}</td>
                  <td style={{ maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {getTextContent(item).substring(0, 100)}
                    {getTextContent(item).length > 100 && '...'}
                  </td>
                  <td>{getImageContent(item)}</td>
                  <td>{item.position || 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {totalPages > 0 && (
          <div className="dataset-pagination" style={{ flexShrink: 0 }}>
            <button 
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              style={{
                backgroundColor: currentPage === 1 ? '#6c757d' : 'black',
                color: 'white',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (currentPage !== 1) e.target.style.backgroundColor = '#333';
              }}
              onMouseLeave={(e) => {
                if (currentPage !== 1) e.target.style.backgroundColor = 'black';
              }}
            >
              ← Previous
            </button>
            <div className="page-info">
              Page {currentPage} of {totalPages}
            </div>
            <button 
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              style={{
                backgroundColor: currentPage === totalPages ? '#6c757d' : 'black',
                color: 'white',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '4px',
                cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s ease'
              }}
              onMouseEnter={(e) => {
                if (currentPage !== totalPages) e.target.style.backgroundColor = '#333';
              }}
              onMouseLeave={(e) => {
                if (currentPage !== totalPages) e.target.style.backgroundColor = 'black';
              }}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    );
  };

  const handleDatasetChange = (datasetId) => {
    console.log("Dataset selection changed to:", datasetId);
    setSelectedDataset(datasetId);
    // Clear selections when changing datasets
    setSelectedItems(new Set());
    setCurrentPage(1);
    // Clear chat messages when changing dataset
    setChatMessages([]);
  };

  const handleAnalyserChange = (analyserId) => {
    console.log("Analyser selection changed to:", analyserId);
    setSelectedAnalyser(analyserId);
    // Clear chat messages when changing analyser
    setChatMessages([]);
    // Reset maxSentences to default when changing models
    setMaxSentences(3);
  };


  

  return (
    <main>
      <div className="container">
        <h1>Tasks</h1>
        <hr/>

        <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
          <button
            onClick={() => setTaskType('human')}
            style={{
              border: '1px solid black',
              borderRadius: '5px',
              marginBottom: '4px',
              padding: '8px 12px',
              backgroundColor: taskType === 'human' ? '#f5f5f5' : 'transparent',
              cursor: 'pointer',
              minWidth: '120px'
            }}
            onMouseEnter={(e) => {
              if (taskType !== 'human') e.target.style.backgroundColor = '#f5f5f5';
            }}
            onMouseLeave={(e) => {
              if (taskType !== 'human') e.target.style.backgroundColor = 'transparent';
            }}
          >
            Human Task
          </button>
          <button
            onClick={() => setTaskType('ai')}
            style={{
              border: '1px solid black',
              borderRadius: '5px',
              marginBottom: '4px',
              padding: '8px 12px',
              backgroundColor: taskType === 'ai' ? '#f5f5f5' : 'transparent',
              cursor: 'pointer',
              minWidth: '120px'
            }}
            onMouseEnter={(e) => {
              if (taskType !== 'ai') e.target.style.backgroundColor = '#f5f5f5';
            }}
            onMouseLeave={(e) => {
              if (taskType !== 'ai') e.target.style.backgroundColor = 'transparent';
            }}
          >
            Agent Task
          </button>
        </div>
        <hr/>

        {taskType === null ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            Choose One Option
          </div>
        ) : taskType === 'human' ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            Lorem ipsum
          </div>
        ) : (
          <>
            <div style={{ border: '1px solid grey', borderRadius: '5px', padding: '10px', paddingLeft: '20px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 'bold' }}>Service Provider:</span>
              <select
                value={serviceProvider}
                onChange={(e) => setServiceProvider(e.target.value)}
                style={{
                  border: '1px solid grey',
                  borderRadius: '5px',
                  padding: '8px 12px',
                  minWidth: '200px',
                  fontSize: '1rem'
                }}
              >
                <option value="Ollama">Ollama</option>
              </select>
            </div>
            <div style={{ border: '1px solid grey', borderRadius: '5px', padding: '10px', paddingLeft: '20px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 'bold' }}>Agent:</span>
              <select
                value={selectedAgent || ''}
                onChange={(e) => setSelectedAgent(e.target.value)}
                style={{
                  border: '1px solid grey',
                  borderRadius: '5px',
                  padding: '8px 12px',
                  minWidth: '200px',
                  fontSize: '1rem'
                }}
              >
                <option value="">Select Agent</option>
                {agents.map((agent) => (
                  <option key={agent._id} value={agent._id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ border: '1px solid grey', borderRadius: '5px', padding: '10px', paddingLeft: '20px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 'bold' }}>Dataset:</span>
              <select
                value={selectedDataset || ''}
                onChange={(e) => handleDatasetChange(e.target.value)}
                style={{
                  border: '1px solid grey',
                  borderRadius: '5px',
                  padding: '8px 12px',
                  minWidth: '200px',
                  fontSize: '1rem'
                }}
              >
                <option value="">Select a dataset</option>
                {datasets.map((dataset) => (
                  <option key={dataset._id} value={dataset._id}>
                    {dataset.name}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ border: '1px solid grey', borderRadius: '5px', padding: '10px', paddingLeft: '20px', marginBottom: '10px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold' }}>Data Items:</span>
                <DatasetModal 
                  onPressHandler={handleSelectDataElements}
                  title="Select Individual Data Elements"
                  buttonText="Select"
                  modalSize="xl"
                  props={{
                    buttonStyle: {
                      backgroundColor: 'transparent',
                      color: 'black',
                      border: '1px solid grey',
                      borderRadius: '5px',
                      padding: '8px 12px',
                      minWidth: '200px',
                      fontSize: '1rem',
                      transition: 'background-color 0.2s ease'
                    },
                    buttonHoverStyle: {
                      backgroundColor: '#f5f5f5'
                    },
                    dialogClassName: 'custom-modal-80'
                  }}
                >
                  <div className="data-elements-modal">
                    {loadingDataset ? (
                      <p>Loading dataset data...</p>
                    ) : selectedDatasetData ? (
                      <DatasetTable dataset={selectedDatasetData} />
                    ) : (
                      <p>No dataset selected or failed to load dataset data.</p>
                    )}
                  </div>
                </DatasetModal>
              </div>
              {selectedItems.size > 0 && (
                <SelectedItemsDisplay 
                  selectedItems={selectedItems} 
                  datasetData={selectedDatasetData} 
                  onClearAll={handleDeselectAll}
                />
              )}
            </div>
            {/* Chat Messages Display */}
            {chatMessages.length > 0 ? (
              <div className="chat-messages" style={{
                marginTop: '2rem',
                border: '1px solid #b9b9b9',
                borderRadius: '8px',
                backgroundColor: '#fafafa',
                padding: '1rem'
              }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '1rem',
                  paddingBottom: '0.5rem',
                  borderBottom: '1px solid #ddd'
                }}>
                  <h5 style={{ margin: 0, color: '#333' }}>Analysis Session</h5>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ fontSize: '0.9rem', color: '#666' }}>
                      {chatMessages.length} message{chatMessages.length !== 1 ? 's' : ''}
                      {getAnnotationCount() > 0 && (
                        <span style={{ marginLeft: '0.5rem', color: '#28a745' }}>
                          • {getAnnotationCount()} annotation{getAnnotationCount() !== 1 ? 's' : ''}
                        </span>
                      )}
                    </span>
                    <button 
                      onClick={handleClearChat}
                      style={{
                        backgroundColor: 'transparent',
                        color: 'black',
                        border: '1px solid black',
                        padding: '0.25rem 0.5rem',
                        borderRadius: '5px',
                        cursor: 'pointer',
                        fontSize: '0.8rem',
                        transition: 'background-color 0.2s ease'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                    >
                      Clear Chat
                    </button>
                  </div>
                </div>
                
                {chatMessages.map((message, index) => (
                  <div key={message.id} className={`chat-message ${message.type}`} style={{
                    marginBottom: '1.5rem',
                    padding: '1rem',
                    borderRadius: '6px',
                    border: '1px solid #b9b9b9',
                    backgroundColor: message.type === 'analysis' ? '#f8f9fa' : '#fff',
                  }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '0.5rem'
                    }}>
                      <h6 style={{ 
                        margin: 0, 
                        color: 'black',
                        textTransform: 'capitalize'
                      }}>
                        {message.type === 'analysis' ? 'Analysis Results' : 'Annotation'}
                      </h6>
                      <small style={{ color: '#666' }}>
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </small>
                    </div>
                    
                    {message.type === 'analysis' && (
                      <div className="terminal-output" style={{
                        backgroundColor: '#ffffff',
                        color: '#333',
                        padding: '1rem',
                        borderRadius: '4px',
                        fontSize: '0.9rem',
                        fontFamily: 'var(--bs-font-sans-serif)',
                        overflowX: 'auto',
                        whiteSpace: 'pre-wrap'
                      }}>
                        {message.content}
                      </div>
                    )}
                    
                    {message.type === 'annotation' && (
                      <textarea
                        value={message.content}
                        onChange={(e) => handleAnnotationChange(message.id, e.target.value)}
                        placeholder="Add your annotation here..."
                        className="patterns-left-input"
                        style={{ 
                          minHeight: '100px',
                          width: '100%',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          padding: '0.5rem',
                          fontSize: '0.9rem',
                          lineHeight: '1.4'
                        }}
                      />
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{
                padding: '2rem',
                textAlign: 'center',
                backgroundColor: '#f8f9fa',
                border: '1px dashed #dee2e6',
                borderRadius: '8px',
                color: '#6c757d'
              }}>
                <h6 style={{ marginBottom: '0.5rem', color: '#495057' }}>No Task Executed</h6>

                <p style={{ margin: 0, fontSize: '0.9rem' }}>
                  Add elements from the Dataset and select the Task, "Add Annotation" to add notes.
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div style={{ 
              display: 'flex', 
              flexDirection: 'column',
              gap: '10px', 
              marginTop: '1rem',
              padding: '1rem',
              backgroundColor: '#ffffff',
              borderRadius: '6px',
              border: '1px solid #b9b9b9'
            }}>
              {/* Max Sentences Control - only show for opinion type */}
              {getSelectedAnalyser() && getSelectedAnalyser().analyser_type === 'opinion' && (
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '0.5rem',
                  marginBottom: '0.5rem'
                }}>
                  <label style={{ 
                    fontSize: '0.9rem', 
                    color: '#333',
                    whiteSpace: 'nowrap'
                  }}>
                    Max Sentences:
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={maxSentences}
                    onChange={(e) => setMaxSentences(parseInt(e.target.value) || 3)}
                    style={{
                      width: '60px',
                      padding: '0.25rem 0.5rem',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
              )}
              
              {/* Annotation Indicator */}
              {(() => {
                const annotationCount = getAnnotationCount();
                
                if (annotationCount > 0) {
                  return (
                    <div style={{ 
                      marginBottom: '0.5rem',
                      padding: '0.5rem',
                      backgroundColor: '#e8f5e8',
                      border: '1px solid #28a745',
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                      color: '#155724'
                    }}>
                      <strong>📝 Annotations will be included:</strong> {annotationCount} annotation{annotationCount !== 1 ? 's' : ''} 
                      {annotationCount > 3 && ` (only the last 3 will be used)`}
                    </div>
                  );
                }
                return null;
              })()}
              
              {/* Buttons Row */}
              <div style={{ 
                display: 'flex', 
                gap: '10px',
                flexWrap: 'wrap',
                alignItems: 'center'
              }}>
                <button 
                  className="patterns-create-btn" 
                  onClick={handleAnalyzeClick}
                  disabled={isAnalyzing || selectedItems.size === 0}
                  style={{
                    backgroundColor: (isAnalyzing || selectedItems.size === 0) ? '#f5f5f5' : 'transparent',
                    color: 'black',
                    border: '1px solid black',
                    padding: '0.5rem 1rem',
                    borderRadius: '5px',
                    cursor: (isAnalyzing || selectedItems.size === 0) ? 'not-allowed' : 'pointer',
                    fontSize: '0.9rem',
                    transition: 'background-color 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (!isAnalyzing && selectedItems.size > 0) e.target.style.backgroundColor = '#f5f5f5';
                  }}
                  onMouseLeave={(e) => {
                    if (!isAnalyzing && selectedItems.size > 0) e.target.style.backgroundColor = 'transparent';
                  }}
                >
                  {isAnalyzing ? 'Analysing...' : 'Analyse Data'}
                </button>
                
                <button 
                  className="patterns-create-btn" 
                  onClick={handleAddAnnotation}
                  style={{
                    backgroundColor: 'transparent',
                    color: 'black',
                    border: '1px solid black',
                    padding: '0.5rem 1rem',
                    borderRadius: '5px',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                    transition: 'background-color 0.2s ease'
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = '#f5f5f5'}
                  onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
                >
                  Add Annotation
                </button>
                
                <button 
                  className="patterns-create-btn" 
                  onClick={handleSaveAnalysis}
                  disabled={chatMessages.length === 0}
                  style={{
                    backgroundColor: chatMessages.length === 0 ? '#f5f5f5' : 'transparent',
                    color: 'black',
                    border: '1px solid black',
                    padding: '0.5rem 1rem',
                    borderRadius: '5px',
                    cursor: chatMessages.length === 0 ? 'not-allowed' : 'pointer',
                    fontSize: '0.9rem',
                    transition: 'background-color 0.2s ease'
                  }}
                  onMouseEnter={(e) => {
                    if (chatMessages.length > 0) e.target.style.backgroundColor = '#f5f5f5';
                  }}
                  onMouseLeave={(e) => {
                    if (chatMessages.length > 0) e.target.style.backgroundColor = 'transparent';
                  }}
                >
                  Save Analysis
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
};

export default withAuth(Tasks);


