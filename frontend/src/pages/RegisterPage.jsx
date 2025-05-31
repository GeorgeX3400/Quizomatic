// frontend/src/pages/RegisterPage.jsx

import React, { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import axios from "axios";
import "./Auth.css";

function RegisterPage() {
  const [data, setData] = useState({
    username: "",
    password: "",
    email: "",
  });
  const [redirect, setRedirect] = useState(false);
  const [error, setError] = useState(null);

  function handleChange(e) {
    const { name, value } = e.target;
    setData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  }

  async function registerUser(event) {
    event.preventDefault();
    setError(null);
    try {
      const registerResponse = await axios.post(
        "http://localhost:8000/v2/register/",
        {
          ...data,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (registerResponse.status === 201) {
        const tokenResponse = await axios.post("http://localhost:8000/token/", {
          username: data.username,
          password: data.password,
        });

        localStorage.setItem("accessToken", tokenResponse.data.access);
        localStorage.setItem("refreshToken", tokenResponse.data.refresh);
        setRedirect(true);
      } else {
        console.error("Registration failed:", registerResponse.data);
        setError("Registration failed. Please try again.");
      }
    } catch (error) {
      console.error("Registration error:", error);
      setError("An error occurred during registration.");
    }
  }

  if (redirect) {
    return <Navigate to="/login" />;
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">Register</h2>
        {error && <p className="error-message">{error}</p>}
        <form onSubmit={registerUser} className="auth-form">
          <div className="form-group">
            <label>Username</label>
            <input
              type="text"
              name="username"
              placeholder="Enter your username"
              className="auth-input"
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              name="email"
              placeholder="Enter your email"
              className="auth-input"
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              placeholder="Create a password"
              className="auth-input"
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              name="confirm-password"
              placeholder="Confirm your password"
              className="auth-input"
              required
            />
          </div>

          <button type="submit" className="auth-button">
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
