import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminIntegrations = () => {
  const [integrationStatus, setIntegrationStatus] = useState({});
  const [apiKeys, setApiKeys] = useState([]);
  const [newApiKey, setNewApiKey] = useState({
    service: 'stripe',
    key_name: 'secret_key',
    key_value: '',
    environment: 'test'
  });

  const fetchIntegrationStatus = async () => {
    try {
      const response = await axios.get(`${API}/integration-status`);
      setIntegrationStatus(response.data);
    } catch (err) {
      console.error('Failed to fetch integration status:', err);
    }
  };

  const fetchApiKeys = async () => {
    try {
      const response = await axios.get(`${API}/api-keys`);
      setApiKeys(response.data);
    } catch (err) {
      console.error('Failed to fetch API keys:', err);
    }
  };

  const createApiKey = async () => {
    try {
      await axios.post(`${API}/api-keys`, newApiKey);
      setNewApiKey({
        service: 'stripe',
        key_name: 'secret_key',
        key_value: '',
        environment: 'test'
      });
      fetchApiKeys();
      fetchIntegrationStatus();
      alert('API key saved successfully!');
    } catch (err) {
      alert('Failed to save API key: ' + (err.response?.data?.detail || err.message));
    }
  };

  const deleteApiKey = async (keyId) => {
    if (window.confirm('Are you sure you want to delete this API key?')) {
      try {
        await axios.delete(`${API}/api-keys/${keyId}`);
        fetchApiKeys();
        fetchIntegrationStatus();
      } catch (err) {
        alert('Failed to delete API key: ' + (err.response?.data?.detail || err.message));
      }
    }
  };

  useEffect(() => {
    fetchIntegrationStatus();
    fetchApiKeys();
  }, []);

  return (
    <div className="integrations-tab">
      <h3>🔗 Payment & Communication Setup</h3>
      
      {/* Integration Status Cards */}
      <div className="integration-status">
        <div className={`status-card ${integrationStatus.stripe?.configured ? 'connected' : 'disconnected'}`}>
          <h4>💳 Stripe Payments</h4>
          <p className="status">{integrationStatus.stripe?.configured ? 'Connected' : 'Not Connected'}</p>
          {integrationStatus.stripe?.test_mode && <span className="test-badge">Test Mode</span>}
        </div>
        <div className={`status-card ${integrationStatus.twilio?.configured ? 'connected' : 'disconnected'}`}>
          <h4>📱 Twilio SMS</h4>
          <p className="status">{integrationStatus.twilio?.configured ? 'Connected' : 'Not Connected'}</p>
          {integrationStatus.twilio?.from_number && <p className="detail">From: {integrationStatus.twilio.from_number}</p>}
        </div>
        <div className={`status-card ${integrationStatus.sendgrid?.configured ? 'connected' : 'disconnected'}`}>
          <h4>📧 SendGrid Email</h4>
          <p className="status">{integrationStatus.sendgrid?.configured ? 'Connected' : 'Not Connected'}</p>
          {integrationStatus.sendgrid?.from_email && <p className="detail">From: {integrationStatus.sendgrid.from_email}</p>}
        </div>
      </div>

      {/* API Key Management */}
      <div className="api-key-management">
        <h4>🔑 API Key Management</h4>
        
        <div className="add-api-key">
          <h5>Add New API Key</h5>
          <div className="api-key-form">
            <select
              value={newApiKey.service}
              onChange={(e) => {
                const service = e.target.value;
                let keyName = 'secret_key';
                if (service === 'twilio') keyName = 'account_sid';
                if (service === 'sendgrid') keyName = 'api_key';
                setNewApiKey({...newApiKey, service, key_name: keyName});
              }}
            >
              <option value="stripe">Stripe</option>
              <option value="twilio">Twilio</option>
              <option value="sendgrid">SendGrid</option>
            </select>
            
            <select
              value={newApiKey.key_name}
              onChange={(e) => setNewApiKey({...newApiKey, key_name: e.target.value})}
            >
              {newApiKey.service === 'stripe' && (
                <option value="secret_key">Secret Key</option>
              )}
              {newApiKey.service === 'twilio' && (
                <>
                  <option value="account_sid">Account SID</option>
                  <option value="auth_token">Auth Token</option>
                  <option value="from_number">From Number</option>
                </>
              )}
              {newApiKey.service === 'sendgrid' && (
                <>
                  <option value="api_key">API Key</option>
                  <option value="from_email">From Email</option>
                </>
              )}
            </select>
            
            <input
              type="text"
              placeholder="Enter API key or value"
              value={newApiKey.key_value}
              onChange={(e) => setNewApiKey({...newApiKey, key_value: e.target.value})}
            />
            
            <select
              value={newApiKey.environment}
              onChange={(e) => setNewApiKey({...newApiKey, environment: e.target.value})}
            >
              <option value="test">Test</option>
              <option value="production">Production</option>
            </select>
            
            <button onClick={createApiKey} className="save-api-key-btn">
              Save API Key
            </button>
          </div>
        </div>

        {/* Existing API Keys */}
        <div className="existing-keys">
          <h5>Configured API Keys</h5>
          {apiKeys.length > 0 ? (
            <div className="keys-list">
              {apiKeys.map(key => (
                <div key={key.id} className="key-item">
                  <div className="key-info">
                    <span className="service-badge">{key.service}</span>
                    <span className="key-name">{key.key_name}</span>
                    <span className="key-value">{key.key_value}</span>
                    <span className={`env-badge ${key.environment}`}>{key.environment}</span>
                  </div>
                  <button 
                    onClick={() => deleteApiKey(key.id)}
                    className="delete-key-btn"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-keys">No API keys configured yet. Add keys above to enable integrations.</p>
          )}
        </div>

        {/* Setup Instructions */}
        <div className="setup-instructions">
          <h5>📋 Setup Instructions</h5>
          <div className="instructions-grid">
            <div className="instruction-card">
              <h6>💳 Stripe Setup</h6>
              <ol>
                <li>Visit Stripe Dashboard at dashboard.stripe.com/apikeys</li>
                <li>Copy your Secret Key (sk_test_... for testing)</li>
                <li>Add it above as Stripe Secret Key</li>
              </ol>
            </div>
            <div className="instruction-card">
              <h6>📱 Twilio Setup</h6>
              <ol>
                <li>Visit Twilio Console at console.twilio.com</li>
                <li>Add Account SID, Auth Token, and From Number</li>
                <li>Verify your phone number first</li>
              </ol>
            </div>
            <div className="instruction-card">
              <h6>📧 SendGrid Setup</h6>
              <ol>
                <li>Visit SendGrid API Keys at app.sendgrid.com/settings/api_keys</li>
                <li>Create new API key with full access</li>
                <li>Add API key and verified sender email</li>
              </ol>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminIntegrations;