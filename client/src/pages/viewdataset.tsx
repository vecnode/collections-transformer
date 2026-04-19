import Head from 'next/head'

import React, {useEffect, useState} from 'react'
import { useSearchParams } from 'next/navigation'
import { useAuth } from "@/contexts/AuthContext";
import { withAuth } from "@/components/withAuth";

import StatusBox from '@/components/statusBox';
import type { Dataset, CollectionItem } from '@/types';






const ViewDataset = () => {
    const { user } = useAuth();

    const title = "Collections Transformer - View Dataset"

    var params = useSearchParams()
    let param_dataset_id = params.get('dataset_id')

    const [dataset, setDataset] = useState<Dataset>({
      id:"",
      name:"",
      artworks:[],
      dataset_type: ""
    })

    const [datasetStatus, setDatasetStatus] = useState("")
    const [dataset_id, setDatasetId] = useState("")


    const getDataset = (dataset_id: string) => {

      const requestOptions: RequestInit = {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
      };
    
      try {
        fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/dataset?" + new URLSearchParams({
          dataset_id:dataset_id,
          include_items:"true"
        }),requestOptions)
        .then(response => response.json())
        .then(
          res => {
            console.log("=== API Response ===", res);
            console.log("Dataset data:", res.data);
            console.log("Artworks:", res.data.artworks);
            if (res.data.artworks && res.data.artworks.length > 0) {
              console.log("First item:", res.data.artworks[0]);
            }
            
            const artworks = res.data.artworks || res.data.items || [];
            const artworkCount = res.data.artwork_count || artworks.length;
            setDatasetStatus("Loaded "+artworkCount+" data records");
            
            const datasetToSet = {
              ...res.data,
              artworks: artworks
            };
            setDataset(datasetToSet as Dataset);
          }
        )
      } catch (e){
        console.log("Error fetching dataset:", e)
      }
    }

    useEffect(() => {
      if (dataset_id!= ""){
        setDatasetStatus("Loading dataset...")
        getDataset(dataset_id)
      }
    }, [dataset_id])

    useEffect(()=>{
      if(param_dataset_id!=undefined && dataset_id==""){
        setDatasetId(param_dataset_id)
      }
    },[])


    const getItemPreview = (item: CollectionItem): string => {
      if (!item) {
        return 'Unknown';
      }

      // Priority 1: Check for object_id (most specific identifier)
      if (item.object_id && typeof item.object_id === 'string') {
        return item.object_id.length > 100 
          ? item.object_id.substring(0, 100) + '...' 
          : item.object_id;
      }

      // Priority 2: Check for direct text property (backend returns this for text items)
      const directText = (item as any).text;
      if (directText && typeof directText === 'string') {
        return directText.length > 100 
          ? directText.substring(0, 100) + '...' 
          : directText;
      }

      // Priority 3: Check other direct properties that might contain the name
      for (const field of ['name', 'title', 'label', 'description']) {
        const value = (item as any)[field];
        if (value && typeof value === 'string') {
          return value.length > 100 
            ? value.substring(0, 100) + '...' 
            : value;
        }
      }

      // Priority 4: Extract from content array
      if (item.content && Array.isArray(item.content) && item.content.length > 0) {
        for (const content of item.content) {
          if (content.content_type === 'text' && content.content_value?.text) {
            const text = content.content_value.text;
            return text.length > 100 
              ? text.substring(0, 100) + '...' 
              : text;
          }
          // Check for images
          if (content.content_type === 'image') {
            return '[Image]';
          }
        }
      }

      // Fallback: Position or ID
      const position = (item as any).position;
      return position !== undefined 
        ? `Item ${position}`  
        : `Item ${item._id?.substring(0, 8) ?? 'unknown'}`;
    };

    return (

      <>
      <Head>
        <title>{title}</title>
      </Head>

      <main className="ws-main">
        <div className="container ws-shell">
          
          {/* Hero section */}
          <section className="home-hero">
            <span className="home-kicker">Collections Transformer</span>
            <h1 className="home-title">{dataset.name || 'Dataset'}</h1>
            <p className="home-subtitle">
              Viewing dataset with {dataset.artworks ? dataset.artworks.length : 0} items
              {dataset.dataset_type && ` • Type: ${dataset.dataset_type}`}
            </p>
          </section>

          {/* Stats strip */}
          <div className="ws-stat-strip" style={{ animationDelay: '60ms' }}>
            <div className="ws-stat">
              <span className="ws-stat-value">{dataset.artworks ? dataset.artworks.length : 0}</span>
              <span className="ws-stat-label">Total Items</span>
            </div>
            <div className="ws-stat">
              <span className="ws-stat-value">{dataset.dataset_type || 'Mixed'}</span>
              <span className="ws-stat-label">Dataset Type</span>
            </div>
            <div className="ws-stat">
              <span className="ws-stat-value">{dataset.id ? String(dataset.id).substring(0, 8) : '...'}</span>
              <span className="ws-stat-label">Dataset ID</span>
            </div>
          </div>

          {/* Content panel */}
          <div className="agent-card ws-panel-card">
            <div className="agent-card-body ws-panel-body">
              {!dataset.artworks || dataset.artworks.length === 0 ? (
                <div className="ws-empty">
                  {dataset.artworks === undefined ? 'Loading items...' : 'No items in this dataset yet.'}
                </div>
              ) : (
                <>
                  <div style={{ marginBottom: '1rem', fontSize: '0.875rem', color: 'var(--ink-muted)' }}>
                    Showing {dataset.artworks.length} items
                  </div>

                  {/* Debug panel - show first item structure */}
                  {dataset.artworks.length > 0 && (
                    <div style={{
                      marginBottom: '1rem',
                      padding: '0.75rem',
                      backgroundColor: '#f0f0f0',
                      border: '1px solid #ccc',
                      borderRadius: '4px',
                      fontSize: '0.75rem',
                      fontFamily: 'monospace',
                      maxHeight: '200px',
                      overflowY: 'auto'
                    }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Debug - First Item Structure:</div>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {JSON.stringify(dataset.artworks[0], null, 2)}
                      </pre>
                    </div>
                  )}

                  <div className="ws-table-wrap">
                    <table className="ws-table">
                      <thead>
                        <tr>
                          <th style={{ width: '80px' }}>Position</th>
                          <th>Name / Preview</th>
                          <th style={{ width: '100px' }}>Type</th>
                          <th style={{ width: '120px' }}>ID</th>
                        </tr>
                      </thead>
                      <tbody>
                        {dataset.artworks.map((item: CollectionItem, index: number) => {
                          const contentType = item.content && item.content.length > 0 
                            ? item.content[0].content_type || 'unknown'
                            : 'unknown';
                          const itemName = getItemPreview(item);
                          return (
                            <tr key={item._id || index}>
                              <td>{item.position !== undefined && item.position !== null ? item.position : index + 1}</td>
                              <td style={{ fontWeight: 500 }}>{itemName}</td>
                              <td style={{ fontSize: '0.85rem', color: 'var(--ink-muted)' }}>{contentType}</td>
                              <td style={{ fontSize: '0.75rem', color: 'var(--ink-muted)', fontFamily: 'monospace' }}>
                                {item._id ? String(item._id).substring(0, 12) + '...' : '-'}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          </div>

          {datasetStatus && (
            <div style={{ marginTop: '1rem' }}>
              <StatusBox text={datasetStatus} />
            </div>
          )}

        </div>
      </main>

      </>
  )
}

export default withAuth(ViewDataset)
