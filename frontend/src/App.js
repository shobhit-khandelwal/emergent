import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import AdminIntegrations from './AdminIntegrations';
import AdminCRM from './AdminCRM';
import AdminLocations from './AdminLocations';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Utility to generate session ID
const getSessionId = () => {
  let sessionId = localStorage.getItem('sessionId');
  if (!sessionId) {
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('sessionId', sessionId);
  }
  return sessionId;
};

// Funnel tracking utility
const trackEvent = async (eventType, metadata = {}) => {
  try {
    await axios.post(`${API}/funnel/track`, {
      session_id: getSessionId(),
      event_type: eventType,
      metadata
    });
  } catch (err) {
    console.error('Failed to track event:', err);
  }
};

const PromoBanner = ({ banner, onClose }) => {
  if (!banner) return null;

  return (
    <div 
      className="promo-banner"
      style={{
        backgroundColor: banner.background_color,
        color: banner.text_color
      }}
    >
      <div className="banner-content">
        <strong>{banner.title}</strong>
        <span>{banner.message}</span>
        {banner.cta_text && (
          <button 
            className="banner-cta"
            onClick={() => {
              if (banner.cta_url && banner.cta_url !== '#') {
                window.location.href = banner.cta_url;
              }
              trackEvent('banner_clicked', { banner_id: banner.id });
            }}
          >
            {banner.cta_text}
          </button>
        )}
      </div>
      <button className="banner-close" onClick={() => onClose(banner.id)}>×</button>
    </div>
  );
};

