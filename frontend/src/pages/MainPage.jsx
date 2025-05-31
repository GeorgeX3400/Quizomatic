// src/pages/MainPage.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { getAccessToken, clearTokens } from '../assets/auth';
import { useNavigate, Link } from 'react-router-dom';
import Header from '../components/layout/Header';

const MainPage = () => {
  const [chats, setChats]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [chatName, setChatName]   = useState('');
  const [error, setError]         = useState(null);
  const navigate = useNavigate();

  const fetchChats = async () => {
    try {
      const token = await getAccessToken();
      const res   = await axios.get('http://localhost:8000/api/chats/', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChats(res.data);
    } catch (err) {
      console.error('Error fetching chats:', err);
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
      await axios.post('http://localhost:8000/api/chats/create/', { name: chatName }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setChatName('');
      setShowModal(false);
      fetchChats();
    } catch (err) {
      console.error('Error creating chat:', err);
      setError('Failed to create chat. Please try again.');
    }
  };

  const logout = () => {
    clearTokens();
    navigate('/login');
  };

  return (
    <>
      <Header />

      <div style={{
        padding: '20px',
        backgroundColor: '#B5FCCD',
        minHeight: '100vh',
        marginTop: '60px'
      }}>
        <button
          onClick={logout}
          style={{ display: 'block', margin: '20px auto' }}
        >
          Log out
        </button>

        <h2 style={{ color: '#3A59D1', textAlign: 'center' }}>
          Your Chats
        </h2>

        <button
          onClick={() => setShowModal(true)}
          style={{
            backgroundColor: '#3D90D7',
            color: 'white',
            padding: '10px 20px',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            margin: '20px auto',
            display: 'block',
          }}
        >
          + Add New Chat
        </button>

        {loading ? (
          <p style={{ textAlign: 'center', color: '#3D90D7' }}>Loading...</p>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '20px',
            marginTop: '20px',
          }}>
            {chats.map(chat => (
              <Link
                key={chat.id}
                to={`/chats/${chat.id}`}
                style={{ textDecoration: 'none' }}
              >
                <div style={{
                  backgroundColor: '#7AC6D2',
                  borderRadius: '8px',
                  padding: '15px',
                  boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                  textAlign: 'center',
                  cursor: 'pointer'
                }}>
                  <h3 style={{ color: '#3A59D1' }}>
                    {chat.name || 'Untitled Chat'}
                  </h3>
                  <p style={{ color: '#3D90D7' }}>
                    Created on: {new Date(chat.created_at).toLocaleDateString()}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}

        {showModal && (
          <div style={{
            position: 'fixed', top: 0, left: 0,
            width: '100vw', height: '100vh',
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            zIndex: 1000,
          }}>
            <div style={{
              backgroundColor: '#7AC6D2',
              padding: '20px',
              borderRadius: '8px',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
              width: '100%', maxWidth: '400px'
            }}>
              <h2 style={{ color: '#3A59D1', textAlign: 'center' }}>
                Create a New Chat
              </h2>
              {error && (
                <p style={{ color: 'red', textAlign: 'center' }}>
                  {error}
                </p>
              )}
              <form onSubmit={handleAddChat}>
                <div style={{ marginBottom: '15px' }}>
                  <label
                    htmlFor="chatName"
                    style={{ color: '#3A59D1', display: 'block', marginBottom: '5px' }}
                  >
                    Chat Name
                  </label>
                  <input
                    id="chatName"
                    type="text"
                    value={chatName}
                    onChange={e => setChatName(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      padding: '10px',
                      border: '1px solid #3D90D7',
                      borderRadius: '4px',
                      fontSize: '1em',
                      backgroundColor: '#fff',
                    }}
                  />
                </div>
                <button
                  type="submit"
                  style={{
                    width: '100%',
                    padding: '10px',
                    backgroundColor: '#3D90D7',
                    color: 'white',
                    fontSize: '1em',
                    fontWeight: 'bold',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    transition: 'background-color 0.3s',
                  }}
                >
                  Create Chat
                </button>
              </form>
              <button
                onClick={() => setShowModal(false)}
                style={{
                  marginTop: '10px',
                  width: '100%',
                  padding: '10px',
                  backgroundColor: '#3A59D1',
                  color: 'white',
                  fontSize: '1em',
                  fontWeight: 'bold',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  transition: 'background-color 0.3s',
                }}
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
