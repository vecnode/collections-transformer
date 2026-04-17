import React, {useEffect, useState} from 'react'
import { useAuth } from "@/_contexts/AuthContext";
import { formatAnalyserType } from '@/_helpers/utills';
import Image from 'next/image';
import DatasetModal from './datasetModal';

// Image Thumbnail Component (copied from findpatterns.js)
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

const OverviewAnalyser = ({
  user,
  analyser_id=null,
  analyser=null,
  showPredictions=false,
  accordionLabels=["Details"],
  getAnalyser=()=>{},
  onUpdate=()=>{},
  onComplete=()=>{},
  onError=()=>{},
  onWarning=()=>{}
}) => {

  const [analyser_name, setAnalyserName] = useState("")
  const [task_description, setTaskDescription] = useState("")
  const [labelling_guide, setLabellingGuide] = useState("")
  const [chosen_analyser_type, setChosenAnalyserType] = useState("binary")
  const [dataset, setDataset] = useState({})
  const [labelset, setLabelset] = useState({})
  const [loadingDataset, setLoadingDataset] = useState(false)
  const [accuracy, setAccuracy] = useState(null)
  const [loadingAccuracy, setLoadingAccuracy] = useState(false)
  
  // Test sample selection state
  const [selectedTestSamples, setSelectedTestSamples] = useState(new Set())
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage] = useState(50)
  const [testSampleLabels, setTestSampleLabels] = useState({})

  useEffect(() => {
    if (Object.keys(analyser).length > 0) {
      setAnalyserName(analyser.name || "")
      setTaskDescription(analyser.task_description || "")
      setLabellingGuide(analyser.labelling_guide || "")
      setChosenAnalyserType(analyser.analyser_type || "binary")
      
      // Fetch dataset and labelset data if available
      if (analyser.dataset_id) {
        console.log("Fetching dataset for ID:", analyser.dataset_id)
        getDataset(analyser.dataset_id)
      }
      if (analyser.labelset_id) {
        console.log("Fetching labelset for ID:", analyser.labelset_id)
        console.log("Analyser data:", analyser)
        getLabelset(analyser.labelset_id)
      } else {
        console.log("No labelset_id found in analyser:", analyser)
      }
    }
  }, [analyser])

  const getDataset = (dataset_id) => {
    setLoadingDataset(true)
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };

    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/dataset?" + new URLSearchParams({
      dataset_id: dataset_id,
      include_items: true
    }), requestOptions)
    .then(res => res.json()).then((res) => {
      console.log("Dataset response:", res)
      if (res.status === 200 || res.status === '200') {
        setDataset(res.data)
        console.log("Dataset loaded:", res.data)
      }
      setLoadingDataset(false)
    }).catch((error) => {
      console.error("Error fetching dataset:", error)
      setLoadingDataset(false)
    })
  }

  const getLabelset = (labelset_id) => {
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };

    console.log("Fetching labelset with ID:", labelset_id)
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/labelset?" + new URLSearchParams({
      labelset_id: labelset_id,
      include_labels: true
    }), requestOptions)
    .then(res => res.json()).then((res) => {
      console.log("Labelset response:", res)
      if (res.status === 200 || res.status === '200') {
        setLabelset(res.data)
        console.log("Labelset loaded:", res.data)
        if (res.data.labels) {
          console.log("Labels found:", res.data.labels.length)
          res.data.labels.forEach(label => {
            console.log(`Label: item_id=${label.item_id} (${typeof label.item_id}), value=${label.value}`)
          })
        } else {
          console.log("No labels array found in labelset data")
        }
      } else {
        console.error("Failed to load labelset:", res.error)
      }
    }).catch((error) => {
      console.error("Error fetching labelset:", error)
    })
  }

  const computeAccuracy = async () => {
    if (!analyser_id) return;
    
    // Check if we have selected test samples and labels
    if (selectedTestSamples.size === 0) {
      alert('Please select test samples first');
      return;
    }
    
    const labeledSamples = Object.keys(testSampleLabels).filter(id => testSampleLabels[id]);
    if (labeledSamples.length === 0) {
      alert('Please label at least one test sample before computing accuracy');
      return;
    }
    
    setLoadingAccuracy(true);
    
    try {
      // Prepare the data for backend accuracy computation
      const testSampleData = {
        analyser_id: analyser_id,
        selected_test_samples: Array.from(selectedTestSamples),
        test_sample_labels: testSampleLabels
      };
      
      const requestOptions = {
        method: 'POST',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(testSampleData)
      };
      
      const response = await fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/compute_accuracy_with_samples", requestOptions);
      const data = await response.json();
      
      if (data.status === "200") {
        setAccuracy(data.data.accuracy);
        setLoadingAccuracy(false);
        
        // Show additional metrics if available
        if (data.data.metrics) {
          const metrics = data.data.metrics;
          let metricsMessage = `Accuracy: ${(data.data.accuracy * 100).toFixed(1)}%\n`;
          
          if (metrics.precision) metricsMessage += `Precision: ${(parseFloat(metrics.precision) * 100).toFixed(1)}%\n`;
          if (metrics.recall) metricsMessage += `Recall: ${(parseFloat(metrics.recall) * 100).toFixed(1)}%\n`;
          if (metrics.f1_score) metricsMessage += `F1-Score: ${(parseFloat(metrics.f1_score) * 100).toFixed(1)}%\n`;
          if (metrics.mae) metricsMessage += `MAE: ${parseFloat(metrics.mae).toFixed(2)}\n`;
          if (metrics.rmse) metricsMessage += `RMSE: ${parseFloat(metrics.rmse).toFixed(2)}\n`;
          
          alert(`Accuracy computation completed!\n\n${metricsMessage}\nTest samples processed: ${data.data.test_samples_processed}`);
        } else {
          alert(`Accuracy computation completed!\n\nAccuracy: ${(data.data.accuracy * 100).toFixed(1)}%\nTest samples processed: ${data.data.test_samples_processed}`);
        }
      } else {
        throw new Error(data.error || 'Failed to compute accuracy');
      }
    } catch (error) {
      console.error('Error computing accuracy:', error);
      alert('Error computing accuracy: ' + error.message);
      setLoadingAccuracy(false);
    }
  }

  // Helper functions to get content from items
  const getTextContent = (item) => {
    if (item.content) {
      const textContent = item.content.find(c => c.content_type === 'text');
      return textContent ? textContent.content_value.text : 'No text content';
    }
    return item.textContent || 'No text content';
  };

  const getImageContent = (item) => {
    if (item.content) {
      const imageContent = item.content.find(c => c.content_type === 'image');
      return imageContent ? imageContent.content_value.image_storage_id : null;
    }
    return item.imageStorageId || null;
  };

  // Get training examples and test samples from the dataset
  const getTrainingExamples = () => {
    if (!dataset.artworks || !analyser.example_refs) {
      console.log("No dataset artworks or example_refs:", { artworks: dataset.artworks, example_refs: analyser.example_refs })
      return []
    }
    const examples = dataset.artworks.filter(item => analyser.example_refs.includes(item._id))
    console.log("Training examples found:", examples.length, examples)
    console.log("Training example IDs:", examples.map(item => ({ id: item._id, type: typeof item._id })))
    console.log("Analyser example_refs:", analyser.example_refs)
    return examples
  }

  const getTestSamples = () => {
    if (!dataset.artworks || !analyser.sample_ids) {
      console.log("No dataset artworks or sample_ids:", { artworks: dataset.artworks, sample_ids: analyser.sample_ids })
      return []
    }
    const samples = dataset.artworks.filter(item => analyser.sample_ids.includes(item._id))
    console.log("Test samples found:", samples.length, samples)
    return samples
  }

  // Test sample selection functions
  const handleTestSampleSelection = (itemId, event) => {
    event.preventDefault();
    event.stopPropagation();
    
    const newSelectedTestSamples = new Set(selectedTestSamples);
    if (newSelectedTestSamples.has(itemId)) {
      newSelectedTestSamples.delete(itemId);
    } else {
      newSelectedTestSamples.add(itemId);
    }
    setSelectedTestSamples(newSelectedTestSamples);
  };

  const handleSelectAllTestSamplesCurrentPage = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (dataset.artworks) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      const currentItems = dataset.artworks.slice(startIndex, endIndex);
      const currentItemIds = currentItems.map(item => item._id);
      
      const newSelectedTestSamples = new Set(selectedTestSamples);
      currentItemIds.forEach(id => newSelectedTestSamples.add(id));
      setSelectedTestSamples(newSelectedTestSamples);
    }
  };

  const handleDeselectAllTestSamplesCurrentPage = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (dataset.artworks) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      const currentItems = dataset.artworks.slice(startIndex, endIndex);
      const currentItemIds = currentItems.map(item => item._id);
      
      const newSelectedTestSamples = new Set(selectedTestSamples);
      currentItemIds.forEach(id => newSelectedTestSamples.delete(id));
      setSelectedTestSamples(newSelectedTestSamples);
    }
  };

  const handleSelectAllTestSamples = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    if (dataset.artworks) {
      const allItemIds = dataset.artworks.map(item => item._id);
      setSelectedTestSamples(new Set(allItemIds));
    }
  };

  const handleDeselectAllTestSamples = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setSelectedTestSamples(new Set());
  };

  // Handle test sample label changes
  const handleTestSampleLabelChange = (itemId, newLabel) => {
    setTestSampleLabels(prev => ({
      ...prev,
      [itemId]: newLabel
    }));
  };

  const handleSelectDataElements = () => {
    // This will be handled by the modal
    console.log("Select test samples clicked");
  };

  const trainingExamples = getTrainingExamples()
  const testSamples = getTestSamples()

  // Dataset Table Component for Test Sample Selection Modal
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
    };

    return (
      <div className="dataset-table-container">
        <div className="dataset-header">
          <h4>Dataset: {dataset.name}</h4>
          <p><strong>Type:</strong> {dataset.type} | <strong>Items:</strong> {dataset.artworks.length} | <strong>Selected:</strong> {selectedTestSamples.size}</p>
          
          <div className="selection-controls">
            <button 
              className="btn btn-sm" 
              onClick={handleSelectAllTestSamples}
              style={{ marginRight: '0.5em', backgroundColor: 'white', border: '1px solid #ccc', color: '#333' }}
            >
              Select All Dataset
            </button>
            <button 
              className="btn btn-sm" 
              onClick={handleDeselectAllTestSamples}
              style={{ marginRight: '0.5em', backgroundColor: 'white', border: '1px solid #ccc', color: '#333' }}
            >
              Deselect All Dataset
            </button>
            <button 
              className="btn btn-sm" 
              onClick={handleSelectAllTestSamplesCurrentPage}
              style={{ marginRight: '0.5em', backgroundColor: 'white', border: '1px solid #ccc', color: '#333' }}
            >
              Select Current Page
            </button>
            <button 
              className="btn btn-sm" 
              onClick={handleDeselectAllTestSamplesCurrentPage}
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
                    checked={currentItems.length > 0 && currentItems.every(item => selectedTestSamples.has(item._id))}
                    onChange={currentItems.every(item => selectedTestSamples.has(item._id)) ? handleDeselectAllTestSamplesCurrentPage : handleSelectAllTestSamplesCurrentPage}
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
                <tr key={item._id} className={selectedTestSamples.has(item._id) ? 'table-primary' : ''}>
                  <td>
                    <input 
                      type="checkbox" 
                      checked={selectedTestSamples.has(item._id)}
                      onChange={(e) => handleTestSampleSelection(item._id, e)}
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

  // Selected Test Samples Display Component
  const SelectedTestSamplesDisplay = ({ selectedTestSamples, datasetData, onClearAll, testSampleLabels, onLabelChange }) => {
    if (!selectedTestSamples || selectedTestSamples.size === 0 || !datasetData || !datasetData.artworks) {
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


    const selectedItemsData = datasetData.artworks.filter(item => selectedTestSamples.has(item._id));

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
          <strong>Selected Test Samples: {selectedTestSamples.size}</strong>
          <button 
            className="btn btn-sm btn-outline-secondary" 
            onClick={onClearAll}
          >
            Clear All
          </button>
        </div>
        <small style={{ color: '#666', display: 'block', marginBottom: '0.75rem' }}>
          {selectedTestSamples.size} of {datasetData.artworks.length} items selected for testing
          {Object.keys(testSampleLabels).length > 0 && (
            <span style={{ marginLeft: '1rem', color: '#28a745' }}>
              • {Object.keys(testSampleLabels).length} items labeled
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
                      onClick={() => onLabelChange(item.id, testSampleLabels[item.id] === 'positive' ? 'negative' : 'positive')}
                      style={{
                        padding: '0.25rem 0.5rem',
                        fontSize: '0.75rem',
                        backgroundColor: testSampleLabels[item.id] === 'positive' ? '#28a745' : 
                                         testSampleLabels[item.id] === 'negative' ? '#dc3545' : '#6c757d',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        minWidth: '60px'
                      }}
                    >
                      {testSampleLabels[item.id] === 'positive' ? 'Positive' : 
                       testSampleLabels[item.id] === 'negative' ? 'Negative' : 'Label'}
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
                    onClick={() => onLabelChange(item.id, testSampleLabels[item.id] === 'positive' ? 'negative' : 'positive')}
                    style={{
                      padding: '0.25rem 0.5rem',
                      fontSize: '0.75rem',
                      backgroundColor: testSampleLabels[item.id] === 'positive' ? '#28a745' : 
                                       testSampleLabels[item.id] === 'negative' ? '#dc3545' : '#6c757d',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      minWidth: '60px'
                    }}
                  >
                    {testSampleLabels[item.id] === 'positive' ? 'Positive' : 
                     testSampleLabels[item.id] === 'negative' ? 'Negative' : 'Label'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* Model Overview Section */}
      <div style={{
        border: '1px solid lightgrey',
        borderRadius: '8px',
        padding: '1.5rem',
        marginBottom: '1.5rem',
        backgroundColor: 'white'
      }}>
        <div>
          <h4 style={{ marginTop: 0, marginBottom: '1rem' }}>Overview</h4>
          
          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Name:</strong> {analyser.name || "Untitled"}
        </div>

          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Task Description:</strong> "{analyser.task_description || "No description provided"}"
        </div>

          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Label Type:</strong> {formatAnalyserType(analyser.analyser_type)}
          </div>
          
          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Labelling Guide:</strong> "{analyser.labelling_guide || "No labelling guide provided"}"
        </div>
          
          <div style={{ marginBottom: '0.5rem' }}>
            <strong>Status:</strong> 
            {accuracy !== null ? 
              ` Trained (${(parseFloat(accuracy) * 100).toFixed(1)}% accuracy)` : 
              analyser.accuracy ? 
                ` Trained (${(parseFloat(analyser.accuracy) * 100).toFixed(1)}% accuracy)` : 
                " Accuracy not compared with human labels"
            }
          </div>
          
          {analyser.last_updated && (
            <div style={{ marginBottom: '1rem' }}>
              <strong>Last Updated:</strong> {new Date(analyser.last_updated).toLocaleString()}
            </div>
          )}


        </div>
      </div>

      {/* Dataset Information */}
      {dataset._id && (
        <div style={{
          border: '1px solid lightgrey',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          backgroundColor: 'white'
        }}>
          <div>
            <h4 style={{ marginTop: 0, marginBottom: '1rem' }}>Dataset Information</h4>
            
            <div style={{ marginBottom: '0.5rem' }}>
              <strong>Dataset:</strong> {dataset.name || "Unknown"}
            </div>
            
            <div style={{ marginBottom: '0.5rem' }}>
              <strong>Type:</strong> {dataset.type ? dataset.type.charAt(0).toUpperCase() + dataset.type.slice(1) : "Unknown"}
            </div>

            {dataset.artworks && (
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>Total Items:</strong> {dataset.artworks.length}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Training Examples Section */}
      {trainingExamples.length > 0 && (
        <div style={{
          border: '1px solid lightgrey',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          backgroundColor: 'white'
        }}>
          <div>
            <h4 style={{ marginTop: 0, marginBottom: '1rem' }}>
              Training Examples ({trainingExamples.length} items)
            </h4>
            <p style={{ marginBottom: '1rem', color: '#666' }}>
              These are the specific items that were chosen as examples when creating this model:
            </p>
            
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap',
              gap: '1rem',
              marginTop: '1rem'
            }}>
              {trainingExamples.map((item, index) => {
                const textContent = getTextContent(item);
                const imageStorageId = getImageContent(item);
                
                return (
                  <div key={item._id} style={{
                    border: '1px solid #e0e0e0',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    backgroundColor: '#f8f9fa',
                    maxWidth: '250px',
                    minWidth: '150px',
                    flex: '1 1 300px',
                    overflow: 'hidden'
                  }}>
                    <div style={{ marginBottom: '0.5rem', color: '#666666', fontWeight: 'bold', fontSize: '0.9rem' }}>
                      Data Element {index + 1}
                    </div>
                    
                    {/* Image and Text Layout */}
                    <div style={{ 
                      display: 'flex', 
                      gap: '0.75rem', 
                      marginBottom: '0.5rem',
                      maxHeight: '100px',
                      overflow: 'hidden'
                    }}>
                      {/* Image Thumbnail */}
                      {imageStorageId && (
                        <div style={{ 
                          width: '80px', 
                          height: '80px', 
                          flexShrink: 0,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
                          <ImageThumbnail itemId={item._id} imageStorageId={imageStorageId} />
                        </div>
                      )}
                      
                      {/* Text Content */}
                      {textContent && textContent !== 'No text content' && (
                        <div style={{ flex: 1, overflow: 'hidden' }}>
                          <strong style={{ fontSize: '0.85rem' }}>Text:</strong><br/>
                          <div style={{ 
                            padding: '0.5rem', 
                            backgroundColor: 'white', 
                            borderRadius: '4px',
                            border: '1px solid #ddd',
                            marginTop: '0.25rem',
                            fontSize: '0.8rem',
                            lineHeight: '1.3',
                            maxHeight: '60px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical'
                          }}>
                            {textContent}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Label */}
                    {labelset.labels && (
                      <div style={{ fontSize: '0.85rem' }}>
                        <strong>Label:</strong> {
                          (() => {
                            const itemIdStr = String(item._id)
                            const label = labelset.labels.find(l => String(l.item_id) === itemIdStr)
                            if (label) {
                              console.log(`Found label for item ${itemIdStr}: value=${label.value} (type: ${typeof label.value}), rationale=${label.rationale}`)
                            } else {
                              console.log(`No label found for item ${itemIdStr}`)
                            }
                            return label ? (
                              // All model types now use binary labels (positive/negative) for training examples
                              <span style={{ 
                                backgroundColor: (label.value === '1' || label.value === 1) ? '#d4edda' : '#f8d7da',
                                padding: '0.25rem 0.5rem',
                                borderRadius: '4px',
                                fontWeight: 'bold',
                                marginLeft: '0.5rem',
                                fontSize: '0.75rem'
                              }}>
                                {(label.value === '1' || label.value === 1) ? 'Positive' : 'Negative'}
                              </span>
                            ) : 'No label'
                          })()
                        }
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Accuracy Computation Section, TODO with new interface

      <div style={{
        border: '1px solid lightgrey',
        borderRadius: '8px',
        padding: '1.5rem',
        marginBottom: '1.5rem',
        backgroundColor: 'white'
      }}>
        <div>
          <h4 style={{ marginTop: 0, marginBottom: '1rem' }}>
            Model Accuracy
          </h4>
          <p style={{ marginBottom: '1rem', color: '#666' }}>
            Compute the accuracy of this model against human labels to evaluate its performance:
          </p>
          
          {selectedTestSamples.size === 0 && (
            <ul style={{ margin: '0.5rem 0 0 1.5rem', padding: 0 }}>
              <li>Select test samples from the dataset using the button below</li>
              <li>Label those test samples using the inline buttons</li>
              <li>Click "Compute Accuracy" to evaluate the model</li>
            </ul>
          )}
          
          <div style={{ 
            display: 'flex', 
            alignItems: 'center',
            gap: '1rem',
            marginTop: '1rem',
            flexWrap: 'wrap'
          }}>
            <button 
              onClick={computeAccuracy}
              disabled={loadingAccuracy || !analyser_id}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: loadingAccuracy ? '#6c757d' : '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: loadingAccuracy ? 'not-allowed' : 'pointer',
                fontSize: '0.9rem',
                fontWeight: '500'
              }}
            >
              {loadingAccuracy ? (
                <>
                  <span className="spinner-border spinner-border-sm" role="status" style={{ marginRight: '0.5rem' }}></span>
                  Computing...
                </>
              ) : (
                'Compute Accuracy'
              )}
            </button>
            
            <DatasetModal 
              onPressHandler={handleSelectDataElements}
              title="Select Test Samples"
              iconName="list"
              modalSize="xl"
              props={{
                buttonStyle: {
                  backgroundColor: 'black',
                  color: 'white',
                  border: '1px solid black',
                  transition: 'background-color 0.2s ease',
                  padding: '0.5rem 1rem',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '0.9rem',
                  fontWeight: '500'
                },
                buttonHoverStyle: {
                  backgroundColor: '#333'
                }
              }}
            >
              <div className="data-elements-modal">
                {loadingDataset ? (
                  <p>Loading dataset data...</p>
                ) : dataset._id ? (
                  <DatasetTable dataset={dataset} />
                ) : (
                  <p>No dataset selected or failed to load dataset data.</p>
                )}
              </div>
            </DatasetModal>
            
            {accuracy !== null && (
              <div style={{ 
                padding: '0.5rem 1rem',
                backgroundColor: '#d4edda',
                border: '1px solid #c3e6cb',
                borderRadius: '4px',
                color: '#155724',
                fontWeight: '500'
              }}>
                Accuracy: {(parseFloat(accuracy) * 100).toFixed(1)}%
              </div>
            )}
          </div>
          
          {selectedTestSamples.size > 0 && (
            <SelectedTestSamplesDisplay 
              selectedTestSamples={selectedTestSamples} 
              datasetData={dataset} 
              onClearAll={handleDeselectAllTestSamples} 
              testSampleLabels={testSampleLabels} 
              onLabelChange={handleTestSampleLabelChange} 
            />
          )}
          
          {accuracy !== null && (
            <div style={{ 
              marginTop: '1rem',
              padding: '0.75rem',
              backgroundColor: '#f8f9fa',
              border: '1px solid #dee2e6',
              borderRadius: '4px',
              fontSize: '0.9rem',
              color: '#495057'
            }}>
              <strong>What this means:</strong>
              {analyser.analyser_type === 'binary' ? (
                <div>This model correctly classified {(parseFloat(accuracy) * 100).toFixed(1)}% of the test samples when compared to human labels.</div>
              ) : analyser.analyser_type === 'score' ? (
                <div>This model's predicted scores are within ±1 of the actual scores for {(parseFloat(accuracy) * 100).toFixed(1)}% of the test samples.</div>
              ) : (
                <div>This model achieved {(parseFloat(accuracy) * 100).toFixed(1)}% accuracy on the test samples.</div>
              )}
            </div>
          )}
        </div>
      </div>
      

      {testSamples.length > 0 && (
        <div style={{
          border: '1px solid lightgrey',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          backgroundColor: 'white'
        }}>
          <div>
            <h4 style={{ marginTop: 0, marginBottom: '1rem' }}>
              Test Samples ({testSamples.length} items)
            </h4>
            <p style={{ marginBottom: '1rem', color: '#666' }}>
              These are the items used to test the model's accuracy:
            </p>
            
            <div style={{ 
              display: 'flex', 
              flexWrap: 'wrap',
              gap: '1rem',
              marginTop: '1rem'
            }}>
              {testSamples.map((item, index) => {
                const textContent = getTextContent(item);
                const imageStorageId = getImageContent(item);
                
                return (
                  <div key={item._id} style={{
                    border: '1px solid #e0e0e0',
                    borderRadius: '8px',
                    padding: '0.75rem',
                    backgroundColor: '#f8f9fa',
                    maxWidth: '400px',
                    minWidth: '300px',
                    flex: '1 1 300px'
                  }}>
                    <div style={{ marginBottom: '0.5rem', color: '#28a745', fontWeight: 'bold', fontSize: '0.9rem' }}>
                      Test Sample {index + 1}
                    </div>
                    
                    <div style={{ 
                      display: 'flex', 
                      gap: '0.75rem', 
                      marginBottom: '0.5rem',
                      maxHeight: '100px',
                      overflow: 'hidden'
                    }}>

                      {imageStorageId && (
                        <div style={{ 
                          width: '80px', 
                          height: '80px', 
                          flexShrink: 0,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}>
                          <ImageThumbnail itemId={item._id} imageStorageId={imageStorageId} />
                        </div>
                      )}
                      
                      {textContent && textContent !== 'No text content' && (
                        <div style={{ flex: 1, overflow: 'hidden' }}>
                          <strong style={{ fontSize: '0.85rem' }}>Text:</strong><br/>
                          <div style={{ 
                            padding: '0.5rem', 
                            backgroundColor: 'white', 
                            borderRadius: '4px',
                            border: '1px solid #ddd',
                            marginTop: '0.25rem',
                            fontSize: '0.8rem',
                            lineHeight: '1.3',
                            maxHeight: '60px',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            display: '-webkit-box',
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: 'vertical'
                          }}>
                            {textContent}
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {labelset.labels && (
                      <div style={{ fontSize: '0.85rem' }}>
                        <strong>Label:</strong> {
                          (() => {
                            const itemIdStr = String(item._id)
                            const label = labelset.labels.find(l => String(l.item_id) === itemIdStr)
                            if (label) {
                              console.log(`Found label for item ${itemIdStr}: value=${label.value} (type: ${typeof label.value}), rationale=${label.rationale}`)
                            } else {
                              console.log(`No label found for item ${itemIdStr}`)
                            }
                            return label ? (
                              // All model types now use binary labels (positive/negative) for training examples
                              <span style={{ 
                                backgroundColor: (label.value === '1' || label.value === 1) ? '#d4edda' : '#f8d7da',
                                padding: '0.25rem 0.5rem',
                                borderRadius: '4px',
                                fontWeight: 'bold',
                                marginLeft: '0.5rem',
                                fontSize: '0.75rem'
                              }}>
                                {(label.value === '1' || label.value === 1) ? 'Positive' : 'Negative'}
                              </span>
                            ) : 'No label'
                          })()
                        }
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {loadingDataset && (
        <div style={{
          border: '1px solid lightgrey',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          backgroundColor: 'white'
        }}>
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div className="spinner-border text-primary" role="status"></div>
            <div style={{ marginTop: '1rem' }}>Loading dataset information...</div>
          </div>
        </div>
      )}

      {!dataset._id && !loadingDataset && analyser.dataset_id && (
        <div style={{
          border: '1px solid lightgrey',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          backgroundColor: 'white'
        }}>
          <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '3rem', marginBottom: '1rem' }}>info</span>
            <div>Dataset information not available</div>
          </div>
        </div>
      )}

      {!loadingDataset && dataset._id && trainingExamples.length === 0 && testSamples.length === 0 && (
        <div style={{
          border: '1px solid lightgrey',
          borderRadius: '8px',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          backgroundColor: 'white'
        }}>
          <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
            <span className="material-symbols-outlined" style={{ fontSize: '3rem', marginBottom: '1rem' }}>info</span>
            <div>No training examples or test samples found for this model</div>
            <div style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
              This might mean the model was created without selecting specific examples or the data is not available.
            </div>
          </div>
        </div>
      )}
      */}
      
    </div>
  )
}

export default OverviewAnalyser
