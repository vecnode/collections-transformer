'use client'

import React, {useEffect, useRef, useState,  memo} from 'react'
import { Button } from 'react-bootstrap'
import DatasetModal from './datasetModal'

const ItemImage = ({
    image_data
  }) => {

    const handleShow = (e) => {
      e.preventDefault()

    }

    return (
        <>
        <div className="item-image-container">
          <DatasetModal 
            title={"Image Viewer"}
            iconName="fullscreen"
            canCancel={false}
          >
            <img className="item-image" src={image_data} />
          </DatasetModal>
          <img className="item-image-thumbnail" src={image_data} />
        </div>
        </>
    )
        
}

export default memo(ItemImage)
  
