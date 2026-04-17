// client/src/_components/radioList.js
import React from 'react';

const RadioList = ({ items, name, selectedId, onChange, getLabel }) => (
  <div>
    {items.map(item => (
      <label key={item._id || item.id} 
        style={{ 
            display: 'block', 
            marginBottom: '0px',
            fontSize: 'small'
        }}>
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
);

export default RadioList;

