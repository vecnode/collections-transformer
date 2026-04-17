import React, { useEffect, useState } from 'react';

import DatasetModal from '../components/datasetModal';


import { useAuth } from "@/contexts/AuthContext";
import { withAuth } from "@/components/withAuth";

// Custom Image Thumbnail Component for Table (from findpatterns.js)
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

// Text Modal Component (from findpatterns.js)
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

// Selected Examples Display Component (similar to findpatterns.js)
const SelectedExamplesDisplay = ({ selectedExamples, datasetData, onClearAll, itemLabels, onLabelChange }) => {
  if (!selectedExamples || selectedExamples.length === 0 || !datasetData || !datasetData.artworks) {
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



  const selectedItemsData = datasetData.artworks.filter(item => selectedExamples.includes(item._id));

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

  return (
    <div style={{
      marginTop: '1rem',
      padding: '0.75rem',
      backgroundColor: 'rgb(236, 236, 236)',
      borderRadius: '6px',
      border: '1px solid rgb(185, 185, 185)' 
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
        <strong>Selected Examples: {selectedExamples.length}</strong>
        <button 
          className="btn btn-sm btn-outline-secondary" 
          onClick={onClearAll}
        >
          Clear All
        </button>
      </div>
      <small style={{ color: '#666', display: 'block', marginBottom: '0.75rem' }}>
        {selectedExamples.length} of {datasetData.artworks.length} examples selected
        {Object.keys(itemLabels).length > 0 && (
          <span style={{ marginLeft: '1rem', color: '#28a745' }}>
            • {Object.keys(itemLabels).length} items labeled
          </span>
        )}
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
                  <button
                    onClick={() => onLabelChange(item.id, itemLabels[item.id] === 'positive' ? 'negative' : 'positive')}
                    style={{
                      padding: '0.25rem 0.5rem',
                      fontSize: '0.75rem',
                      backgroundColor: itemLabels[item.id] === 'positive' ? '#28a745' : 
                                       itemLabels[item.id] === 'negative' ? '#dc3545' : '#6c757d',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      minWidth: '60px'
                    }}
                  >
                    {itemLabels[item.id] === 'positive' ? 'Positive' : 
                     itemLabels[item.id] === 'negative' ? 'Negative' : 'Label'}
                  </button>
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
                    overflow: 'hidden'
                  }}
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
                <button
                  onClick={() => onLabelChange(item.id, itemLabels[item.id] === 'positive' ? 'negative' : 'positive')}
                  style={{
                    padding: '0.25rem 0.5rem',
                    fontSize: '0.75rem',
                    backgroundColor: itemLabels[item.id] === 'positive' ? '#28a745' : 
                                     itemLabels[item.id] === 'negative' ? '#dc3545' : '#6c757d',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    minWidth: '60px'
                  }}
                >
                  {itemLabels[item.id] === 'positive' ? 'Positive' : 
                   itemLabels[item.id] === 'negative' ? 'Negative' : 'Label'}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

const NewAgent = () => {
  const { user } = useAuth();
  const [datasets, setDatasets] = useState([]);
  const [selectedDataset, setSelectedDataset] = useState(null);
  const [selectedButtonType, setSelectedButtonType] = useState('boolean');
  
  // Form state
  const [aiName, setAiName] = useState('');
  const [taskDescription, setTaskDescription] = useState('');
  const [taskType, setTaskType] = useState('Text Detection (T/F)'); // Task type selection
  const [labellingGuide, setLabellingGuide] = useState('');
  const [selectedExamples, setSelectedExamples] = useState([]);
  const [itemLabels, setItemLabels] = useState({});
  const [promptPreview, setPromptPreview] = useState("");
  const [showPromptPreview, setShowPromptPreview] = useState(false)
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [showTextModal, setShowTextModal] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [selectedDatasetData, setSelectedDatasetData] = useState(null);
  const [loadingDataset, setLoadingDataset] = useState(false);
  const [detectedFormat, setDetectedFormat] = useState('');
  const [showExamples, setShowExamples] = useState(false);

  useEffect(() => {
    if (user) {
      getDatasets();
    }
  }, [user]);

  // When datasets are loaded, select the last one by default
  useEffect(() => {
    if (datasets.length > 0 && !datasets.some(d => d._id === selectedDataset)) {
      setSelectedDataset(datasets[datasets.length - 1]._id);
    }
  }, [datasets, selectedDataset]);

  // Fetch dataset data when selected dataset changes
  useEffect(() => {
    if (selectedDataset) {
      fetchDatasetData(selectedDataset);
      detectDatasetFormat(selectedDataset);
    }
  }, [selectedDataset]);

  const detectDatasetFormat = (datasetId) => {
    const dataset = datasets.find(d => d._id === datasetId);
    if (dataset) {
      if (dataset.type === 'text') {
        setDetectedFormat('text');
      } else if (dataset.type === 'image') {
        setDetectedFormat('image');
      } else if (dataset.type === 'textimage') {
        setDetectedFormat('textimage');
      }
    }
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

  // Fetch dataset data when selected dataset changes
  const fetchDatasetData = async (datasetId) => {
    if (!datasetId) {
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
      
      const response = await fetch(url, requestOptions);
      const res = await response.json();
      
      if (res.status === 200 || res.status === '200') {
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

  const handleSelectDataElements = () => {
    // This will be handled by the modal
    console.log("Select data elements clicked");
  };

  // Handle item selection
  const handleItemSelection = (itemId, event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (selectedExamples.includes(itemId)) {
      setSelectedExamples(prev => prev.filter(id => id !== itemId));
    } else {
      setSelectedExamples(prev => [...prev, itemId]);
    }
  };

  // Select all items on current page
  const handleSelectAllCurrentPage = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (selectedDatasetData && selectedDatasetData.artworks) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      const currentItems = selectedDatasetData.artworks.slice(startIndex, endIndex);
      const currentItemIds = currentItems.map(item => item._id);
      
      const newSelectedExamples = [...selectedExamples];
      currentItemIds.forEach(id => {
        if (!newSelectedExamples.includes(id)) {
          newSelectedExamples.push(id);
        }
      });
      setSelectedExamples(newSelectedExamples);
    }
  };

  // Deselect all items on current page
  const handleDeselectAllCurrentPage = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (selectedDatasetData && selectedDatasetData.artworks) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      const currentItems = selectedDatasetData.artworks.slice(startIndex, endIndex);
      const currentItemIds = currentItems.map(item => item._id);
      
      setSelectedExamples(prev => prev.filter(id => !currentItemIds.includes(id)));
    }
  };

  // Select all items in entire dataset
  const handleSelectAll = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (selectedDatasetData && selectedDatasetData.artworks) {
      const allItemIds = selectedDatasetData.artworks.map(item => item._id);
      setSelectedExamples(allItemIds);
    }
  };

  // Deselect all items in entire dataset
  const handleDeselectAll = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedExamples([]);
  };

  // Handle label changes for individual items
  const handleLabelChange = (itemId, newLabel) => {
    setItemLabels(prev => ({
      ...prev,
      [itemId]: newLabel
    }));
  };

  // Dataset Table Component for Modal (similar to findpatterns.js)
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

    const handleTextClick = (text) => {
      setSelectedText(text);
      setShowTextModal(true);
    };

    // Pagination calculations
    const totalPages = Math.ceil(dataset.artworks.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentItems = dataset.artworks.slice(startIndex, endIndex);

    const handlePageChange = (newPage) => {
      setCurrentPage(newPage);
    };

    return (
      <div className="dataset-table-container">
        <div className="dataset-header">
          <h4>Dataset: {dataset.name}</h4>
          <p><strong>Type:</strong> {dataset.type} | <strong>Items:</strong> {dataset.artworks.length} | <strong>Selected:</strong> {selectedExamples.length}</p>
          
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
        
        <div className="table-responsive" style={{ maxHeight: '400px', overflowY: 'auto' }}>
          <table className="table table-striped table-sm">
            <thead>
              <tr>
                <th style={{ width: '50px' }}>
                  <input 
                    type="checkbox" 
                    checked={currentItems.length > 0 && currentItems.every(item => selectedExamples.includes(item._id))}
                    onChange={currentItems.every(item => selectedExamples.includes(item._id)) ? handleDeselectAllCurrentPage : handleSelectAllCurrentPage}
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
                <tr key={item._id} className={selectedExamples.includes(item._id) ? 'table-primary' : ''}>
                  <td>
                    <input 
                      type="checkbox" 
                      checked={selectedExamples.includes(item._id)}
                      onChange={(e) => handleItemSelection(item._id, e)}
                      />
                  </td>
                  <td>{startIndex + index + 1}</td>
                  <td>{item._id}</td>
                  <td 
                    style={{ 
                      maxWidth: '300px', 
                      overflow: 'hidden', 
                      textOverflow: 'ellipsis',
                      cursor: 'pointer'
                    }}
                    onClick={() => handleTextClick(getTextContent(item))}
                    title="Click to view full text"
                  >
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
        {totalPages > 1 && (
          <div className="dataset-pagination">
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
    setSelectedExamples([]);
    setCurrentPage(1);
  };

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
    // Note: Dataset and other fields are optional for agents

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

    const response = await fetch(
      (process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/agent_new",
      requestOptions
    );

    const data = await response.json();    
    if (data.status === "200") {
      alert('Agent created successfully!');
      // Reset form
      setAiName('');
      setTaskDescription('');
      setTaskType('Text Detection (T/F)');
      setLabellingGuide('');
      setSelectedExamples([]);
      setSelectedDataset(null);
      setItemLabels({});
      setPromptPreview('');
      setShowPromptPreview(false);
    } else {
      alert('Error creating Agent: ' + (data.error || 'Unknown error'));
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

        {/* Examples card (collapsible) */}
        <section className="agent-card agent-card-collapsible">
          <button
            type="button"
            className="agent-card-toggle"
            onClick={() => setShowExamples(!showExamples)}
            aria-expanded={showExamples}
          >
            <div className="agent-card-header" style={{ pointerEvents: 'none' }}>
              <span className="agent-card-icon material-symbols-outlined">dataset</span>
              <div>
                <h2 className="agent-card-title">Training Examples <span className="agent-badge">Optional</span></h2>
                <p className="agent-card-subtitle">Attach labelled examples from a dataset to guide the agent prompt.</p>
              </div>
            </div>
            <span className="material-symbols-outlined agent-toggle-chevron">
              {showExamples ? 'expand_less' : 'expand_more'}
            </span>
          </button>

          {showExamples && (
            <div className="agent-card-body">
              <div className="agent-field">
                <label className="agent-label">Example Guide</label>
                <textarea
                  className="agent-input agent-textarea"
                  value={labellingGuide}
                  onChange={(e) => setLabellingGuide(e.target.value)}
                  placeholder="Describe what positive and negative labels mean. e.g. Positive: abstract art with geometric shapes. Negative: representational or figurative works."
                />
              </div>

              <div className="agent-field">
                <label className="agent-label">Example Dataset</label>
                <select
                  className="agent-input agent-select"
                  value={selectedDataset || ''}
                  onChange={(e) => handleDatasetChange(e.target.value)}
                >
                  <option value="">Select a dataset</option>
                  {datasets.map((dataset) => (
                    <option key={dataset._id} value={dataset._id}>
                      {dataset.name} ({dataset.type || 'unknown type'})
                    </option>
                  ))}
                </select>
              </div>

              <div className="agent-field">
                <label className="agent-label">Example Data Items</label>
                <DatasetModal
                  onPressHandler={handleSelectDataElements}
                  title="Example Data Items"
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
                    buttonHoverStyle: { backgroundColor: '#f5f5f5' },
                    dialogClassName: 'custom-modal-80'
                  }}
                >
                  <div className="data-elements-modal">
                    {loadingDataset ? (
                      <p>Loading dataset data…</p>
                    ) : selectedDatasetData ? (
                      <DatasetTable dataset={selectedDatasetData} />
                    ) : (
                      <p>No dataset selected or failed to load dataset data.</p>
                    )}
                  </div>
                </DatasetModal>

                {selectedExamples.length > 0 && (
                  <SelectedExamplesDisplay
                    selectedExamples={selectedExamples}
                    datasetData={selectedDatasetData}
                    onClearAll={handleDeselectAll}
                    itemLabels={itemLabels}
                    onLabelChange={handleLabelChange}
                  />
                )}
              </div>
            </div>
          )}
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

      {/* Text Modal */}
      {showTextModal && (
        <TextModal text={selectedText} onClose={() => setShowTextModal(false)} />
      )}
    </main>
  );
};

export default withAuth(NewAgent);
