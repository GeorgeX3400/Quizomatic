import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import axios from 'axios';
import Header from '../components/layout/Header';
import { getAccessToken } from '../assets/auth';

const CreateChatPage = () => {
    const [chatName, setChatName] = useState('');
    const [error, setError] = useState(null);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);

        try {
            const token = await getAccessToken();
            await axios.post('http://localhost:8000/chats/create/', {
                name: chatName,
            }, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            navigate('/'); // Redirect to the main page after successful creation
        } catch (err) {
            console.error('Error creating chat:', err);
            setError('Failed to create chat. Please try again.');
        }
    };

    return (
        <>
            <Header />
            <div style={{
                padding: '20px',
                backgroundColor: '#B5FCCD',
                minHeight: '100vh',
                marginTop: '60px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
            }}>
                <form onSubmit={handleSubmit} style={{
                    backgroundColor: '#7AC6D2',
                    padding: '20px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                    width: '100%',
                    maxWidth: '400px',
                }}>
                    <h2 style={{ color: '#3A59D1', textAlign: 'center' }}>Create a New Chat</h2>
                    {error && <p style={{ color: 'red', textAlign: 'center' }}>{error}</p>}
                    <div style={{ marginBottom: '15px' }}>
                        <label htmlFor="chatName" style={{ color: '#3A59D1', display: 'block', marginBottom: '5px' }}>Chat Name</label>
                        <input
                            type="text"
                            id="chatName"
                            value={chatName}
                            onChange={(e) => setChatName(e.target.value)}
                            style={{
                                width: '100%',
                                padding: '10px',
                                border: '1px solid #3D90D7',
                                borderRadius: '4px',
                                fontSize: '1em',
                            }}
                            required
                        />
                    </div>
                    <button type="submit" style={{
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
                    }}>Create Chat</button>
                </form>
            </div>
        </>
    );
};

export default CreateChatPage;