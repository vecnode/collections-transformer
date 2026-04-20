'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { dateFromObjectId } from '@/lib/date'

const DatasetList = ({
  user_id,
  datasets = [],
  onDeleteHandler = () => {}
}) => {
  useEffect(() => {
    datasets.sort(function (a, b) {
      let a_date = 'last_updated' in a ? new Date(a['last_updated']) : (('_id' in a) ? dateFromObjectId(a._id) : '')
      let b_date = 'last_updated' in b ? new Date(b['last_updated']) : (('_id' in b) ? dateFromObjectId(b._id) : '')
      return b_date - a_date
    })
  }, [datasets])

  return (
    <div className="ws-table-wrap">
      <table id="datasets" className="ws-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Item Count</th>
            <th>Status</th>
            <th>Availability</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {datasets
            .filter((dataset) => dataset.status != -1)
            .map(function (dataset, index) {
              return (
                <tr key={'dataset-' + (dataset._id != undefined ? dataset._id : index)}>
                  <td>
                    {dataset._id != undefined ? (
                      <Link href={'/viewdataset?dataset_id=' + dataset._id}>{dataset.name}</Link>
                    ) : null}
                  </td>
                  <td>
                    {dataset._id != undefined ? dataset['artwork_count'] : ''}
                  </td>
                  <td>
                    {dataset.status == 1 ? 'Ready' : (
                      dataset.status == 0 ? 'Processing' : 'Loading...'
                    )}
                  </td>
                  <td>
                    {('owner' in dataset && dataset.owner == user_id) &&
                    (!('users' in dataset) || ('users' in dataset && dataset.users.length == 0)) ? (
                      'Private'
                    ) : ((('users' in dataset) && (dataset.users.length > 0)) ? 'Shared' : 'Public')}
                  </td>
                  <td>
                    {'owner' in dataset && dataset.owner == user_id ? (
                      <button className="ws-btn ws-btn--danger" onClick={() => onDeleteHandler(dataset)}>
                        Delete
                      </button>
                    ) : null}
                  </td>
                </tr>
              )
            })}
        </tbody>
      </table>
    </div>
  )
}

export default DatasetList
