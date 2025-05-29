import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminCRM = () => {
  const [customers, setCustomers] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerBookings, setCustomerBookings] = useState([]);
  const [loyaltyInfo, setLoyaltyInfo] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterTier, setFilterTier] = useState('');
  const [showAddCustomer, setShowAddCustomer] = useState(false);
  const [newCustomer, setNewCustomer] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    company: '',
    customer_type: 'individual',
    acquisition_source: 'web'
  });

  const fetchCustomers = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterType) params.append('customer_type', filterType);
      if (filterTier) params.append('loyalty_tier', filterTier);
      
      const response = await axios.get(`${API}/customers?${params}`);
      setCustomers(response.data);
    } catch (err) {
      console.error('Failed to fetch customers:', err);
    }
  };

  const fetchCustomerDetails = async (customerId) => {
    try {
      // Get customer bookings
      const bookingsResponse = await axios.get(`${API}/customers/${customerId}/bookings`);
      setCustomerBookings(bookingsResponse.data);
      
      // Get loyalty info
      const loyaltyResponse = await axios.get(`${API}/loyalty/customer/${customerId}`);
      setLoyaltyInfo(loyaltyResponse.data);
    } catch (err) {
      console.error('Failed to fetch customer details:', err);
    }
  };

  const createCustomer = async () => {
    try {
      await axios.post(`${API}/customers`, newCustomer);
      setNewCustomer({
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        company: '',
        customer_type: 'individual',
        acquisition_source: 'web'
      });
      setShowAddCustomer(false);
      fetchCustomers();
    } catch (err) {
      alert('Failed to create customer: ' + (err.response?.data?.detail || err.message));
    }
  };

  const awardPoints = async (customerId, points, description) => {
    try {
      await axios.post(`${API}/loyalty/award-points`, {
        customer_id: customerId,
        points: parseInt(points),
        description
      });
      fetchCustomerDetails(customerId);
      fetchCustomers(); // Refresh to update points display
    } catch (err) {
      alert('Failed to award points: ' + (err.response?.data?.detail || err.message));
    }
  };

  const redeemPoints = async (customerId, points, description) => {
    try {
      await axios.post(`${API}/loyalty/redeem-points`, {
        customer_id: customerId,
        points: parseInt(points),
        description
      });
      fetchCustomerDetails(customerId);
      fetchCustomers();
    } catch (err) {
      alert('Failed to redeem points: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getTierColor = (tier) => {
    switch (tier) {
      case 'bronze': return '#cd7f32';
      case 'silver': return '#c0c0c0';
      case 'gold': return '#ffd700';
      case 'platinum': return '#e5e4e2';
      default: return '#cd7f32';
    }
  };

  const getTierIcon = (tier) => {
    switch (tier) {
      case 'bronze': return '🥉';
      case 'silver': return '🥈';
      case 'gold': return '🥇';
      case 'platinum': return '💎';
      default: return '🥉';
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [searchTerm, filterType, filterTier]);

  useEffect(() => {
    if (selectedCustomer) {
      fetchCustomerDetails(selectedCustomer.id);
    }
  }, [selectedCustomer]);

  return (
    <div className="crm-tab">
      <h3>👥 Customer Relationship Management</h3>
      
      {/* Search and Filters */}
      <div className="crm-controls">
        <div className="search-filters">
          <input
            type="text"
            placeholder="Search customers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="filter-select"
          >
            <option value="">All Types</option>
            <option value="individual">Individual</option>
            <option value="business">Business</option>
            <option value="vip">VIP</option>
          </select>
          <select
            value={filterTier}
            onChange={(e) => setFilterTier(e.target.value)}
            className="filter-select"
          >
            <option value="">All Tiers</option>
            <option value="bronze">Bronze</option>
            <option value="silver">Silver</option>
            <option value="gold">Gold</option>
            <option value="platinum">Platinum</option>
          </select>
        </div>
        <button 
          onClick={() => setShowAddCustomer(true)}
          className="add-customer-btn"
        >
          ➕ Add Customer
        </button>
      </div>

      <div className="crm-content">
        {/* Customer List */}
        <div className="customers-list">
          <h4>Customers ({customers.length})</h4>
          <div className="customers-grid">
            {customers.map(customer => (
              <div 
                key={customer.id} 
                className={`customer-card ${selectedCustomer?.id === customer.id ? 'selected' : ''}`}
                onClick={() => setSelectedCustomer(customer)}
              >
                <div className="customer-header">
                  <h5>{customer.first_name} {customer.last_name}</h5>
                  <span 
                    className="tier-badge"
                    style={{ backgroundColor: getTierColor(customer.loyalty_tier) }}
                  >
                    {getTierIcon(customer.loyalty_tier)} {customer.loyalty_tier}
                  </span>
                </div>
                <p className="customer-email">{customer.email}</p>
                <div className="customer-stats">
                  <span className="stat">
                    <strong>{customer.loyalty_points}</strong> points
                  </span>
                  <span className="stat">
                    <strong>{customer.total_bookings}</strong> bookings
                  </span>
                  <span className="stat">
                    <strong>${customer.lifetime_value}</strong> LTV
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Customer Details */}
        {selectedCustomer && (
          <div className="customer-details">
            <div className="details-header">
              <h4>{selectedCustomer.first_name} {selectedCustomer.last_name}</h4>
              <span className="customer-type">{selectedCustomer.customer_type}</span>
            </div>

            {/* Contact Info */}
            <div className="details-section">
              <h5>📞 Contact Information</h5>
              <div className="contact-info">
                <p><strong>Email:</strong> {selectedCustomer.email}</p>
                <p><strong>Phone:</strong> {selectedCustomer.phone}</p>
                {selectedCustomer.company && <p><strong>Company:</strong> {selectedCustomer.company}</p>}
                <p><strong>Referral Code:</strong> {selectedCustomer.referral_code}</p>
              </div>
            </div>

            {/* Loyalty Program */}
            {loyaltyInfo && (
              <div className="details-section">
                <h5>🎁 Loyalty Program</h5>
                <div className="loyalty-overview">
                  <div className="loyalty-stats">
                    <div className="loyalty-stat">
                      <span className="stat-value">{loyaltyInfo.points}</span>
                      <span className="stat-label">Points</span>
                    </div>
                    <div className="loyalty-stat">
                      <span className="stat-value" style={{ color: getTierColor(loyaltyInfo.tier) }}>
                        {getTierIcon(loyaltyInfo.tier)} {loyaltyInfo.tier}
                      </span>
                      <span className="stat-label">Tier</span>
                    </div>
                    <div className="loyalty-stat">
                      <span className="stat-value">${loyaltyInfo.lifetime_value}</span>
                      <span className="stat-label">Lifetime Value</span>
                    </div>
                  </div>
                  
                  <div className="loyalty-actions">
                    <button 
                      onClick={() => {
                        const points = prompt('Points to award:');
                        const description = prompt('Description:');
                        if (points && description) {
                          awardPoints(selectedCustomer.id, points, description);
                        }
                      }}
                      className="award-points-btn"
                    >
                      ➕ Award Points
                    </button>
                    <button 
                      onClick={() => {
                        const points = prompt('Points to redeem:');
                        const description = prompt('Description:');
                        if (points && description) {
                          redeemPoints(selectedCustomer.id, points, description);
                        }
                      }}
                      className="redeem-points-btn"
                    >
                      ➖ Redeem Points
                    </button>
                  </div>
                </div>

                {/* Recent Transactions */}
                <div className="loyalty-transactions">
                  <h6>Recent Transactions</h6>
                  {loyaltyInfo.transactions.slice(0, 5).map(transaction => (
                    <div key={transaction.id} className="transaction-item">
                      <span className={`transaction-type ${transaction.transaction_type}`}>
                        {transaction.transaction_type === 'earned' ? '↗️' : '↙️'}
                      </span>
                      <span className="transaction-points">
                        {transaction.points > 0 ? '+' : ''}{transaction.points} pts
                      </span>
                      <span className="transaction-description">{transaction.description}</span>
                      <span className="transaction-date">
                        {new Date(transaction.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Booking History */}
            <div className="details-section">
              <h5>📋 Booking History ({customerBookings.length})</h5>
              <div className="bookings-list">
                {customerBookings.map(booking => (
                  <div key={booking.id} className="booking-item">
                    <div className="booking-info">
                      <strong>Booking #{booking.id.slice(0, 8)}</strong>
                      <span className="booking-amount">${booking.total_price}</span>
                    </div>
                    <div className="booking-details">
                      <p>Payment: {booking.payment_option.replace('_', ' ')}</p>
                      <p>Period: {booking.pricing_period}</p>
                      <p>Created: {new Date(booking.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Add Customer Modal */}
      {showAddCustomer && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Add New Customer</h3>
            <div className="add-customer-form">
              <div className="form-row">
                <input
                  type="text"
                  placeholder="First Name"
                  value={newCustomer.first_name}
                  onChange={(e) => setNewCustomer({...newCustomer, first_name: e.target.value})}
                />
                <input
                  type="text"
                  placeholder="Last Name"
                  value={newCustomer.last_name}
                  onChange={(e) => setNewCustomer({...newCustomer, last_name: e.target.value})}
                />
              </div>
              <input
                type="email"
                placeholder="Email"
                value={newCustomer.email}
                onChange={(e) => setNewCustomer({...newCustomer, email: e.target.value})}
              />
              <input
                type="tel"
                placeholder="Phone"
                value={newCustomer.phone}
                onChange={(e) => setNewCustomer({...newCustomer, phone: e.target.value})}
              />
              <input
                type="text"
                placeholder="Company (optional)"
                value={newCustomer.company}
                onChange={(e) => setNewCustomer({...newCustomer, company: e.target.value})}
              />
              <div className="form-row">
                <select
                  value={newCustomer.customer_type}
                  onChange={(e) => setNewCustomer({...newCustomer, customer_type: e.target.value})}
                >
                  <option value="individual">Individual</option>
                  <option value="business">Business</option>
                  <option value="vip">VIP</option>
                </select>
                <select
                  value={newCustomer.acquisition_source}
                  onChange={(e) => setNewCustomer({...newCustomer, acquisition_source: e.target.value})}
                >
                  <option value="web">Website</option>
                  <option value="referral">Referral</option>
                  <option value="ads">Advertising</option>
                  <option value="social">Social Media</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div className="modal-actions">
                <button onClick={() => setShowAddCustomer(false)} className="cancel-btn">
                  Cancel
                </button>
                <button onClick={createCustomer} className="create-btn">
                  Create Customer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCRM;