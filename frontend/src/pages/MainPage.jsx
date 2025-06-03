// frontend/src/pages/MainPage.jsx

import React, { useState, useEffect } from "react";
import axios from "axios";
import { getAccessToken, clearTokens } from "../assets/auth";
import { useNavigate, Link } from "react-router-dom";
import Header from "../components/layout/Header";
import "./MainPage.css";

const MainPage = () => {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [chatName, setChatName] = useState("");
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const fetchChats = async () => {
    try {
      const token = await getAccessToken();
      const res = await axios.get("http://localhost:8000/api/chats/", {
        headers: { Authorization: `Bearer ${token}` },
      });
      setChats(res.data);
    } catch (err) {
      console.error("Error fetching chats:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChats();
  }, []);

  const handleAddChat = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const token = await getAccessToken();
      await axios.post(
        "http://localhost:8000/api/chats/create/",
        { name: chatName },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setChatName("");
      setShowModal(false);
      fetchChats();
    } catch (err) {
      console.error("Error creating chat:", err);
      setError("Failed to create chat. Please try again.");
    }
  };

  const logout = () => {
    clearTokens();
    navigate("/login");
  };

  return (
    <>
      <Header />

      <div className="app-container page-container mainpage-container">
        <button onClick={logout} className="logout-button">
          Log out
        </button>

        <h2 className="main-title">Your Chats</h2>

        <button
          onClick={() => setShowModal(true)}
          className="btn-primary add-chat-button"
        >
          + Add New Chat
        </button>

        {loading ? (
          <p className="loading-text">Loading...</p>
        ) : (
          <div className="chats-grid">
            {chats.map((chat) => (
              <Link
                key={chat.id}
                to={`/chats/${chat.id}`}
                className="chat-link"
              >
                <div className="chat-card">
                  <h3 className="chat-card-title">
                    {chat.name || "Untitled Chat"}
                  </h3>
                  <p className="chat-card-date">
                    Created on:{" "}
                    {new Date(chat.created_at).toLocaleDateString()}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}

        {showModal && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h2 className="modal-title">Create a New Chat</h2>
              {error && <p className="error-message">{error}</p>}
              <form onSubmit={handleAddChat} className="modal-form">
                <div className="form-group">
                  <label htmlFor="chatName">Chat Name</label>
                  <input
                    id="chatName"
                    type="text"
                    value={chatName}
                    onChange={(e) => setChatName(e.target.value)}
                    required
                    className="modal-input"
                  />
                </div>
                <button type="submit" className="btn-primary modal-create-button">
                  Create Chat
                </button>
              </form>
              <button
                onClick={() => setShowModal(false)}
                className="btn-primary modal-cancel-button"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
};

export default MainPage;
