// frontend/src/pages/RegisterPage.js
import React, { useState } from 'react';
import axios from 'axios'; // Importe o axios
import { useNavigate } from 'react-router-dom'; // Importe useNavigate para redirecionamento

function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(''); // Estado para mensagens de erro
  const [success, setSuccess] = useState(''); // Estado para mensagens de sucesso
  const navigate = useNavigate(); // Hook para navegação programática

  const handleSubmit = async (e) => {
    e.preventDefault(); // Previne o recarregamento da página

    setError(''); // Limpa erros anteriores
    setSuccess(''); // Limpa mensagens de sucesso anteriores

    try {
      // Faz a requisição POST para o endpoint de registro do seu backend
      const response = await axios.post('http://localhost:8000/users/', {
        email: email,
        password: password
      });

      console.log('Registro bem-sucedido:', response.data);
      setSuccess('Usuário registrado com sucesso! Redirecionando para o login...');
      setEmail(''); // Limpa os campos
      setPassword('');

      // Redireciona para a página de login após 2 segundos
      setTimeout(() => {
        navigate('/login'); 
      }, 2000);

    } catch (err) {
      console.error('Erro no registro:', err.response ? err.response.data : err.message);
      // err.response?.data?.detail é onde o FastAPI coloca mensagens de erro de validação
      setError(err.response?.data?.detail || 'Erro ao registrar. Tente novamente.');
    }
  };

  return (
    <div>
      <h2>Registro</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>} {/* Exibe mensagens de erro */}
      {success && <p style={{ color: 'green' }}>{success}</p>} {/* Exibe mensagens de sucesso */}
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
        <button type="submit">Registrar</button>
      </form>
      <p>Já tem uma conta? <a href="/login">Faça login aqui</a></p>
    </div>
  );
}

export default RegisterPage;