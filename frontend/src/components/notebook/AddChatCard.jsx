import React from 'react';
import { Link } from 'react-router-dom';
import './AddChatCard.css';

const AddChatCard = () => {
  return (
    <Link to="/create-chat" className="add-chat-card">
      <h3>+ Add New Chat</h3>
    </Link>
  );
};

export default AddChatCard;
