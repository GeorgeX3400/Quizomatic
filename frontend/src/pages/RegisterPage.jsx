import React from "react";
import { Link, Navigate } from "react-router";
import { useState } from 'react';
import axios from "axios";

function RegisterPage() {
  const [data, setData] = useState({
    'username': '',
    'password': '',
    'email': '',
  });
  const [redirect, setRedirect] = useState(false);

  function handleChange(e) {
    const { name, value } = e.target;
    setData((prevData) => ({
      ...prevData,
      [name]: value
    }));
  }

  async function registerUser(event) {
    event.preventDefault(); 
    try {
      const registerResponse = await axios.post('http://localhost:8000/v2/register/', {
        ...data
      }, {
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (registerResponse.status === 201) { 
        const tokenResponse = await axios.post('http://localhost:8000/token/', {
          username: data.username,
          password: data.password
        });

        // Store the JWT tokens in localStorage
        localStorage.setItem('accessToken', tokenResponse.data.access);
        localStorage.setItem('refreshToken', tokenResponse.data.refresh);

        setRedirect(true); // Update redirect state on successful registration
      } else {
        console.error('Registration failed:', registerResponse.data);
      }
    } catch (error) {
      console.error('Registration error:', error);
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault(); 
    await registerUser(event); 
  };

  if (redirect) {
    return <Navigate to='/login/'/>;
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">Register</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              name="username"
              placeholder="Enter your username"
              className="auth-input"
              onChange={handleChange}
            />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              className="auth-input"
              onChange={handleChange}
              placeholder="Enter your email"
            />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              className="auth-input"
              onChange={handleChange}
              placeholder="Create a password"
            />
          </div>
          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              name="confirm-password"
              className="auth-input"
              placeholder="Confirm your password"
            />
          </div>
          <button className="auth-button">
            Register
          </button>
        </form>
        <p className="auth-footer">
          Already have an account?{" "}
          <Link to="/login" className="auth-link">
            Login here
          </Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;