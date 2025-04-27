// src/assets/auth.js
export const storeTokens = (accessToken, refreshToken) => {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
  };

export const getAccessToken = () => {
    return sessionStorage.getItem('access_token');
};

export const getRefreshToken = () => {
    return sesionStorage.getItem('refresh_token');
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
