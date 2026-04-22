'use client'
 
import Link from 'next/link';
import { dateFromObjectId } from '@/lib/date';

const AgentList = ({
  user_id,
  agents=[{
    _id:"Loading...",
    name:" "}], 
  onDeleteHandler
}) => {
  agents.sort(function(a,b){
    if ((a!= null) && (b != null)){
      let a_date = 'created_at' in a ? new Date(a['created_at']) : (("_id" in a) ? dateFromObjectId(a._id) : "")
      let b_date = 'created_at' in b ? new Date(b['created_at']) : (("_id" in b) ? dateFromObjectId(b._id) : "")
      return b_date - a_date;
    } else {
      return 0
    }
  });

  return (
    <div className="ws-table-wrap ws-table-wrap--agents">
    <table id="agents" className="ws-table ws-table--agents">
    <thead>
      <tr>
        <th>Name</th>
        <th>Description</th>
        <th>Created</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {agents.map(function(agent) {
        if (agent!= null){
          return (
            <tr key={"agent-" + (agent._id != undefined ? agent._id : "")}>
              <td title={agent.name && agent.name.length > 0 ? agent.name : "* Untitled *"}>
                { agent.name && agent.name.length>0 ? agent.name : "* Untitled *" }
              </td>
              <td className="agent-description-cell" title={agent.description || ""}>
                <span className="agent-description-text">
                  { agent.description || "" }
                </span>
              </td>
              <td>
                { 'created_at' in agent ? (new Date(agent['created_at']).toLocaleString()) : (("_id" in agent) ? dateFromObjectId(agent._id).toLocaleString() : "") }
              </td>
              <td className="agent-actions-cell">
              { 'owner' in agent && agent.owner == user_id ? (
                <button className="ws-btn ws-btn--danger agent-delete-btn" onClick={() => onDeleteHandler(agent)}>
                  Delete
                </button>
              ) : (
                <></>
              )}

              </td>
            </tr>
          )
        } else {
          return
        }
      })}
    </tbody>
    </table>
    </div>
  );
}

export default AgentList;
