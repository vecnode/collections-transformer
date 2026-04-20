'use client'

import React, { useEffect, useState, memo, useCallback } from 'react'
import DatasetModal from './datasetModal'

const ItemImage = ({ image_data }) => {
    return (
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
    )
}

const ItemImageLoader = ({
    item_id, 
    item_storage_id
  }) => {

    const [loadState, setLoadState] = useState("unknown")
    const [image, setImage] = useState("")

    const getImage = useCallback((img_storage_id) => {
        const requestOptions = {
            method: 'GET',
            mode: 'cors',
            headers: {'Content-Type': 'application/json'},
        };

        setLoadState("loading")

        fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/api/v1/backend/item_image?"+ new URLSearchParams({
            item_id:item_id,
            image_storage_id:img_storage_id
        }), requestOptions)
        .then(response => response.json())
        .then(res => {
            if(res.status=="200"){
                setImage("data:image/jpeg;base64,"+ res.data)
                setLoadState("ready")
            } else {
                console.log(res['error'])
                onError(res['error'])
            }
        })
    } ,[])

    useEffect(()=>{
        getImage(item_storage_id)
    },[item_storage_id])

    return (
        <>
        {loadState != "ready" ? (
            <div className="image-placeholder">
                <div>
                    <span id={"image-loading-icon"} className="spinner-border text-primary" role="status"></span>
                </div>
            </div>
        ) : (
            <>
            <ItemImage image_data={image}/>
            </>
        ) 
        }
        </>
    )
        
}

export default memo(ItemImageLoader)
  
  