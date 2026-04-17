// @ts-nocheck
'use client'
 
import ItemDynamicList from './itemDynamicList'
import type { Dataset, Labelset } from '@/types'

interface DatasetLabellerProps {
  dataset?: Dataset
  labelset?: Labelset
  showLabels: boolean
  enableLabelling: boolean
  onLabelsChanged: (...args: unknown[]) => void
}

const DatasetLabeller = ({
    dataset={
      id:"",
      name:"",
      artworks:[],
      dataset_type: ""
    },
    labelset={ _id: '', labels: [] },
    showLabels,
    enableLabelling,
    onLabelsChanged
  }: DatasetLabellerProps) => {

    return (

        <div className="container">
            <ItemDynamicList 
              labelset_id={labelset._id}
              labelset_type={labelset.label_type}
              dataset={dataset} 
              labelset={labelset}
              examples={[]}
              predictions={[]} 
              sample_ids={[]} 
              enableLabelling={enableLabelling}
              showLabels={showLabels}
              showPredictions={false}
              showExamples={false}
              showRobotItems={false}
              onLabelsChanged={onLabelsChanged}
            />

            {
  }

          </div>);
          
        
}
  
export default DatasetLabeller