// frontend/src/components/DocumentUpload.jsx

import React, { useState } from "react";
import axios from "axios";
import { getAccessToken } from "../assets/auth";
import "./UploadDocumentPage.css";

export default function DocumentUpload({ chatId, onSuccess }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleFile = (e) => {
    setError("");
    setFile(e.target.files[0]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a file first.");
      return;
    }
    setLoading(true);
    try {
      const token = await getAccessToken();
      const form = new FormData();
      form.append("file", file);
      form.append("chat_id", chatId);
      form.append("name", file.name);

      const res = await axios.post("http://localhost:8000/documents/add/", form, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`,
        },
      });
      onSuccess(res.data);
    } catch (err) {
      console.error(err);
      setError("Upload failed. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="upload-form">
      <input type="file" onChange={handleFile} className="upload-input" />
      <button
        type="submit"
        disabled={!file || loading}
        className="btn-primary upload-button"
      >
        {loading ? "Uploading…" : "Upload Document"}
      </button>
      {error && <p className="error-message">{error}</p>}
    </form>
  );
}
