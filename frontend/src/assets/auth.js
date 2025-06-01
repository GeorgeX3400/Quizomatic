import axios from 'axios';

export const storeTokens = (accessToken, refreshToken) => {
  // Salvăm accesul și refresh-ul în sessionStorage
  sessionStorage.setItem('access_token', accessToken);
  sessionStorage.setItem('refresh_token', refreshToken);
};

export const getAccessToken = async () => {
  // Citim din sessionStorage
  const accessToken = sessionStorage.getItem('access_token');
  const refreshToken = sessionStorage.getItem('refresh_token');

  if (!accessToken || !refreshToken) {
    throw new Error('No tokens available');
  }

  try {
    // Verificăm token-ul de acces
    await axios.post('http://localhost:8000/token/verify/', {
      token: accessToken,
    });
    return accessToken;
  } catch (error) {
    if (error.response && error.response.status === 401) {
      // Dacă a expirat access-ul, încercăm să dăm refresh
      try {
        const response = await axios.post('http://localhost:8000/token/refresh/', {
          refresh: refreshToken,
        });
        const newAccessToken = response.data.access;
        // Salvăm noul access token în sessionStorage
        sessionStorage.setItem('access_token', newAccessToken);
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
  return sessionStorage.getItem('refresh_token');
};

export const clearTokens = () => {
  sessionStorage.removeItem('access_token');
  sessionStorage.removeItem('refresh_token');
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
    // Salvăm noul access token (și păstrăm același refreshToken)
    storeTokens(data.access, refreshToken);
    return data.access;
  } catch (error) {
    console.error('Error refreshing token:', error);
    clearTokens();
    throw error;
  }
};
