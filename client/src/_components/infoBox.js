'use client'

import React, { useEffect, useState } from 'react'
import DatasetModal from './datasetModal'
import { AccordionItem } from 'react-bootstrap'

const InfoBox = ({
    children,
    props,
    title="",
    type="",
    tooltip=""
}) => {

    if (type=="modal") {
        return (
            <div className='info-box'>
                <div className="info_tooltip">
                    <div>{tooltip}</div>
                </div>
                <DatasetModal iconName='info' title={title} isButton={false}>{children}</DatasetModal>
            </div>
        )
    } else if (type=="accordion") {
        return (
            <div className='info-box'>
                <Accordion defaultActiveKey={[]}>
                    <Accordion.Item eventKey="0">
                        <Accordion.Header>{title}</Accordion.Header>
                        <Accordion.Body>{children}</Accordion.Body>
                    </Accordion.Item>
                </Accordion>
            </div>
        )
    } else {
        return (
            <div className='info-box'>
                <div className="info_tooltip">
                    <div>{children}</div>
                </div>
                <span className='info_icon material-symbols-outlined'>info</span>
            </div>
        )
    }
}

export default InfoBox
