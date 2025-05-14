import React, { useState } from 'react';

export default function LiveVideo() {
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [conversationUrl, setConversationUrl] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLanguageChange = (e) => {
    setSelectedLanguage(e.target.value);
    setError(''); // Clear any previous errors
  };

  const handleApplyLanguage = async () => {
    if (!name.trim()) {
      setError('Please enter your name first');
      return;
    }

    setIsLoading(true);
    setError('');
    
    try {
      const response = await fetch('http://localhost:8000/start-conversation', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          language: selectedLanguage,
          person: name.trim()
        }),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`);
      }
      
      if (data.conversation_url) {
        console.log('Setting conversation URL:', data.conversation_url);
        setConversationUrl(data.conversation_url);
        setError('');
      } else if (data.error) {
        throw new Error(data.error);
      } else {
        console.error('Unexpected response format:', data);
        throw new Error('No conversation URL in response');
      }
    } catch (error) {
      console.error('Error starting conversation:', error);
      setError(error.message || 'Failed to start conversation');
      setConversationUrl('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Enter your name"
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <select 
          value={selectedLanguage}
          onChange={handleLanguageChange}
          style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
        >
          <option value="English">English</option>
          <option value="Spanish">Spanish</option>
          <option value="French">French</option>
          <option value="German">German</option>
          <option value="Urdu">Urdu</option>
          <option value="Hindi">Hindi</option>
        </select>
        <button 
          onClick={handleApplyLanguage}
          disabled={isLoading || !name.trim()}
          style={{ 
            padding: '0.5rem 1rem',
            borderRadius: '4px',
            backgroundColor: isLoading ? '#ccc' : '#007bff',
            color: 'white',
            border: 'none',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'Starting...' : 'Start Conversation'}
        </button>
      </div>

      {error && (
        <div style={{ 
          color: '#dc3545', 
          padding: '1rem', 
          marginBottom: '1rem', 
          backgroundColor: '#f8d7da',
          borderRadius: '4px',
          border: '1px solid #f5c6cb'
        }}>
          {error}
        </div>
      )}

      {conversationUrl && (
        <iframe
          src={conversationUrl}
          width="100%"
          height="600"
          frameBorder="0"
          allow="camera; microphone"
          title="Tavus Conversation"
        />
      )}
    </div>
  );
}