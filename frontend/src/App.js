import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link} from 'react-router-dom';
import Loginpage from './pages/Loginpage';
import Dashboardpage from './pages/Dashboardpage';
import Registerpage from './pages/Registerpage';



function App() {
  return (
    <Router>
      <nav style={{ padding: '10px', background: '#f0f0f0'}}>
        <ul style={{ listenStyleType: 'nome', margin: 0, padding: 0, display: 'flex', gap: '15px'}}>
          <li>
            <Link to='/login'>Login</Link>
          </li>
          <li>
            <Link to='/register'>Register</Link>
          </li>
          <li>
            <Link to='/dashboard'>Dashboard</Link>
          </li>
        </ul>
      </nav>

      <div style={{ padding: '20px' }}>
        <Routes>
          <Route path="/login" element={<Loginpage />} />
          <Route path="/register" element={<Registerpage />} />
          <Route path = "/dashboard" element={<Dashboardpage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;