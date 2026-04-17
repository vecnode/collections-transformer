import React, { useState, useEffect } from 'react';

const AnalysisDetailsModal = ({ 
  showModal, 
  selectedAnalysis, 
  selectedItemsDetails, 
  onClose 
}) => {
  const [csvData, setCsvData] = useState('');

  // Image loading component for modal
  const ModalImageThumbnail = ({ itemId, imageStorageId }) => {
    const [loadState, setLoadState] = useState("loading");
    const [image, setImage] = useState("");

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

    if (loadState === "loading") {
      return (
        <div style={{
          width: '60px',
          height: '60px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #ddd',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.8rem',
          color: '#666',
          fontStyle: 'italic'
        }}>
          Loading...
        </div>
      );
    }

    if (loadState === "error") {
      return (
        <div style={{
          width: '60px',
          height: '60px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #ddd',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.8rem',
          color: '#999',
          fontStyle: 'italic'
        }}>
          Error
        </div>
      );
    }

    return (
      <img 
        src={image}
        alt="Item preview"
        style={{
          maxWidth: '60px',
          maxHeight: '60px',
          objectFit: 'cover',
          borderRadius: '4px',
          border: '1px solid #ddd'
        }}
      />
    );
  };

  // Generate CSV data for download
  const generateCSVData = () => {
    if (!selectedAnalysis) return '';

    const rows = [];
    
    // Header row
    rows.push([
      'Analysis ID',
      'Analysis Name',
      'Dataset Name',
      'Status',
      'Created Date',
      'Selected Items Count',
      'Analysis Messages',
      'Annotation Messages',
      'Total Messages'
    ]);

    // Analysis summary row
    rows.push([
      selectedAnalysis._id || '',
      selectedAnalysis.analyser_name || 'Unknown',
      selectedAnalysis.dataset_name || 'Unknown',
      selectedAnalysis.status || 'Completed',
      new Date(selectedAnalysis.created_at).toLocaleString('en-GB', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        timeZone: 'Europe/London'
      }),
      selectedAnalysis.selected_items_count || selectedAnalysis.selected_items?.length || 0,
      selectedAnalysis.analysis_summary?.analysisMessages || 0,
      selectedAnalysis.analysis_summary?.annotationMessages || 0,
      selectedAnalysis.analysis_summary?.totalMessages || 0
    ]);

    // Add empty row for spacing
    rows.push([]);

    // Chat messages section
    if (selectedAnalysis.chat_messages && selectedAnalysis.chat_messages.length > 0) {
      rows.push(['Chat Messages']);
      rows.push(['Type', 'Timestamp', 'Content']);
      
      selectedAnalysis.chat_messages.forEach((message, index) => {
        rows.push([
          message.type || '',
          new Date(message.timestamp).toLocaleString('en-GB', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            timeZone: 'Europe/London'
          }),
          (message.content || '').replace(/"/g, '""') // Escape quotes for CSV
        ]);
      });
      
      rows.push([]);
    }

    // Selected items section
    if (selectedAnalysis.selected_items && selectedAnalysis.selected_items.length > 0) {
      rows.push(['Selected Items']);
      rows.push(['Item ID', 'Content Type', 'Content Value']);
      
      selectedAnalysis.selected_items.forEach((itemId, index) => {
        const itemDetail = selectedItemsDetails.find(item => String(item._id) === String(itemId));
        
        if (itemDetail && itemDetail.content) {
          itemDetail.content.forEach((content, contentIndex) => {
            let contentValue = '';
            if (content.content_type === 'text' && content.content_value && content.content_value.text) {
              contentValue = content.content_value.text.substring(0, 500); // Limit text length
            } else if (content.content_type === 'image' && content.content_value && content.content_value.image_storage_id) {
              contentValue = `Image: ${content.content_value.image_storage_id}`;
            }
            
            rows.push([
              itemId,
              content.content_type || '',
              contentValue.replace(/"/g, '""') // Escape quotes for CSV
            ]);
          });
        } else {
          rows.push([itemId, 'Loading...', '']);
        }
      });
    }

    // Convert to CSV format
    return rows.map(row => 
      row.map(cell => `"${cell}"`).join(',')
    ).join('\n');
  };

  // Download CSV function
  const downloadCSV = () => {
    const csvContent = generateCSVData();
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `analysis_${selectedAnalysis._id}_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  if (!showModal || !selectedAnalysis) {
    return null;
  }

  return (
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
        width: '60vw',
        height: '80vh',
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '20px',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
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
        
        <h3 style={{ marginBottom: '1rem', marginRight: '2rem' }}>Analysis Details</h3>
        
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '1rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '4px',
          border: '1px solid #dee2e6',
          fontFamily: 'Arial, sans-serif',
          fontSize: '0.9rem',
          lineHeight: '1.4'
        }}>
          <div style={{ marginBottom: '0.5rem' }}>
            <h4 style={{ marginBottom: '0.5rem', color: '#333' }}>Overview</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div style={{ padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                <strong>Analysis ID:</strong> {selectedAnalysis._id}
                <br />
                <small style={{ color: '#666' }}>Unique identifier for this analysis</small>
              </div>
              <div style={{ padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                <strong>Status:</strong> 
                <span style={{ 
                  padding: '2px 8px', 
                  borderRadius: '12px', 
                  fontSize: '0.8rem',
                  backgroundColor: '#f0f0f0',
                  color: '#333',
                  border: '1px solid #ccc',
                  marginLeft: '0.5rem'
                }}>
                  {selectedAnalysis.status}
                </span>
              </div>
              <div style={{ padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                <strong>Created:</strong> {new Date(selectedAnalysis.created_at).toLocaleString('en-GB', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                  timeZone: 'Europe/London'
                })}
              </div>
              <div style={{ padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                <strong>Selected Items:</strong> {selectedAnalysis.selected_items_count || selectedAnalysis.selected_items?.length || 0}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '0.5rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
              <div style={{ padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                <strong>Analysis Model:</strong> {selectedAnalysis.analyser_name || 'Unknown'}
                <br />
                <small style={{ color: '#666' }}>ID: {selectedAnalysis.analyser_id}</small>
              </div>
              <div style={{ padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                <strong>Dataset:</strong> {selectedAnalysis.dataset_name || 'Unknown'}
                <br />
                <small style={{ color: '#666' }}>ID: {selectedAnalysis.dataset_id}</small>
              </div>
            </div>
          </div>

          {selectedAnalysis.analysis_summary && (
            <div style={{ marginBottom: '1.5rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
                <div style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#333' }}>
                    {selectedAnalysis.analysis_summary.analysisMessages || 0}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>Analysis Messages</div>
                </div>
                <div style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#333' }}>
                    {selectedAnalysis.analysis_summary.annotationMessages || 0}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>Annotation Messages</div>
                </div>
                <div style={{ textAlign: 'center', padding: '0.5rem', backgroundColor: 'white', borderRadius: '4px', border: '1px solid #ddd' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#333' }}>
                    {selectedAnalysis.analysis_summary.totalMessages || 0}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#666' }}>Total Messages</div>
                </div>
              </div>
            </div>
          )}

          {selectedAnalysis.chat_messages && selectedAnalysis.chat_messages.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ marginBottom: '0.5rem', color: '#333' }}>Interactions ({selectedAnalysis.chat_messages.length})</h4>
              {selectedAnalysis.chat_messages.map((message, index) => (
                <div key={message.id || index} style={{ 
                  marginBottom: '1rem', 
                  padding: '1rem', 
                  backgroundColor: 'white', 
                  borderRadius: '4px',
                  border: '1px solid #ddd'
                }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '0.5rem',
                    paddingBottom: '0.5rem',
                    borderBottom: '1px solid #eee'
                  }}>
                    <span style={{ 
                      padding: '2px 8px', 
                      borderRadius: '12px', 
                      fontSize: '0.8rem',
                      backgroundColor: '#f0f0f0',
                      color: '#333',
                      border: '1px solid #ccc'
                    }}>
                      {message.type}
                    </span>
                    <small style={{ color: '#666' }}>
                      {new Date(message.timestamp).toLocaleString('en-GB', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        timeZone: 'Europe/London'
                      })}
                    </small>
                  </div>
                  <div style={{ 
                    fontFamily: 'monospace', 
                    fontSize: '0.85rem',
                    whiteSpace: 'pre-wrap',
                    maxHeight: '200px',
                    overflowY: 'auto',
                    backgroundColor: '#f8f9fa',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #ddd'
                  }}>
                    {message.content}
                  </div>
                </div>
              ))}
            </div>
          )}

          {selectedAnalysis.selected_items && selectedAnalysis.selected_items.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ marginBottom: '0.5rem', color: '#333' }}>Selected Items</h4>
              <div style={{ 
                backgroundColor: 'white', 
                padding: '0.5rem', 
                borderRadius: '4px',
                border: '1px solid #ddd',
                maxHeight: '300px',
                overflowY: 'auto'
              }}>
                {selectedAnalysis.selected_items.map((itemId, index) => {
                  const itemDetail = selectedItemsDetails.find(item => String(item._id) === String(itemId));
                  return (
                    <div key={index} style={{ 
                      padding: '0.5rem',
                      backgroundColor: '#f8f9fa',
                      borderRadius: '4px',
                      border: '1px solid #ddd'
                    }}>
                      <div style={{ 
                        display: 'inline-block', 
                        padding: '0.25rem 0.5rem', 
                        backgroundColor: '#f0f0f0', 
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        fontFamily: 'monospace',
                        border: '1px solid #ccc'
                      }}>
                        {itemId}
                      </div>
                      {itemDetail ? (
                        itemDetail.content && itemDetail.content.map((content, contentIndex) => (
                          <div key={contentIndex} style={{ marginTop: '0.5rem' }}>
                            {content.content_type === 'text' && content.content_value && content.content_value.text && (
                              <div style={{
                                fontSize: '0.85rem',
                                color: '#333',
                                padding: '0.25rem',
                                backgroundColor: 'white',
                                borderRadius: '2px',
                                border: '1px solid #eee',
                                maxHeight: '60px',
                                overflowY: 'auto',
                                fontStyle: 'italic'
                              }}>
                                {content.content_value.text.length > 100 
                                  ? content.content_value.text.substring(0, 100) + '...' 
                                  : content.content_value.text}
                              </div>
                            )}
                            {content.content_type === 'image' && content.content_value && content.content_value.image_storage_id && (
                              <div style={{
                                marginTop: '0.25rem',
                                textAlign: 'left'
                              }}>
                                <ModalImageThumbnail itemId={itemId} imageStorageId={content.content_value.image_storage_id} />
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <div style={{
                          fontSize: '0.8rem',
                          color: '#999',
                          fontStyle: 'italic',
                          marginTop: '0.5rem'
                        }}>
                          Loading item details...
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Download CSV Button */}
          <div style={{ 
            textAlign: 'center', 
            padding: '1rem', 
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            marginTop: '1rem'
          }}>
            <button 
              onClick={downloadCSV}
              style={{
                padding: '10px 20px',
                backgroundColor: 'black',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '0.9rem',
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#666'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'black'}
            >
              Download Analysis Spreadsheet
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisDetailsModal;
