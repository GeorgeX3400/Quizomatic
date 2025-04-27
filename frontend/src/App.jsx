import { useState } from 'react'
import {BrowserRouter as Router, Routes, Route} from 'react-router'
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import MainPage from './pages/MainPage';

import './App.css'


function App() {
  const [currentPage, setCurrentPage] = useState('watches')

  const handlePage = (e) => {
    setCurrentPage(e.target.value);
  }
  

  return <Router>
    <Routes>
      <Route path='/dashboard' element={<MainPage/>}></Route>
      <Route path='/login' element={<LoginPage/>}></Route>
      <Route path='/register' element={<RegisterPage/>}></Route>
    </Routes>
  </Router>
  ;
}

export default App
