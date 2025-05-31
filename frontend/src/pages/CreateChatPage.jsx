// frontend/src/pages/CreateChatPage.jsx

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import Header from "../components/layout/Header";
import { getAccessToken } from "../assets/auth";
import "./CreateChatPage.css";

const CreateChatPage = () => {
  const [chatName, setChatName] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      const token = await getAccessToken();
      await axios.post(
        "http://localhost:8000/api/chats/create/",
        { name: chatName },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      navigate("/"); // Redirect to the main page
    } catch (err) {
      console.error("Error creating chat:", err);
      setError("Failed to create chat. Please try again.");
    }
  };

  return (
    <>
      <Header />
      <div className="app-container page-container create-chat-page">
        <div className="create-chat-card">
          <h2>Create a New Chat</h2>
          {error && <p className="error-message">{error}</p>}
          <form onSubmit={handleSubmit} className="create-chat-form">
            <div className="form-group">
              <label htmlFor="chatName">Chat Name</label>
              <input
                type="text"
                id="chatName"
                value={chatName}
                onChange={(e) => setChatName(e.target.value)}
                required
                className="create-chat-input"
              />
            </div>
            <button type="submit" className="btn-primary create-chat-button">
              Create Chat
            </button>
          </form>
        </div>
      </div>
    </>
  );
};

export default CreateChatPage;
