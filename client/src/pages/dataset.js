'use client'

import Head from 'next/head'
import React, { useEffect, useState } from 'react'
import { useAuth } from "@/_contexts/AuthContext"
import { withAuth } from "@/_components/withAuth"
import { useRouter } from 'next/navigation'
import FileUploader from '../_components/fileUploader'
import StatusBox from '@/_components/statusBox'

const DatasetPage = () => {
  const { user } = useAuth()
  const title = "Dataset — Collections Transformer"

  const [text_file, setTextFile] = useState(null)
  const [image_files, setImageFiles] = useState(null)
  const [text_image_file, setTextImageFile] = useState(null)
  const [dataset_name, setDatasetName] = useState("")
  const [dataset_type, setDatasetType] = useState("text")
  const [image_upload_type, setImageType] = useState("image_file")
  const [csvData, setCsvData] = useState([])
  const [uploadStatus, setUploadStatus] = useState("")
  const router = useRouter()

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!dataset_name.trim()) return

    const data = new FormData()
    data.append('dataset_name', dataset_name)

    if (dataset_type.includes('text') && text_file != null) {
      setUploadStatus("Uploading data…")
      data.append('text_file', text_file)
    }

    if (dataset_type.includes('image') && image_files != null) {
      if (image_upload_type === 'image_file') {
        setUploadStatus(image_files.length > 1000
          ? "Uploading data (This may take 5–10 minutes for 1000+ images)"
          : "Uploading data…")
        for (let f in image_files) data.append('image_file', image_files[f])
      } else {
        setUploadStatus(csvData.length > 1000
          ? "Uploading data (This may take 5–10 minutes for 1000+ images)"
          : "Uploading data…")
        data.append('image_file', image_files)
      }
    }

    if (dataset_type === 'textimage' && text_image_file != null && image_upload_type === 'image_link') {
      setUploadStatus(csvData.length > 1000
        ? "Uploading data (This may take 5–10 minutes for 1000+ images)"
        : "Uploading data…")
      data.append('text_image_file', text_image_file)
    }

    const requestOptions = { method: 'POST', mode: 'no-cors', headers: { 'Content-Type': 'application/json' }, body: data }

    const params = dataset_type === 'text'
      ? new URLSearchParams({ owner_id: user.user_id || user.sub, dataset_type })
      : new URLSearchParams({ owner_id: user.user_id || user.sub, dataset_type, image_upload_type })

    fetch((process.env.NEXT_PUBLIC_SERVER_URL || "") + "/backend/dataset_new?" + params, requestOptions)
      .then(() => {
        setUploadStatus("Upload complete!")
        router.push("/")
      })
  }

  const TYPE_OPTIONS = [
    { value: 'text',      icon: 'article',    label: 'Text',             desc: 'CSV with a text column' },
    { value: 'image',     icon: 'image',       label: 'Image',            desc: 'Image files or CSV with image URLs' },
    { value: 'textimage', icon: 'photo_library', label: 'Text + Image',  desc: 'Paired text and image data' },
  ]

  const IMG_SOURCE_OPTIONS = [
    { value: 'image_file', icon: 'upload_file', label: 'Image files',  desc: 'Upload .jpg/.png files directly (max 20 MB each)' },
    { value: 'image_link', icon: 'link',         label: 'Image links',  desc: 'CSV with a column of image URLs' },
  ]

  const compressing = uploadStatus === 'Compressing images…'

  return (
    <>
      <Head><title>{title}</title></Head>
      <main>
        <div className="container">

          {/* Hero — full width, same as home/newagent */}
          <section className="home-hero" style={{ marginBottom: '1.2rem' }}>
            <p className="home-kicker">Collections Management</p>
            <h1>Dataset</h1>
            <p className="home-subtitle">
              Ingest text, image, or multimodal collections into the platform. Datasets power every agent analysis run.
            </p>
          </section>

          <div className="agent-shell">

            {/* Step 1 — Identity */}
            <section className="agent-card">
              <div className="agent-card-header">
                <span className="agent-card-icon material-symbols-outlined">drive_file_rename_outline</span>
                <div>
                  <h2 className="agent-card-title">Dataset Name</h2>
                  <p className="agent-card-subtitle">Name the dataset so it is easy to find in your workspace.</p>
                </div>
              </div>
              <div className="agent-field">
                <label className="agent-label">Name</label>
                <input
                  type="text"
                  className="agent-input"
                  value={dataset_name}
                  onChange={e => setDatasetName(e.target.value)}
                  placeholder="e.g. V&A Paintings 2024"
                />
              </div>
            </section>

            {/* Step 2 — Dataset type */}
            <section className="agent-card">
              <div className="agent-card-header">
                <span className="agent-card-icon material-symbols-outlined">category</span>
                <div>
                  <h2 className="agent-card-title">Dataset Type</h2>
                  <p className="agent-card-subtitle">Choose the modality that describes your source material.</p>
                </div>
              </div>
              <div className="agent-field">
                <div className="ds-type-grid">
                  {TYPE_OPTIONS.map(opt => (
                    <button
                      key={opt.value}
                      type="button"
                      className={`ds-type-card${dataset_type === opt.value ? ' ds-type-card--active' : ''}`}
                      onClick={() => setDatasetType(opt.value)}
                    >
                      <span className="material-symbols-outlined ds-type-icon">{opt.icon}</span>
                      <span className="ds-type-label">{opt.label}</span>
                      <span className="ds-type-desc">{opt.desc}</span>
                    </button>
                  ))}
                </div>
              </div>
            </section>

            {/* Step 3 — Upload */}
            <section className="agent-card">
              <div className="agent-card-header">
                <span className="agent-card-icon material-symbols-outlined">upload</span>
                <div>
                  <h2 className="agent-card-title">Upload Files</h2>
                  <p className="agent-card-subtitle">Provide the source files for the selected dataset type.</p>
                </div>
              </div>

              {/* TEXT only */}
              {dataset_type === 'text' && (
                <div className="agent-field">
                  <label className="agent-label">Text CSV</label>
                  <div className="ds-note-box">
                    <span className="material-symbols-outlined ds-note-icon">info</span>
                    <ul className="ds-note-list">
                      <li>CSV must include a column named <code>text</code></li>
                      <li>Optional: include an <code>object_id</code> column for reference IDs</li>
                    </ul>
                  </div>
                  <FileUploader
                    onFileSelectSuccess={file => setTextFile(file)}
                    onFileSelectError={({ error }) => alert(error)}
                    dataset_type="text"
                  />
                </div>
              )}

              {/* IMAGE only */}
              {dataset_type === 'image' && (
                <div className="agent-field">
                  <label className="agent-label">Image source</label>
                  <div className="ds-source-grid">
                    {IMG_SOURCE_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        type="button"
                        className={`ds-source-card${image_upload_type === opt.value ? ' ds-source-card--active' : ''}`}
                        onClick={() => setImageType(opt.value)}
                      >
                        <span className="material-symbols-outlined">{opt.icon}</span>
                        <span className="ds-source-label">{opt.label}</span>
                        <span className="ds-source-desc">{opt.desc}</span>
                      </button>
                    ))}
                  </div>

                  {image_upload_type === 'image_link' && (
                    <div className="ds-note-box" style={{ marginTop: '0.75rem' }}>
                      <span className="material-symbols-outlined ds-note-icon">info</span>
                      <ul className="ds-note-list">
                        <li>CSV must include a column named <code>image</code> with the image URLs</li>
                        <li>Optional: include an <code>object_id</code> column</li>
                      </ul>
                    </div>
                  )}

                  <FileUploader
                    onFileSelectSuccess={file => setImageFiles(file)}
                    onFileSelectError={({ error }) => alert(error)}
                    onFileCompressStart={() => setUploadStatus('Compressing images…')}
                    onFileCompressEnd={() => setUploadStatus('Compression finished! Ready to create dataset.')}
                    dataset_type="image"
                    image_upload_type={image_upload_type}
                    setCsvData={setCsvData}
                  />
                </div>
              )}

              {/* TEXT + IMAGE */}
              {dataset_type === 'textimage' && (
                <div className="agent-field">
                  <label className="agent-label">Upload source</label>
                  <div className="ds-source-grid">
                    {IMG_SOURCE_OPTIONS.map(opt => (
                      <button
                        key={opt.value}
                        type="button"
                        className={`ds-source-card${image_upload_type === opt.value ? ' ds-source-card--active' : ''}`}
                        onClick={() => setImageType(opt.value)}
                      >
                        <span className="material-symbols-outlined">{opt.icon}</span>
                        <span className="ds-source-label">{opt.label}</span>
                        <span className="ds-source-desc">{opt.desc}</span>
                      </button>
                    ))}
                  </div>

                  {image_upload_type === 'image_file' ? (
                    <>
                      <label className="agent-label" style={{ marginTop: '1rem' }}>Image files</label>
                      <FileUploader
                        onFileSelectSuccess={file => setImageFiles(file)}
                        onFileSelectError={({ error }) => alert(error)}
                        onFileCompressStart={() => setUploadStatus('Compressing images…')}
                        onFileCompressEnd={() => setUploadStatus('Compression finished! Ready to create dataset.')}
                        dataset_type="image"
                        image_upload_type={image_upload_type}
                        setCsvData={setCsvData}
                      />

                      <label className="agent-label" style={{ marginTop: '1rem' }}>Text CSV</label>
                      <div className="ds-note-box">
                        <span className="material-symbols-outlined ds-note-icon">info</span>
                        <ul className="ds-note-list">
                          <li>CSV must include a column named <code>text</code></li>
                          <li>Include a column named <code>filename</code> (without extension) to match images to text rows</li>
                          <li>Without a <code>filename</code> column, pairs are matched by upload order</li>
                          <li>Optional: include an <code>object_id</code> column</li>
                        </ul>
                      </div>
                      <FileUploader
                        onFileSelectSuccess={file => setTextFile(file)}
                        onFileSelectError={({ error }) => alert(error)}
                        dataset_type="text"
                      />
                    </>
                  ) : (
                    <>
                      <div className="ds-note-box" style={{ marginTop: '0.75rem' }}>
                        <span className="material-symbols-outlined ds-note-icon">info</span>
                        <ul className="ds-note-list">
                          <li>CSV must include a column named <code>text</code> and a column named <code>image</code> with image URLs</li>
                          <li>Optional: include an <code>object_id</code> column</li>
                        </ul>
                      </div>
                      <FileUploader
                        onFileSelectSuccess={file => setTextImageFile(file)}
                        onFileSelectError={({ error }) => alert(error)}
                        onFileCompressStart={() => setUploadStatus('Compressing images…')}
                        onFileCompressEnd={() => setUploadStatus('Compression finished! Ready to create dataset.')}
                        dataset_type="textimage"
                        image_upload_type={image_upload_type}
                        setCsvData={setCsvData}
                      />
                    </>
                  )}
                </div>
              )}
            </section>

            {/* Submit */}
            <section className="agent-submit-row">
              <button
                className="agent-submit-btn"
                onClick={handleSubmit}
                disabled={compressing || !dataset_name.trim()}
              >
                <span className="material-symbols-outlined">add_circle</span>
                {compressing ? 'Compressing…' : 'Create Dataset'}
              </button>
              {uploadStatus && uploadStatus !== 'Compressing images…' && (
                <p className="agent-submit-note">{uploadStatus}</p>
              )}
              {compressing && (
                <p className="agent-submit-note">
                  <span className="spinner-border" style={{ marginRight: '0.4rem' }} />
                  {uploadStatus}
                </p>
              )}
            </section>

          </div>{/* /agent-shell */}
        </div>
        <StatusBox text={uploadStatus} />
      </main>
    </>
  )
}

export default withAuth(DatasetPage)
