'use client'

import Head from 'next/head'
import React, { useState, useEffect } from 'react'
import { useAuth } from "@/_contexts/AuthContext";
import { withAuth } from "@/_components/withAuth";

// TreeNode component for recursive tree rendering
const TreeNode = ({ node, level, expandedNodes, onToggle, onLoadChildren }) => {
  const nodeId = node.id;
  const isExpanded = expandedNodes.has(nodeId);
  const hasChildren = node.children !== undefined && node.children.length > 0;
  const isLoading = node.loading === true;

  const handleClick = () => {
    if (node.loadOnExpand && (!node.children || node.children.length === 0) && !isLoading) {
      onLoadChildren(node);
    }
    onToggle(nodeId);
  };

  const indent = level * 20;

  return (
    <div style={{ fontFamily: 'monospace', fontSize: '0.9rem' }}>
      <div
        style={{
          paddingLeft: `${indent}px`,
          paddingTop: '2px',
          paddingBottom: '2px',
          cursor: 'pointer',
          userSelect: 'none'
        }}
        onClick={handleClick}
        onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
        onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
      >
        <span style={{ marginRight: '5px' }}>
          {isLoading ? '⏳' : hasChildren || node.loadOnExpand ? (isExpanded ? '▼' : '▶') : '  '}
        </span>
        <span style={{ fontWeight: level === 0 ? 'bold' : 'normal' }}>
          {node.name}
        </span>
        {node.count !== undefined && (
          <span style={{ color: '#666', marginLeft: '5px' }}>
            ({node.count})
          </span>
        )}
        {node.type && (
          <span style={{ color: '#999', marginLeft: '5px', fontSize: '0.85em' }}>
            [{node.type}]
          </span>
        )}
      </div>
      {isExpanded && (
        <div>
          {isLoading && (
            <div style={{ paddingLeft: `${indent + 25}px`, color: '#999', fontStyle: 'italic' }}>
              Loading...
            </div>
          )}
          {hasChildren && node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              expandedNodes={expandedNodes}
              onToggle={onToggle}
              onLoadChildren={onLoadChildren}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Format value for display
const formatValue = (value) => {
  if (value === null) return 'null';
  if (value === undefined) return 'undefined';
  
  const valueType = typeof value;
  
  if (valueType === 'string') {
    if (value.length > 50) {
      return `"${value.substring(0, 50)}..."`;
    }
    return `"${value}"`;
  }
  
  if (valueType === 'object') {
    if (Array.isArray(value)) {
      return `Array[${value.length}]`;
    }
    if (value.$oid) {
      return `ObjectId("${value.$oid}")`;
    }
    if (value.$date) {
      return `Date("${new Date(value.$date).toISOString()}")`;
    }
    return 'Object';
  }
  
  return String(value);
};

// Convert document to tree nodes
const documentToNodes = (doc, docId) => {
  const nodes = [];
  
  for (const [key, value] of Object.entries(doc)) {
    const nodeId = `doc:${docId}:field:${key}`;
    const valueType = typeof value;
    let children = null;
    let loadOnExpand = false;
    
    if (value === null || value === undefined) {
      children = [];
    } else if (Array.isArray(value)) {
      children = value.map((item, index) => {
        const itemId = `doc:${docId}:field:${key}:item:${index}`;
        if (typeof item === 'object' && item !== null) {
          return {
            id: itemId,
            name: `[${index}]`,
            type: 'Object',
            children: Object.entries(item).map(([k, v]) => ({
              id: `${itemId}:${k}`,
              name: `${k}: ${formatValue(v)}`,
              type: typeof v,
              children: []
            }))
          };
        }
        return {
          id: itemId,
          name: `[${index}]: ${formatValue(item)}`,
          type: typeof item,
          children: []
        };
      });
    } else if (typeof value === 'object' && value !== null) {
      if (value.$oid) {
        children = [];
      } else if (value.$date) {
        children = [];
      } else {
        children = Object.entries(value).map(([k, v]) => ({
          id: `${nodeId}:${k}`,
          name: `${k}: ${formatValue(v)}`,
          type: typeof v,
          children: []
        }));
      }
    } else {
      children = [];
    }
    
    nodes.push({
      id: nodeId,
      name: `${key}: ${formatValue(value)}`,
      type: valueType,
      children: children || [],
      count: Array.isArray(value) ? value.length : undefined
    });
  }
  
  return nodes;
};

const DB = () => {
  const { user, isLoading } = useAuth();
  const [collections, setCollections] = useState([]);
  const [databaseName, setDatabaseName] = useState('');
  const [expandedNodes, setExpandedNodes] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [loadedDocuments, setLoadedDocuments] = useState({});

  useEffect(() => {
    if (user) {
      fetchDatabase();
    }
  }, [user]);

  const fetchDatabase = () => {
    setLoading(true);
    const requestOptions = {
      method: 'GET',
      mode: 'cors',
      headers: {'Content-Type': 'application/json'}
    };
    
    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/db/inspect", requestOptions)
      .then(response => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then(res => {
        console.log('Database inspect response:', res);
        console.log('Response status:', res.status, 'Type:', typeof res.status);
        console.log('Has data:', !!res.data);
        console.log('Has collections:', !!res.data?.collections);
        console.log('Collections array:', res.data?.collections);
        
        if ((res.status === 200 || res.status === "200" || String(res.status) === "200") && res.data && Array.isArray(res.data.collections)) {
          setDatabaseName(res.data.database_name || '');
          const collectionsData = res.data.collections.map(coll => ({
            id: `collection:${coll.name}`,
            name: coll.name,
            count: coll.count,
            type: 'Collection',
            loadOnExpand: true,
            collectionName: coll.name,
            children: []
          }));
          console.log('Setting collections:', collectionsData);
          setCollections(collectionsData);
        } else {
          console.log('Invalid response structure:', res);
          console.log('Status check:', res.status === 200, res.status === "200", String(res.status) === "200");
          console.log('Data check:', !!res.data);
          console.log('Collections check:', Array.isArray(res.data?.collections));
          setCollections([]);
        }
        setLoading(false);
      })
      .catch(error => {
        console.error('Error fetching database:', error);
        setCollections([]);
        setLoading(false);
      });
  };

  const loadCollectionDocuments = async (node) => {
    if (loadedDocuments[node.collectionName]) {
      return; // Already loaded
    }

    // Mark as loading
    setCollections(prev => prev.map(coll => 
      coll.id === node.id ? { ...coll, loading: true } : coll
    ));

    try {
      const requestOptions = {
        method: 'GET',
        mode: 'cors',
        headers: {'Content-Type': 'application/json'}
      };
      
      const response = await fetch(
        (process.env.NEXT_PUBLIC_SERVER_URL || "") + `/backend/db/collection/${node.collectionName}?limit=20`,
        requestOptions
      );
      
      const res = await response.json();
      
      console.log('Collection documents response:', res);
      
      if ((res.status === 200 || res.status === "200" || String(res.status) === "200") && res.data && res.data.documents) {
        const documents = res.data.documents.map((doc, index) => {
          const docId = doc._id?.$oid || doc._id || `doc_${index}`;
          return {
            id: `doc:${node.collectionName}:${docId}`,
            name: `_id: ${docId.substring(0, 24)}${docId.length > 24 ? '...' : ''}`,
            type: 'Document',
            docId: docId,
            document: doc,
            children: documentToNodes(doc, docId)
          };
        });

        // Cache loaded documents
        setLoadedDocuments(prev => ({
          ...prev,
          [node.collectionName]: documents
        }));

        // Update collection with documents
        console.log('Updating collection with documents:', documents.length, 'documents');
        setCollections(prev => prev.map(coll => 
          coll.id === node.id 
            ? { ...coll, children: documents, loading: false }
            : coll
        ));
      } else {
        console.log('Invalid response structure for documents:', res);
        setCollections(prev => prev.map(coll => 
          coll.id === node.id ? { ...coll, loading: false } : coll
        ));
      }
    } catch (error) {
      console.error('Error loading documents:', error);
      setCollections(prev => prev.map(coll => 
        coll.id === node.id ? { ...coll, loading: false } : coll
      ));
    }
  };

  const toggleNode = (nodeId) => {
    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeId)) {
        newSet.delete(nodeId);
      } else {
        newSet.add(nodeId);
      }
      return newSet;
    });
  };

  const handleRefresh = () => {
    setExpandedNodes(new Set());
    setLoadedDocuments({});
    fetchDatabase();
  };

  if (isLoading || !user) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <Head>
        <title>MongoDB Inspector - Collections Transformer</title>
      </Head>
      <main>
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h1 style={{ margin: 0 }}>MongoDB Inspector</h1>
            <button
              onClick={handleRefresh}
              disabled={loading}
              style={{
                padding: '6px 12px',
                backgroundColor: 'white',
                color: 'black',
                border: '1px solid black',
                borderRadius: '5px',
                cursor: loading ? 'not-allowed' : 'pointer',
                fontSize: '1rem',
                opacity: loading ? 0.6 : 1
              }}
              onMouseEnter={(e) => {
                if (!loading) e.target.style.backgroundColor = '#f0f0f0';
              }}
              onMouseLeave={(e) => {
                if (!loading) e.target.style.backgroundColor = 'white';
              }}
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>
          <hr/>
          
          {databaseName && (
            <div style={{ marginBottom: '1rem', fontFamily: 'monospace', fontSize: '0.9rem' }}>
              <strong>Database:</strong> {databaseName}
            </div>
          )}

          <div style={{ 
            border: '1px solid #ddd', 
            borderRadius: '5px', 
            padding: '15px',
            backgroundColor: '#fafafa',
            minHeight: '200px'
          }}>
            {collections.length === 0 && !loading ? (
              <div style={{ color: '#666', fontStyle: 'italic' }}>No collections found</div>
            ) : (
              collections.map((collection) => (
                <TreeNode
                  key={collection.id}
                  node={collection}
                  level={0}
                  expandedNodes={expandedNodes}
                  onToggle={toggleNode}
                  onLoadChildren={loadCollectionDocuments}
                />
              ))
            )}
          </div>
        </div>
      </main>
    </>
  )
}

export default withAuth(DB)
