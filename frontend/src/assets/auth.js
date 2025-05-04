import axios from 'axios';

export const storeTokens = (accessToken, refreshToken) => {
  localStorage.setItem('access_token', accessToken);
  localStorage.setItem('refresh_token', refreshToken);
};

export const getAccessToken = async () => {
  const accessToken = localStorage.getItem('accessToken');
  const refreshToken = localStorage.getItem('refreshToken');

  if (!accessToken || !refreshToken) {
    throw new Error('No tokens available');
  }

  try {
    // Verify the access token
    await axios.post('http://localhost:8000/token/verify/', {
      token: accessToken,
    });
    return accessToken;
  } catch (error) {
    if (error.response && error.response.status === 401) {
      // Access token is invalid, try refreshing it
      try {
        const response = await axios.post('http://localhost:8000/token/refresh/', {
          refresh: refreshToken,
        });
        const newAccessToken = response.data.access;
        localStorage.setItem('access_token', newAccessToken);
        return newAccessToken;
      } catch (refreshError) {
        console.error('Error refreshing token:', refreshError);
        throw new Error('Unable to refresh token');
      }
    } else {
      console.error('Error verifying token:', error);
      throw new Error('Token verification failed');
    }
  }
};

export const getRefreshToken = () => {
  return localStorage.getItem('refresh_token');
};

export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new Error('No refresh token available');

  try {
    const response = await fetch('http://localhost:8000/token/refresh/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    const data = await response.json();
    storeTokens(data.access, refreshToken);
    return data.access;
  } catch (error) {
    console.error('Error refreshing token:', error);
    clearTokens();
    throw error;
  }
};
