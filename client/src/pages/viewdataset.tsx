import Head from 'next/head'

import React, {useEffect, useState} from 'react'
import { useSearchParams } from 'next/navigation'
import { useAuth } from "@/contexts/AuthContext";
import { withAuth } from "@/components/withAuth";

import StatusBox from '@/components/statusBox';
import type { Dataset, CollectionItem } from '@/types';


const ItemThumbnail = ({ itemId, imageStorageId }: { itemId: string; imageStorageId: string }) => {
    const [loadState, setLoadState] = useState<'loading' | 'ready' | 'error'>('loading')
    const [image, setImage] = useState('')

    useEffect(() => {
      let isCancelled = false

      const getImage = async () => {
        setLoadState('loading')

        try {
          const response = await fetch((process.env.NEXT_PUBLIC_SERVER_URL || '') + '/api/v1/backend/item_image?' + new URLSearchParams({
            item_id: itemId,
            image_storage_id: imageStorageId
          }), {
            method: 'GET',
            mode: 'cors',
            headers: {'Content-Type': 'application/json'}
          })

          const res = await response.json()
          if (!isCancelled && res.status === '200') {
            setImage('data:image/jpeg;base64,' + res.data)
            setLoadState('ready')
          } else if (!isCancelled) {
            setLoadState('error')
          }
        } catch {
          if (!isCancelled) {
            setLoadState('error')
          }
        }
      }

      void getImage()

      return () => {
        isCancelled = true
      }
    }, [imageStorageId, itemId])

    if (loadState === 'loading') {
      return (
        <div style={{
          marginTop: '0.25rem',
          padding: '0.5rem',
          backgroundColor: '#fff',
          borderRadius: '2px',
          height: '140px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--ink-muted)',
          fontSize: '0.85rem'
        }}>
          Loading image...
        </div>
      )
    }

    if (loadState === 'error') {
      return (
        <div style={{
          marginTop: '0.25rem',
          padding: '0.5rem',
          backgroundColor: '#fff',
          borderRadius: '2px',
          height: '140px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--ink-muted)',
          fontSize: '0.85rem'
        }}>
          Image unavailable
        </div>
      )
    }

    return (
      <div style={{
        marginTop: '0.25rem',
        padding: '0.5rem',
        backgroundColor: '#fff',
        borderRadius: '2px',
        height: '140px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden'
      }}>
        <img
          src={image}
          alt="Item thumbnail"
          style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
        />
      </div>
    )
}

