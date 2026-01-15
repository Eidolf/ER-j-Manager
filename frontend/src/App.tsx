import { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { api } from './api/client';

function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const res = await api.post('/login', formData);
      const newToken = res.data.access_token;

      localStorage.setItem('token', newToken);
      setToken(newToken);
    } catch {
      alert('Login failed');
    }
  };

  if (!token) {
    return (
      <div className="min-h-screen bg-cyber-black flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-cyber-card p-8 rounded-xl border border-gray-800 shadow-2xl neon-border">
          <h1 className="text-3xl font-bold text-center mb-8 neon-text">System Access</h1>
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Username</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                className="w-full bg-cyber-dark border border-gray-700 rounded p-3 text-white focus:border-cyber-neon outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full bg-cyber-dark border border-gray-700 rounded p-3 text-white focus:border-cyber-neon outline-none"
              />
            </div>
            <button className="w-full py-3 bg-cyber-neon text-cyber-black font-bold rounded hover:bg-cyber-neon/80 transition-all">
              Initialize Session
            </button>
          </form>
        </div>
      </div>
    );
  }

  return <Dashboard />;
}

export default App;
