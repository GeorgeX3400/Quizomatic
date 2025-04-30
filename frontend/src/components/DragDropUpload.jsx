import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { v4 as uuidv4 } from 'uuid';
import { useAuth } from '../auth'; // Your auth context
import axios from 'axios';

const DragDropUpload = () => {
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { user } = useAuth(); // Get current user ID

  const onDrop = useCallback(async (acceptedFiles) => {
    if (!user || !user.id) return;

    try {
      const formData = new FormData();
      acceptedFiles.forEach((file) => {
        formData.append('files', file);
      });
      formData.append('user_id', user.id);

      await axios.post('/upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      alert("Files uploaded successfully!");
      navigate('/dashboard'); // Redirect to dashboard
    } catch (err) {
      setError("Failed to upload files. Please try again.");
    }
  }, [user, navigate]);

  return (
    <div style={{ border: "2px dashed #ccc", padding: "50px", textAlign: "center" }}>
      <h3>Drag & Drop Files Here</h3>
      <p>Supported formats: PDF, DOCX, TXT</p>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default DragDropUpload;
