import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import axios from "axios";
import "./Auth.css";

function LoginPage() {
  const [credentials, setCredentials] = useState({
    username: "",
    password: "",
  });
  const [redirect, setRedirect] = useState(false);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setCredentials((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  async function login(event) {
    event.preventDefault();
    setError(null);

    try {
      // 1. Trim whitespace
      const username = credentials.username.trim();
      const password = credentials.password;

      const response = await axios.post(
        "http://localhost:8000/token/",
        {
          username,
          password,
        },
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      // 2. Extragem access și refresh din răspuns
      const { access, refresh } = response.data;

      // 3. Salvăm exact sub cheile "access_token" și "refresh_token" în sessionStorage
      sessionStorage.setItem("access_token", access);
      sessionStorage.setItem("refresh_token", refresh);

      // 4. Redirecționăm către dashboard
      setRedirect(true);
    } catch (err) {
      console.error("Login failed:", err.response?.data || err.message);
      setError("Invalid username or password");
    }
  }

  // Dacă login-ul a fost reușit, navigăm la /dashboard
  if (redirect) {
    return <Navigate to="/dashboard" />;
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2 className="auth-title">Login</h2>
        {error && <p className="error-message">{error}</p>}
        <form onSubmit={login} className="auth-form">
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              className="auth-input"
              placeholder="Enter your username"
              value={credentials.username}
              onChange={handleChange}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              className="auth-input"
              placeholder="Enter your password"
              value={credentials.password}
              onChange={handleChange}
              required
            />
          </div>
          <button type="submit" className="auth-button">
            Login
          </button>
        </form>
        <p className="auth-footer">
          Don’t have an account?{" "}
          <Link to="/register" className="auth-link">
            Register here
          </Link>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;
