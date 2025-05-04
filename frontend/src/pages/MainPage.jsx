import React from 'react';
import {useState, useEffect} from 'react';
import axios from 'axios';
import { getAccessToken, clearTokens} from '../assets/auth';
import { useNavigate } from 'react-router';
const MainPage = () => {
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    // useEffect(() => {
    //     const getMessage = async () => {
    //         const token = getAccessToken(); 
    //         try {
    //             const token = getAccessToken(); 
    //             const response = await axios.get('http://localhost:8000/home', {
    //                 headers: {
    //                     Authorization: `Bearer ${token}`,
    //                 },
    //             });
        
    //             if (response.status === 200) {
    //                 setMessage(response.data.message);
    //             }
    //         } catch (error) {
    //             console.error('Error fetching protected resource:', error);
    //             setMessage('Failed to fetch message');
    //         }
    
    //     };
    //     getMessage();
    // }, []);

    const logout = () => {
        clearTokens(); // Clear tokens from storage
        navigate('/login'); // Redirect to the login page
    }

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <h1>Hello</h1>
            <button onClick={logout}>Log out</button>
        </div>
    );
};

export default MainPage;