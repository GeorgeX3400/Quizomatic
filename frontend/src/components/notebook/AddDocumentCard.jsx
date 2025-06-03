import React from 'react';
import './AddDocumentCard.css';

const AddDocumentCard = ({ onClick }) => {
  return (
    <div className="add-document-card" onClick={onClick}>
      <h3>+ Add Document</h3>
    </div>
  );
};

export default AddDocumentCard;
