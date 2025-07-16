// frontend/src/pages/LoginPage.js
import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); // Limpa erros anteriores

    try {
      // Faz a requisição POST para o endpoint de token/login do seu backend
      // Note o uso de URLSearchParams e o Content-Type para corresponder ao FastAPI OAuth2PasswordRequestForm
      const response = await axios.post('http://localhost:8000/token', 
        new URLSearchParams({
          username: email, // O FastAPI espera 'username' para o email/usuário
          password: password,
        }),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded' 
          }
        }
      );

      const { access_token, token_type } = response.data;

      // Armazena o token no localStorage do navegador
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('token_type', token_type); // Geralmente "bearer"

      console.log('Login bem-sucedido! Token:', access_token);
      // Redireciona para o dashboard
      navigate('/dashboard'); 

    } catch (err) {
      console.error('Erro no login:', err.response ? err.response.data : err.message);
      setError(err.response?.data?.detail || 'Email ou senha inválidos. Tente novamente.');
    }
  };

  return (
    <div>
      <h2>Login</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>} {/* Exibe mensagens de erro */}
      <form onSubmit={handleSubmit}>
        <div>
          <label>Email:</label>
          <input 
            type="email" 
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
            required 
          />
        </div>
        <div>
          <label>Senha:</label>
          <input 
            type="password" 
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
            required 
          />
        </div>
        <button type="submit">Entrar</button>
      </form>
      <p>Não tem uma conta? <a href="/register">Registre-se aqui</a></p>
    </div>
  );
}

export default LoginPage;