const ImageReferencePreview = ({ filename }: { filename: string }) => {
    return (
      <div style={{
        marginTop: '0.25rem',
        padding: '0.5rem',
        backgroundColor: '#fff',
        borderRadius: '2px',
        height: '140px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        color: 'var(--ink-muted)'
      }}>
        <div style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '0.35rem' }}>Image reference</div>
        <div style={{ fontSize: '0.8rem', wordBreak: 'break-word' }}>{filename}</div>
      </div>
    )
}






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
    const [selectedItem, setSelectedItem] = useState<CollectionItem | null>(null)


    const getDataset = (dataset_id: string) => {

      const requestOptions: RequestInit = {
        method: 'GET',
        headers: {'Content-Type': 'application/json'}
      };
    
      try {
        fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/dataset?" + new URLSearchParams({
          dataset_id:dataset_id,
          include_items:"true"
        }),requestOptions)
        .then(response => response.json())
        .then(
          res => {
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
      } catch {
        setDatasetStatus("Failed to load dataset")
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

    useEffect(() => {
      if (dataset.artworks && dataset.artworks.length > 0) {
        setSelectedItem((current: CollectionItem | null) => {
          if (current && dataset.artworks.some((item: CollectionItem) => item._id === current._id)) {
            return current
          }
          return dataset.artworks[0]
        })
      }
    }, [dataset.artworks])


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

    const looksLikeImageFilename = (value: string | undefined): boolean => {
      return typeof value === 'string' && /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(value.trim());
    };

    const hasImageContent = (item: CollectionItem): boolean => {
      if (!item.content || !Array.isArray(item.content)) {
        return false;
      }

      return item.content.some((content: NonNullable<CollectionItem['content']>[number]) => {
        const imageStorageId = content.content_value?.image_storage_id;
        const textValue = content.content_value?.text;
        const urlValue = content.content_value?.url;
        const contentValue = typeof textValue === 'string' ? textValue : urlValue;

        return content.content_type === 'image'
          || typeof imageStorageId === 'string'
          || looksLikeImageFilename(contentValue);
      });
    };

    const hasTextContent = (item: CollectionItem): boolean => {
      if (!item.content || !Array.isArray(item.content)) {
        return false;
      }

      return item.content.some((content: NonNullable<CollectionItem['content']>[number]) => {
        const textValue = content.content_value?.text;
        return content.content_type === 'text'
          && typeof textValue === 'string'
          && textValue.trim() !== ''
          && !looksLikeImageFilename(textValue);
      });
    };

    const getDatasetTypeFromItems = (): string => {
      if (!dataset.artworks || dataset.artworks.length === 0) return 'Mixed';
      
      const hasText = dataset.artworks.some((item: CollectionItem) => hasTextContent(item));
      const hasImage = dataset.artworks.some((item: CollectionItem) => hasImageContent(item));
      
      if (hasText && hasImage) return 'Mixed';
      if (hasText) return 'text';
      if (hasImage) return 'image';
      return 'Mixed';
    };

    const getDisplayDatasetType = (): string => {
      const detectedType = getDatasetTypeFromItems();
      const declaredType = typeof dataset.dataset_type === 'string' ? dataset.dataset_type.toLowerCase() : '';

      if (!declaredType || declaredType === 'mixed' || declaredType === 'text' || declaredType === 'image') {
        return detectedType;
      }

      return dataset.dataset_type || detectedType;
    };

    const getItemContentValue = (item: CollectionItem): string => {
      if (item.content && Array.isArray(item.content) && item.content.length > 0) {
        const textContent = item.content.find((content: NonNullable<CollectionItem['content']>[number]) => content.content_type === 'text' && content.content_value?.text);
        if (textContent?.content_value?.text) {
          return textContent.content_value.text;
        }

        const firstContent = item.content[0];
        if (typeof firstContent.content_value?.text === 'string') {
          return firstContent.content_value.text;
        }
        if (typeof firstContent.content_value?.url === 'string') {
          return firstContent.content_value.url;
        }
      }
      return '-';
    };

    const getItemImageStorageId = (item: CollectionItem): string | null => {
      if (!item.content || !Array.isArray(item.content)) {
        return null;
      }

      const imageContent = item.content.find((content: NonNullable<CollectionItem['content']>[number]) => typeof content.content_value?.image_storage_id === 'string');
      return imageContent?.content_value?.image_storage_id ?? null;
    };

    const getItemTextValues = (item: CollectionItem): string[] => {
      if (!item.content || !Array.isArray(item.content)) {
        return [];
      }

      return item.content
        .filter((content: NonNullable<CollectionItem['content']>[number]) => {
          const textValue = content.content_value?.text;
          return content.content_type === 'text'
            && typeof textValue === 'string'
            && textValue.trim() !== '';
        })
        .map((content: NonNullable<CollectionItem['content']>[number]) => (content.content_value?.text || '').trim());
    };

    const getImageReferenceName = (item: CollectionItem): string | null => {
      if (!item.content || !Array.isArray(item.content)) {
        return null;
      }

      const referenceContent = item.content.find((content: NonNullable<CollectionItem['content']>[number]) => {
        const textValue = content.content_value?.text;
        const urlValue = content.content_value?.url;
        return looksLikeImageFilename(typeof textValue === 'string' ? textValue : urlValue);
      });

      if (!referenceContent) {
        return null;
      }

      const textValue = referenceContent.content_value?.text;
      const urlValue = referenceContent.content_value?.url;
      return typeof textValue === 'string' ? textValue : (typeof urlValue === 'string' ? urlValue : null);
    };

    const isItemImage = (item: CollectionItem): boolean => {
      return getItemImageStorageId(item) !== null || getImageReferenceName(item) !== null;
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
              <span className="ws-stat-value">{getDisplayDatasetType()}</span>
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

                  {/* Item details panel */}
                  {dataset.artworks.length > 0 && (
                    <div style={{
                      marginBottom: '1rem',
                      padding: '0.75rem',
                      backgroundColor: '#f0f0f0',
                      border: '1px solid #ccc',
                      borderRadius: '4px'
                    }}>
                      <div style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>
                        {selectedItem ? `Item #${selectedItem.position !== undefined ? selectedItem.position : dataset.artworks.indexOf(selectedItem) + 1}` : 'Item'}
                      </div>
                      {selectedItem || dataset.artworks[0] ? (
                        <div style={{ fontSize: '0.85rem', lineHeight: '1.5' }}>
                          {(() => {
                            const currentItem = selectedItem || dataset.artworks[0];
                            const imageStorageId = getItemImageStorageId(currentItem);
                            const imageReference = getImageReferenceName(currentItem);
                            const textValues = getItemTextValues(currentItem);
                            const hasImage = Boolean(imageStorageId || imageReference);
                            const hasText = textValues.length > 0;

                            return (
                              <>
                          <div style={{ marginBottom: '0.5rem' }}>
                            <strong>ID:</strong> {currentItem._id || '-'}
                          </div>
                          <div style={{ marginBottom: '0.5rem' }}>
                            <strong>Position:</strong> {currentItem.position !== undefined ? currentItem.position : dataset.artworks.indexOf(currentItem) + 1}
                          </div>
                          <div>
                            <strong>Content:</strong> 
                            {hasImage ? (
                              <>
                            {imageStorageId ? (
                              <ItemThumbnail
                                itemId={currentItem._id}
                                imageStorageId={imageStorageId}
                              />
                            ) : (
                              <ImageReferencePreview
                                filename={imageReference || 'Unknown image'}
                              />
                            )}
                            {hasText ? (
                              <div style={{ marginTop: '0.4rem', padding: '0.5rem', backgroundColor: '#fff', borderRadius: '2px', fontSize: '0.8rem', maxHeight: '150px', overflowY: 'auto', wordBreak: 'break-word' }}>
                                {textValues.join(' | ')}
                              </div>
                            ) : null}
                              </>
                            ) : (
                              <div style={{ marginTop: '0.25rem', padding: '0.5rem', backgroundColor: '#fff', borderRadius: '2px', fontSize: '0.8rem', maxHeight: '150px', overflowY: 'auto', wordBreak: 'break-word' }}>
                                {getItemContentValue(currentItem)}
                              </div>
                            )}
                          </div>
                              </>
                            );
                          })()}
                        </div>
                      ) : null}
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
                          const contentType = isItemImage(item)
                            ? 'image'
                            : (hasTextContent(item) ? 'text' : 'unknown');
                          const itemName = getItemPreview(item);
                          const isSelected = selectedItem?._id === item._id;
                          return (
                            <tr 
                              key={item._id || index}
                              onClick={() => setSelectedItem(item)}
                              style={{ 
                                cursor: 'pointer',
                                backgroundColor: isSelected ? '#e8e8e8' : 'transparent',
                                transition: 'background-color 0.2s'
                              }}
                              onMouseEnter={(e) => {
                                if (!isSelected) {
                                  (e.currentTarget as HTMLTableRowElement).style.backgroundColor = '#f5f5f5';
                                }
                              }}
                              onMouseLeave={(e) => {
                                if (!isSelected) {
                                  (e.currentTarget as HTMLTableRowElement).style.backgroundColor = 'transparent';
                                }
                              }}
                            >
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
