import React from 'react';
import { Link } from 'react-router';

const AddChatCard = () => {
    return (
        <div style={{
            backgroundColor: '#7AC6D2',
            borderRadius: '8px',
            padding: '15px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'transform 0.2s',
        }}
        onClick={() => window.location.href = '/create-chat'}>
            <h3 style={{ color: '#3A59D1' }}>+ Add New Chat</h3>
        </div>
    );
};

export default AddChatCard;