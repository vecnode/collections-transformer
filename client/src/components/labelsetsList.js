'use client'
 
import { useState, useEffect } from 'react'
import LoaderButton from './loaderButton';
import { dateFromObjectId } from '@/lib/date';
import { formatAnalyserType } from '@/lib/labels';
import Link from 'next/link'
import DatasetModal from './datasetModal';
 
const LabelsetList = ({
  user,
  labelsets=[{id:"Loading...",name:" "}], 
  onDeleteHandler=()=>{}
}) => {

  labelsets.sort(function(a,b){
    let a_date = 'last_updated' in a ? new Date(a['last_updated']) : (("_id" in a) ? dateFromObjectId(a._id) : "")
    let b_date = 'last_updated' in b ? new Date(b['last_updated']) : (("_id" in b) ? dateFromObjectId(b._id) : "")
    return b_date - a_date;
  });

  return (
    <div className="ws-table-wrap">
    <table id="Labelsets" className="ws-table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Label Type</th>
        <th>Label Count</th>
        <th>Dataset</th>
        <th>Last Updated</th>
        <th>Origin</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
    {labelsets.map(function(labelset) {
      return (
        <tr key={"labelset-" + (labelset._id != undefined ? labelset._id : "")}>
          <td>
            <Link href={"/viewdataset?" + new URLSearchParams({
              dataset_id:labelset['dataset_id'],
              labelset_id:labelset['_id']
            })}>{ labelset.name } </Link>
          </td>
          <td>
            { formatAnalyserType(labelset.label_type) } 
          </td>
          <td>
            { labelset.label_count } 
          </td>
          <td>
            { labelset.dataset_name } 
          </td>
          <td>
            { 'last_updated' in labelset ? (new Date(labelset['last_updated']).toLocaleString()) : (("_id" in labelset) ? dateFromObjectId(labelset._id).toLocaleString() : "") }
          </td>
          <td>
          { (labelset['owner'] == user.sub) && ("origin" in labelset) && (labelset.origin != "system") ? (
            user.nickname
          ) : (
            ("origin" in labelset) && (labelset.origin == "user") ? (<>Shared</>) : (<>System</>)
          )}
          </td>
          <td>
          { labelset['owner'] == user.sub ? (
              <button className="ws-btn ws-btn--danger" onClick={() => onDeleteHandler(labelset)}>
                Delete
              </button>
          ) : (
            <></>
          )}
          </td>
        </tr>
      )
    })}
    </tbody>
    </table>
    </div>
  );
}

export default LabelsetList;