const AdminPortal = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [analytics, setAnalytics] = useState({});
  const [content, setContent] = useState([]);
  const [banners, setBanners] = useState([]);
  const [integrationStatus, setIntegrationStatus] = useState({});
  const [apiKeys, setApiKeys] = useState([]);
  const [editingContent, setEditingContent] = useState(null);
  const [editingBanner, setEditingBanner] = useState(null);
  const [newBanner, setNewBanner] = useState({
    title: '',
    message: '',
    cta_text: '',
    cta_url: '',
    banner_type: 'info',
    funnel_stages: [],
    background_color: '#667eea',
    text_color: '#ffffff'
  });
  const [newApiKey, setNewApiKey] = useState({
    service: 'stripe',
    key_name: 'secret_key',
    key_value: '',
    environment: 'test'
  });

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/admin/analytics`);
      setAnalytics(response.data);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  };

  const fetchContent = async () => {
    try {
      const response = await axios.get(`${API}/content`);
      setContent(response.data);
    } catch (err) {
      console.error('Failed to fetch content:', err);
    }
  };

  const fetchBanners = async () => {
    try {
      const response = await axios.get(`${API}/banners`);
      setBanners(response.data);
    } catch (err) {
      console.error('Failed to fetch banners:', err);
    }
  };

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

  const updateContent = async (key, newContent) => {
    try {
      await axios.put(`${API}/content/key/${key}`, { content: newContent });
      fetchContent();
      setEditingContent(null);
    } catch (err) {
      alert('Failed to update content: ' + (err.response?.data?.detail || err.message));
    }
  };

  const createBanner = async () => {
    try {
      await axios.post(`${API}/banners`, newBanner);
      setNewBanner({
        title: '',
        message: '',
        cta_text: '',
        cta_url: '',
        banner_type: 'info',
        funnel_stages: [],
        background_color: '#667eea',
        text_color: '#ffffff'
      });
      fetchBanners();
    } catch (err) {
      alert('Failed to create banner: ' + (err.response?.data?.detail || err.message));
    }
  };

  const deleteBanner = async (bannerId) => {
    if (window.confirm('Are you sure you want to delete this banner?')) {
      try {
        await axios.delete(`${API}/banners/${bannerId}`);
        fetchBanners();
      } catch (err) {
        alert('Failed to delete banner: ' + (err.response?.data?.detail || err.message));
      }
    }
  };

  const toggleBannerStage = (stage) => {
    const stages = newBanner.funnel_stages;
    if (stages.includes(stage)) {
      setNewBanner({
        ...newBanner,
        funnel_stages: stages.filter(s => s !== stage)
      });
    } else {
      setNewBanner({
        ...newBanner,
        funnel_stages: [...stages, stage]
      });
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
    if (isOpen) {
      fetchAnalytics();
      fetchContent();
      fetchBanners();
      fetchIntegrationStatus();
      fetchApiKeys();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="admin-portal">
        <div className="admin-header">
          <h2>🏢 Admin Portal</h2>
          <button onClick={onClose} className="close-btn">×</button>
        </div>

        <div className="admin-nav">
          <button 
            className={activeTab === 'dashboard' ? 'active' : ''}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={activeTab === 'content' ? 'active' : ''}
            onClick={() => setActiveTab('content')}
          >
            📝 Content
          </button>
          <button 
            className={activeTab === 'banners' ? 'active' : ''}
            onClick={() => setActiveTab('banners')}
          >
            🎯 Banners
          </button>
          <button 
            className={activeTab === 'integrations' ? 'active' : ''}
            onClick={() => setActiveTab('integrations')}
          >
            🔗 Integrations
          </button>
          <button 
            className={activeTab === 'crm' ? 'active' : ''}
            onClick={() => setActiveTab('crm')}
          >
            👥 CRM
          </button>
          <button 
            className={activeTab === 'locations' ? 'active' : ''}
            onClick={() => setActiveTab('locations')}
          >
            🏢 Locations
          </button>
        </div>

        <div className="admin-content">
          {activeTab === 'integrations' && (
            <AdminIntegrations />
          )}

          {activeTab === 'crm' && (
            <AdminCRM />
          )}

          {activeTab === 'locations' && (
            <AdminLocations />
          )}
          {activeTab === 'dashboard' && (
            <div className="dashboard-tab">
              <h3>Analytics Overview</h3>
              <div className="stats-grid">
                <div className="stat-card">
                  <h4>Total Units</h4>
                  <p className="stat-number">{analytics.total_units}</p>
                </div>
                <div className="stat-card">
                  <h4>Total Bookings</h4>
                  <p className="stat-number">{analytics.total_bookings}</p>
                </div>
                <div className="stat-card">
                  <h4>Total Images</h4>
                  <p className="stat-number">{analytics.total_images}</p>
                </div>
                <div className="stat-card">
                  <h4>Unique Visitors (7d)</h4>
                  <p className="stat-number">{analytics.last_7_days?.unique_visitors}</p>
                </div>
              </div>

              {analytics.last_7_days?.event_counts && (
                <div className="events-section">
                  <h4>User Activity (Last 7 Days)</h4>
                  <div className="events-list">
                    {Object.entries(analytics.last_7_days.event_counts).map(([event, count]) => (
                      <div key={event} className="event-item">
                        <span className="event-name">{event.replace('_', ' ')}</span>
                        <span className="event-count">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'content' && (
            <div className="content-tab">
              <h3>Content Management</h3>
              <div className="content-list">
                {content.map(item => (
                  <div key={item.id} className="content-item">
                    <div className="content-header">
                      <h4>{item.key}</h4>
                      <span className="content-section">{item.section}</span>
                    </div>
                    {editingContent === item.key ? (
                      <div className="content-edit">
                        <textarea
                          value={item.content}
                          onChange={(e) => {
                            const updatedContent = content.map(c => 
                              c.key === item.key ? {...c, content: e.target.value} : c
                            );
                            setContent(updatedContent);
                          }}
                        />
                        <div className="edit-actions">
                          <button 
                            onClick={() => updateContent(item.key, item.content)}
                            className="save-btn"
                          >
                            Save
                          </button>
                          <button 
                            onClick={() => setEditingContent(null)}
                            className="cancel-btn"
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="content-display">
                        <p>{item.content}</p>
                        <button 
                          onClick={() => setEditingContent(item.key)}
                          className="edit-btn"
                        >
                          Edit
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'banners' && (
            <div className="banners-tab">
              <h3>Banner Management</h3>
              
              <div className="create-banner">
                <h4>Create New Banner</h4>
                <div className="banner-form">
                  <input
                    type="text"
                    placeholder="Banner Title"
                    value={newBanner.title}
                    onChange={(e) => setNewBanner({...newBanner, title: e.target.value})}
                  />
                  <textarea
                    placeholder="Banner Message"
                    value={newBanner.message}
                    onChange={(e) => setNewBanner({...newBanner, message: e.target.value})}
                  />
                  <input
                    type="text"
                    placeholder="CTA Text"
                    value={newBanner.cta_text}
                    onChange={(e) => setNewBanner({...newBanner, cta_text: e.target.value})}
                  />
                  <input
                    type="text"
                    placeholder="CTA URL"
                    value={newBanner.cta_url}
                    onChange={(e) => setNewBanner({...newBanner, cta_url: e.target.value})}
                  />
                  
                  <div className="form-row">
                    <select
                      value={newBanner.banner_type}
                      onChange={(e) => setNewBanner({...newBanner, banner_type: e.target.value})}
                    >
                      <option value="info">Info</option>
                      <option value="success">Success</option>
                      <option value="warning">Warning</option>
                      <option value="promotional">Promotional</option>
                    </select>
                    
                    <input
                      type="color"
                      value={newBanner.background_color}
                      onChange={(e) => setNewBanner({...newBanner, background_color: e.target.value})}
                      title="Background Color"
                    />
                    
                    <input
                      type="color"
                      value={newBanner.text_color}
                      onChange={(e) => setNewBanner({...newBanner, text_color: e.target.value})}
                      title="Text Color"
                    />
                  </div>
                  
                  <div className="funnel-stages">
                    <h5>Target Funnel Stages:</h5>
                    {['visitor', 'viewing_units', 'filtering', 'booking_started', 'booking_abandoned', 'booking_completed', 'returning_visitor'].map(stage => (
                      <label key={stage} className="checkbox-label">
                        <input
                          type="checkbox"
                          checked={newBanner.funnel_stages.includes(stage)}
                          onChange={() => toggleBannerStage(stage)}
                        />
                        {stage.replace('_', ' ')}
                      </label>
                    ))}
                  </div>
                  
                  <button onClick={createBanner} className="create-btn">
                    Create Banner
                  </button>
                </div>
              </div>

              <div className="banners-list">
                <h4>Existing Banners</h4>
                {banners.map(banner => (
                  <div key={banner.id} className="banner-item">
                    <div 
                      className="banner-preview"
                      style={{
                        backgroundColor: banner.background_color,
                        color: banner.text_color
                      }}
                    >
                      <strong>{banner.title}</strong>
                      <p>{banner.message}</p>
                      {banner.cta_text && <button>{banner.cta_text}</button>}
                    </div>
                    <div className="banner-info">
                      <p><strong>Type:</strong> {banner.banner_type}</p>
                      <p><strong>Stages:</strong> {banner.funnel_stages.join(', ') || 'All'}</p>
                      <p><strong>Active:</strong> {banner.is_active ? 'Yes' : 'No'}</p>
                      <button 
                        onClick={() => deleteBanner(banner.id)}
                        className="delete-btn"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
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
                        <>
                          <option value="secret_key">Secret Key</option>
                        </>
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
                        <li>Visit <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer">Stripe Dashboard</a></li>
                        <li>Copy your Secret Key (sk_test_... for testing)</li>
                        <li>Add it above as "Stripe &gt; Secret Key"</li>
                      </ol>
                    </div>
                    <div className="instruction-card">
                      <h6>📱 Twilio Setup</h6>
                      <ol>
                        <li>Visit <a href="https://console.twilio.com/" target="_blank" rel="noopener noreferrer">Twilio Console</a></li>
                        <li>Add Account SID, Auth Token, and From Number</li>
                        <li>Verify your phone number first</li>
                      </ol>
                    </div>
                    <div className="instruction-card">
                      <h6>📧 SendGrid Setup</h6>
                      <ol>
                        <li>Visit <a href="https://app.sendgrid.com/settings/api_keys" target="_blank" rel="noopener noreferrer">SendGrid API Keys</a></li>
                        <li>Create new API key with full access</li>
                        <li>Add API key and verified sender email</li>
                      </ol>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
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
                        <>
                          <option value="secret_key">Secret Key</option>
                        </>
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
                        <li>Visit <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer">Stripe Dashboard</a></li>
                        <li>Copy your Secret Key (sk_test_... for testing)</li>
                        <li>Add it above as "Stripe &gt; Secret Key"</li>
                      </ol>
                    </div>
                    <div className="instruction-card">
                      <h6>📱 Twilio Setup</h6>
                      <ol>
                        <li>Visit <a href="https://console.twilio.com/" target="_blank" rel="noopener noreferrer">Twilio Console</a></li>
                        <li>Add Account SID, Auth Token, and From Number</li>
                        <li>Verify your phone number first</li>
                      </ol>
                    </div>
                    <div className="instruction-card">
                      <h6>📧 SendGrid Setup</h6>
                      <ol>
                        <li>Visit <a href="https://app.sendgrid.com/settings/api_keys" target="_blank" rel="noopener noreferrer">SendGrid API Keys</a></li>
                        <li>Create new API key with full access</li>
                        <li>Add API key and verified sender email</li>
                      </ol>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'integrations' && (
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
                        <>
                          <option value="secret_key">Secret Key</option>
                        </>
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
                        <li>Visit <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer">Stripe Dashboard</a></li>
                        <li>Copy your Secret Key (sk_test_... for testing)</li>
                        <li>Add it above as "Stripe &gt; Secret Key"</li>
                      </ol>
                    </div>
                    <div className="instruction-card">
                      <h6>📱 Twilio Setup</h6>
                      <ol>
                        <li>Visit <a href="https://console.twilio.com/" target="_blank" rel="noopener noreferrer">Twilio Console</a></li>
                        <li>Add Account SID, Auth Token, and From Number</li>
                        <li>Verify your phone number first</li>
                      </ol>
                    </div>
                    <div className="instruction-card">
                      <h6>📧 SendGrid Setup</h6>
                      <ol>
                        <li>Visit <a href="https://app.sendgrid.com/settings/api_keys" target="_blank" rel="noopener noreferrer">SendGrid API Keys</a></li>
                        <li>Create new API key with full access</li>
                        <li>Add API key and verified sender email</li>
                      </ol>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const ImageManager = ({ isOpen, onClose }) => {
  const [images, setImages] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newImage, setNewImage] = useState({
    name: '',
    url: '',
    category: 'unit',
    tags: '',
    description: ''
  });

  const fetchImages = async () => {
    try {
      const params = selectedCategory !== 'all' ? `?category=${selectedCategory}` : '';
      const response = await axios.get(`${API}/images${params}`);
      setImages(response.data);
    } catch (err) {
      console.error('Failed to fetch images:', err);
    }
  };

  const handleAddImage = async (e) => {
    e.preventDefault();
    try {
      const imageData = {
        ...newImage,
        tags: newImage.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
      };
      await axios.post(`${API}/images`, imageData);
      setNewImage({ name: '', url: '', category: 'unit', tags: '', description: '' });
      setShowAddForm(false);
      fetchImages();
    } catch (err) {
      alert('Failed to add image: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteImage = async (imageId) => {
    if (window.confirm('Are you sure you want to delete this image?')) {
      try {
        await axios.delete(`${API}/images/${imageId}`);
        fetchImages();
      } catch (err) {
        alert('Failed to delete image: ' + (err.response?.data?.detail || err.message));
      }
    }
  };

  const handleAssignToUnit = async (imageUrl, unitId) => {
    try {
      await axios.put(`${API}/virtual-units/${unitId}/image?image_url=${encodeURIComponent(imageUrl)}`);
      alert('Image assigned to unit successfully!');
      onClose(); // Close the image manager to refresh the main view
    } catch (err) {
      alert('Failed to assign image: ' + (err.response?.data?.detail || err.message));
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchImages();
    }
  }, [isOpen, selectedCategory]);

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="image-manager-modal">
        <div className="image-manager-header">
          <h2>Image Management</h2>
          <div className="header-controls">
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="category-filter"
            >
              <option value="all">All Categories</option>
              <option value="hero">Hero Images</option>
              <option value="unit">Unit Images</option>
              <option value="feature">Feature Images</option>
              <option value="gallery">Gallery Images</option>
            </select>
            <button 
              onClick={() => setShowAddForm(true)}
              className="add-image-btn"
            >
              Add New Image
            </button>
            <button onClick={onClose} className="close-btn">×</button>
          </div>
        </div>

        {showAddForm && (
          <div className="add-image-form">
            <h3>Add New Image</h3>
            <form onSubmit={handleAddImage}>
              <div className="form-row">
                <input
                  type="text"
                  placeholder="Image Name"
                  value={newImage.name}
                  onChange={(e) => setNewImage({...newImage, name: e.target.value})}
                  required
                />
                <select
                  value={newImage.category}
                  onChange={(e) => setNewImage({...newImage, category: e.target.value})}
                >
                  <option value="unit">Unit Image</option>
                  <option value="hero">Hero Image</option>
                  <option value="feature">Feature Image</option>
                  <option value="gallery">Gallery Image</option>
                </select>
              </div>
              <input
                type="url"
                placeholder="Image URL"
                value={newImage.url}
                onChange={(e) => setNewImage({...newImage, url: e.target.value})}
                required
              />
              <input
                type="text"
                placeholder="Tags (comma separated)"
                value={newImage.tags}
                onChange={(e) => setNewImage({...newImage, tags: e.target.value})}
              />
              <textarea
                placeholder="Description"
                value={newImage.description}
                onChange={(e) => setNewImage({...newImage, description: e.target.value})}
              />
              <div className="form-actions">
                <button type="submit">Add Image</button>
                <button type="button" onClick={() => setShowAddForm(false)}>Cancel</button>
              </div>
            </form>
          </div>
        )}

        <div className="images-grid">
          {images.map(image => (
            <div key={image.id} className="image-item">
              <div className="image-preview">
                <img src={image.url} alt={image.name} />
                <div className="image-overlay">
                  <button 
                    onClick={() => handleDeleteImage(image.id)}
                    className="delete-btn"
                  >
                    🗑️
                  </button>
                  <button 
                    onClick={() => {
                      const unitId = prompt('Enter Virtual Unit ID to assign this image:');
                      if (unitId) handleAssignToUnit(image.url, unitId);
                    }}
                    className="assign-btn"
                  >
                    📎
                  </button>
                </div>
              </div>
              <div className="image-info">
                <h4>{image.name}</h4>
                <span className="category-badge">{image.category}</span>
                <div className="tags">
                  {image.tags.map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
                <p className="description">{image.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const UnitCard = ({ unit, onBook, pricingPeriod, onChangeImage }) => {
  const getPrice = () => {
    switch (pricingPeriod) {
      case 'daily': return unit.daily_price;
      case 'weekly': return unit.weekly_price;
      case 'monthly': return unit.monthly_price;
      default: return unit.monthly_price;
    }
  };

  const getPeriodLabel = () => {
    switch (pricingPeriod) {
      case 'daily': return '/day';
      case 'weekly': return '/week'; 
      case 'monthly': return '/month';
      default: return '/month';
    }
  };

  const getUnitTypeLabel = (type) => {
    return type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  const getSizeCategory = (size) => {
    try {
      const numbers = size.match(/\d+/g);
      if (numbers && numbers.length >= 2) {
        const area = parseInt(numbers[0]) * parseInt(numbers[1]);
        if (area <= 200) return 'Small';
        if (area <= 400) return 'Medium';
        return 'Large';
      }
    } catch (e) {}
    return 'Medium';
  };

  const handleUnitClick = () => {
    trackEvent('unit_viewed', { unit_id: unit.id, unit_type: unit.unit_type });
  };

  return (
    <div className="unit-card" onClick={handleUnitClick}>
      <div className="unit-image">
        <img src={unit.image_url} alt={unit.display_name} />
        <div className="unit-type-badge">
          {getUnitTypeLabel(unit.unit_type)}
        </div>
        {onChangeImage && (
          <button 
            className="change-image-btn"
            onClick={(e) => {
              e.stopPropagation();
              onChangeImage(unit);
            }}
            title="Change Image"
          >
            🖼️
          </button>
        )}
      </div>
      
      <div className="unit-content">
        <h3 className="unit-title">{unit.display_name}</h3>
        <p className="unit-description">{unit.description}</p>
        
        <div className="unit-details">
          <div className="detail-item">
            <span className="label">Size:</span>
            <span className="value">{unit.display_size} ({getSizeCategory(unit.display_size)})</span>
          </div>
          
          <div className="detail-item">
            <span className="label">Amenities:</span>
            <div className="amenities">
              {unit.amenities.map((amenity, index) => (
                <span key={index} className="amenity-tag">
                  {amenity.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        </div>
        
        <div className="unit-pricing">
          <div className="price">
            <span className="amount">${getPrice()}</span>
            <span className="period">{getPeriodLabel()}</span>
          </div>
          
          <button 
            className="book-button"
            onClick={(e) => {
              e.stopPropagation();
              onBook(unit);
              trackEvent('booking_started', { unit_id: unit.id });
            }}
          >
            Book Now
          </button>
        </div>
      </div>
    </div>
  );
};

const FilterPanel = ({ filters, onFilterChange, filterOptions }) => {
  const handleFilterChange = (key, value) => {
    onFilterChange(key, value);
    trackEvent('filter_used', { filter_key: key, filter_value: value });
  };

  return (
    <div className="filter-panel">
      <h3>Filter Units</h3>
      
      <div className="filter-group">
        <label>Unit Type</label>
        <select 
          value={filters.unit_type || ''} 
          onChange={(e) => handleFilterChange('unit_type', e.target.value || null)}
        >
          <option value="">All Types</option>
          {filterOptions.unit_types?.map(type => (
            <option key={type} value={type}>
              {type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
            </option>
          ))}
        </select>
      </div>
      
      <div className="filter-group">
        <label>Size Category</label>
        <select 
          value={filters.size_category || ''} 
          onChange={(e) => handleFilterChange('size_category', e.target.value || null)}
        >
          <option value="">All Sizes</option>
          {filterOptions.size_categories?.map(size => (
            <option key={size} value={size}>
              {size.charAt(0).toUpperCase() + size.slice(1)}
            </option>
          ))}
        </select>
      </div>
      
      <div className="filter-group">
        <label>Pricing Period</label>
        <select 
          value={filters.pricing_period || 'monthly'} 
          onChange={(e) => handleFilterChange('pricing_period', e.target.value)}
        >
          {filterOptions.pricing_periods?.map(period => (
            <option key={period} value={period}>
              {period.charAt(0).toUpperCase() + period.slice(1)}
            </option>
          ))}
        </select>
      </div>
      
      <div className="filter-group">
        <label>Price Range</label>
        <div className="price-range">
          <input
            type="number"
            placeholder="Min"
            value={filters.min_price || ''}
            onChange={(e) => handleFilterChange('min_price', e.target.value ? parseFloat(e.target.value) : null)}
          />
          <span>to</span>
          <input
            type="number"
            placeholder="Max"
            value={filters.max_price || ''}
            onChange={(e) => handleFilterChange('max_price', e.target.value ? parseFloat(e.target.value) : null)}
          />
        </div>
      </div>
      
      <div className="filter-group">
        <label>Amenities</label>
        <div className="amenities-filter">
          {filterOptions.amenities?.map(amenity => (
            <label key={amenity} className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.amenities?.includes(amenity) || false}
                onChange={(e) => {
                  const currentAmenities = filters.amenities || [];
                  if (e.target.checked) {
                    handleFilterChange('amenities', [...currentAmenities, amenity]);
                  } else {
                    handleFilterChange('amenities', currentAmenities.filter(a => a !== amenity));
                  }
                }}
              />
              {amenity.replace('_', ' ')}
            </label>
          ))}
        </div>
      </div>
    </div>
  );
};

const BookingModal = ({ unit, isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    payment_option: 'pay_now_move_now',
    pricing_period: 'monthly',
    start_date: new Date().toISOString().split('T')[0],
    move_in_date: new Date().toISOString().split('T')[0],
    special_requests: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      ...formData,
      virtual_unit_id: unit.id,
      start_date: new Date(formData.start_date).toISOString(),
      move_in_date: new Date(formData.move_in_date).toISOString()
    });
  };

  const handleClose = () => {
    trackEvent('booking_abandoned', { unit_id: unit?.id });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Book {unit?.display_name}</h2>
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              required
              value={formData.customer_name}
              onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              required
              value={formData.customer_email}
              onChange={(e) => setFormData({...formData, customer_email: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Phone</label>
            <input
              type="tel"
              required
              value={formData.customer_phone}
              onChange={(e) => setFormData({...formData, customer_phone: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Payment & Move-in Option</label>
            <select
              value={formData.payment_option}
              onChange={(e) => setFormData({...formData, payment_option: e.target.value})}
            >
              <option value="pay_now_move_now">Pay Now + Move In Now</option>
              <option value="pay_now_move_later">Pay Now + Move In Later</option>
              <option value="pay_later_move_later">Pay Later + Move In Later (Waitlist)</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>Pricing Period</label>
            <select
              value={formData.pricing_period}
              onChange={(e) => setFormData({...formData, pricing_period: e.target.value})}
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
            </select>
          </div>
          
          <div className="form-group">
            <label>Start Date</label>
            <input
              type="date"
              required
              value={formData.start_date}
              onChange={(e) => setFormData({...formData, start_date: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Move-in Date</label>
            <input
              type="date"
              required
              value={formData.move_in_date}
              onChange={(e) => setFormData({...formData, move_in_date: e.target.value})}
            />
          </div>
          
          <div className="form-group">
            <label>Special Requests</label>
            <textarea
              value={formData.special_requests}
              onChange={(e) => setFormData({...formData, special_requests: e.target.value})}
              placeholder="Any special requirements or requests..."
            />
          </div>
          
          <div className="modal-actions">
            <button type="button" onClick={handleClose} className="cancel-button">
              Cancel
            </button>
            <button type="submit" className="submit-button">
              Book Unit
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

function App() {
  const [virtualUnits, setVirtualUnits] = useState([]);
  const [filterOptions, setFilterOptions] = useState({});
  const [filters, setFilters] = useState({
    pricing_period: 'monthly'
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedUnit, setSelectedUnit] = useState(null);
  const [showBookingModal, setShowBookingModal] = useState(false);
  const [showImageManager, setShowImageManager] = useState(false);
  const [showAdminPortal, setShowAdminPortal] = useState(false);
  const [adminMode, setAdminMode] = useState(false);
  const [initialized, setInitialized] = useState(false);
  const [content, setContent] = useState({});
  const [currentBanner, setCurrentBanner] = useState(null);
  const [dismissedBanners, setDismissedBanners] = useState([]);
  const [userFunnelStage, setUserFunnelStage] = useState('visitor');
  const [pwaInstallPrompt, setPwaInstallPrompt] = useState(null);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);

  // PWA Installation
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setPwaInstallPrompt(e);
      setShowInstallPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Register service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration);
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError);
        });
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallPWA = async () => {
    if (pwaInstallPrompt) {
      const result = await pwaInstallPrompt.prompt();
      console.log('Install result:', result);
      setPwaInstallPrompt(null);
      setShowInstallPrompt(false);
    }
  };
  const [pwaInstallPrompt, setPwaInstallPrompt] = useState(null);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);

  // PWA Installation
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setPwaInstallPrompt(e);
      setShowInstallPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Register service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration);
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError);
        });
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallPWA = async () => {
    if (pwaInstallPrompt) {
      const result = await pwaInstallPrompt.prompt();
      console.log('Install result:', result);
      setPwaInstallPrompt(null);
      setShowInstallPrompt(false);
    }
  };
  const [pwaInstallPrompt, setPwaInstallPrompt] = useState(null);
  const [showInstallPrompt, setShowInstallPrompt] = useState(false);

  // PWA Installation
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setPwaInstallPrompt(e);
      setShowInstallPrompt(true);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Register service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then((registration) => {
          console.log('SW registered: ', registration);
        })
        .catch((registrationError) => {
          console.log('SW registration failed: ', registrationError);
        });
    }

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    };
  }, []);

  const handleInstallPWA = async () => {
    if (pwaInstallPrompt) {
      const result = await pwaInstallPrompt.prompt();
      console.log('Install result:', result);
      setPwaInstallPrompt(null);
      setShowInstallPrompt(false);
    }
  };

  const initializeData = async () => {
    try {
      await axios.post(`${API}/initialize-sample-data`);
      setInitialized(true);
    } catch (err) {
      console.error('Failed to initialize data:', err);
    }
  };

  const fetchContent = async () => {
    try {
      const response = await axios.get(`${API}/content`);
      const contentMap = {};
      response.data.forEach(item => {
        contentMap[item.key] = item.content;
      });
      setContent(contentMap);
    } catch (err) {
      console.error('Failed to fetch content:', err);
    }
  };

  const fetchUserFunnelStage = async () => {
    try {
      const response = await axios.get(`${API}/funnel/user/${getSessionId()}`);
      setUserFunnelStage(response.data.funnel_stage);
    } catch (err) {
      console.error('Failed to fetch funnel stage:', err);
    }
  };

  const fetchActiveBanner = async () => {
    try {
      const response = await axios.get(`${API}/banners?active_only=true&funnel_stage=${userFunnelStage}`);
      const availableBanners = response.data.filter(banner => !dismissedBanners.includes(banner.id));
      if (availableBanners.length > 0) {
        setCurrentBanner(availableBanners[0]);
      }
    } catch (err) {
      console.error('Failed to fetch banners:', err);
    }
  };

  const dismissBanner = (bannerId) => {
    const newDismissed = [...dismissedBanners, bannerId];
    setDismissedBanners(newDismissed);
    localStorage.setItem('dismissedBanners', JSON.stringify(newDismissed));
    setCurrentBanner(null);
  };

  const fetchFilterOptions = async () => {
    try {
      const response = await axios.get(`${API}/filter-options`);
      setFilterOptions(response.data);
    } catch (err) {
      console.error('Failed to fetch filter options:', err);
    }
  };

  const fetchVirtualUnits = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '') {
          if (key === 'amenities' && Array.isArray(value)) {
            params.append(key, value.join(','));
          } else {
            params.append(key, value);
          }
        }
      });

      const response = await axios.get(`${API}/virtual-units?${params}`);
      setVirtualUnits(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch units');
      console.error('Error fetching units:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleBookUnit = (unit) => {
    setSelectedUnit(unit);
    setShowBookingModal(true);
  };

  const handleBookingSubmit = async (bookingData) => {
    try {
      await axios.post(`${API}/bookings`, bookingData);
      alert('Booking created successfully!');
      trackEvent('booking_completed', { unit_id: bookingData.virtual_unit_id });
      setShowBookingModal(false);
      setSelectedUnit(null);
      fetchVirtualUnits(); // Refresh the list
    } catch (err) {
      alert('Failed to create booking: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleChangeImage = (unit) => {
    setSelectedUnit(unit);
    setShowImageManager(true);
  };

  const toggleAdminMode = () => {
    setAdminMode(!adminMode);
  };

  // Track page view on load
  useEffect(() => {
    trackEvent('page_view', { page: 'home' });
    
    // Load dismissed banners from localStorage
    const stored = localStorage.getItem('dismissedBanners');
    if (stored) {
      setDismissedBanners(JSON.parse(stored));
    }
  }, []);

  useEffect(() => {
    const initialize = async () => {
      if (!initialized) {
        await initializeData();
      }
      await fetchContent();
      await fetchFilterOptions();
      await fetchVirtualUnits();
      await fetchUserFunnelStage();
    };
    
    initialize();
  }, [initialized]);

  useEffect(() => {
    if (initialized) {
      fetchVirtualUnits();
    }
  }, [filters, initialized]);

  useEffect(() => {
    if (userFunnelStage) {
      fetchActiveBanner();
    }
  }, [userFunnelStage, dismissedBanners]);

  return (
    <div className="App">
      {/* PWA Install Banner */}
      {showInstallPrompt && (
        <div className="pwa-install-banner">
          <div className="banner-content">
            <span>📱 Install our app for the best experience!</span>
            <div className="banner-actions">
              <button onClick={handleInstallPWA} className="install-btn">
                Install App
              </button>
              <button onClick={() => setShowInstallPrompt(false)} className="dismiss-btn">
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Promotional Banner */}
      {currentBanner && (
        <PromoBanner banner={currentBanner} onClose={dismissBanner} />
      )}

      {/* Admin Controls */}
      <div className="admin-controls" style={{top: currentBanner ? '60px' : '20px'}}>
        <button 
          onClick={() => {
            console.log('Admin toggle clicked, current adminMode:', adminMode);
            setAdminMode(!adminMode);
          }}
          className={`admin-toggle ${adminMode ? 'active' : ''}`}
        >
          {adminMode ? '👨‍💼 Admin Mode ON' : '👤 User Mode'}
        </button>
        {adminMode && (
          <>
            <button 
              onClick={() => {
                console.log('Admin portal button clicked');
                setShowAdminPortal(true);
              }}
              className="admin-portal-btn"
            >
              🏢 Admin Portal
            </button>
            <button 
              onClick={() => setShowImageManager(true)}
              className="image-manager-btn"
            >
              🖼️ Manage Images
            </button>
          </>
        )}
      </div>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>{content.hero_title || 'Premium RV & Boat Storage'}</h1>
          <p>{content.hero_subtitle || 'Secure, flexible storage solutions with multiple booking options'}</p>
          {adminMode && <p className="admin-notice">🔧 Admin Mode: You can now manage content and banners</p>}
          <div className="hero-stats">
            <div className="stat">
              <span className="number">{virtualUnits.length}</span>
              <span className="label">Available Units</span>
            </div>
            <div className="stat">
              <span className="number">4</span>
              <span className="label">Storage Types</span>
            </div>
            <div className="stat">
              <span className="number">24/7</span>
              <span className="label">Access Available</span>
            </div>
          </div>
        </div>
        <div className="hero-image">
          <img src="https://images.pexels.com/photos/13016664/pexels-photo-13016664.png" alt="RV Storage" />
        </div>
      </section>

      {/* Main Content */}
      <div className="main-content">
        <aside className="sidebar">
          <FilterPanel 
            filters={filters}
            onFilterChange={handleFilterChange}
            filterOptions={filterOptions}
          />
        </aside>

        <main className="content">
          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          {loading ? (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading available units...</p>
            </div>
          ) : (
            <>
              <div className="results-header">
                <h2>{content.results_header_title || 'Available Storage Units'}</h2>
                <p>{virtualUnits.length} units match your criteria</p>
              </div>

              <div className="units-grid">
                {virtualUnits.map(unit => (
                  <UnitCard
                    key={unit.id}
                    unit={unit}
                    onBook={handleBookUnit}
                    onChangeImage={adminMode ? handleChangeImage : null}
                    pricingPeriod={filters.pricing_period}
                  />
                ))}
              </div>

              {virtualUnits.length === 0 && (
                <div className="no-results">
                  <h3>No units match your criteria</h3>
                  <p>Try adjusting your filters to see more options</p>
                </div>
              )}
            </>
          )}
        </main>
      </div>

      {/* Booking Modal */}
      <BookingModal
        unit={selectedUnit}
        isOpen={showBookingModal}
        onClose={() => {
          setShowBookingModal(false);
          setSelectedUnit(null);
        }}
        onSubmit={handleBookingSubmit}
      />

      {/* Admin Portal */}
      <AdminPortal
        isOpen={showAdminPortal}
        onClose={() => setShowAdminPortal(false)}
      />

      {/* Image Manager */}
      <ImageManager
        isOpen={showImageManager}
        onClose={() => {
          setShowImageManager(false);
          setSelectedUnit(null);
          fetchVirtualUnits(); // Refresh units after image changes
        }}
      />

      {/* Features Section */}
      <section className="features">
        <h2>Why Choose Our Storage?</h2>
        <div className="features-grid">
          <div className="feature">
            <img src="https://images.unsplash.com/photo-1551313158-73d016a829ae" alt="Secure Storage" />
            <h3>{content.feature_1_title || 'Secure & Safe'}</h3>
            <p>{content.feature_1_description || '24/7 security monitoring and controlled access'}</p>
          </div>
          <div className="feature">
            <img src="https://images.pexels.com/photos/13388790/pexels-photo-13388790.jpeg" alt="Flexible Options" />
            <h3>{content.feature_2_title || 'Flexible Booking'}</h3>
            <p>{content.feature_2_description || 'Pay now or later, move in when convenient'}</p>
          </div>
          <div className="feature">
            <img src="https://images.unsplash.com/photo-1711130361680-a3beb1369ef5" alt="Multiple Sizes" />
            <h3>{content.feature_3_title || 'Multiple Sizes'}</h3>
            <p>{content.feature_3_description || 'From small boats to large RVs, we have space for everything'}</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default App;