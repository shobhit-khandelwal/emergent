import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

  return (
    <div className="unit-card">
      <div className="unit-image">
        <img src={unit.image_url} alt={unit.display_name} />
        <div className="unit-type-badge">
          {getUnitTypeLabel(unit.unit_type)}
        </div>
        {onChangeImage && (
          <button 
            className="change-image-btn"
            onClick={() => onChangeImage(unit)}
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
            onClick={() => onBook(unit)}
          >
            Book Now
          </button>
        </div>
      </div>
    </div>
  );
};

const FilterPanel = ({ filters, onFilterChange, filterOptions }) => {
  return (
    <div className="filter-panel">
      <h3>Filter Units</h3>
      
      <div className="filter-group">
        <label>Unit Type</label>
        <select 
          value={filters.unit_type || ''} 
          onChange={(e) => onFilterChange('unit_type', e.target.value || null)}
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
          onChange={(e) => onFilterChange('size_category', e.target.value || null)}
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
          onChange={(e) => onFilterChange('pricing_period', e.target.value)}
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
            onChange={(e) => onFilterChange('min_price', e.target.value ? parseFloat(e.target.value) : null)}
          />
          <span>to</span>
          <input
            type="number"
            placeholder="Max"
            value={filters.max_price || ''}
            onChange={(e) => onFilterChange('max_price', e.target.value ? parseFloat(e.target.value) : null)}
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
                    onFilterChange('amenities', [...currentAmenities, amenity]);
                  } else {
                    onFilterChange('amenities', currentAmenities.filter(a => a !== amenity));
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
            <button type="button" onClick={onClose} className="cancel-button">
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
  const [adminMode, setAdminMode] = useState(false);
  const [initialized, setInitialized] = useState(false);

  const initializeData = async () => {
    try {
      await axios.post(`${API}/initialize-sample-data`);
      setInitialized(true);
    } catch (err) {
      console.error('Failed to initialize data:', err);
    }
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

  useEffect(() => {
    const initialize = async () => {
      if (!initialized) {
        await initializeData();
      }
      await fetchFilterOptions();
      await fetchVirtualUnits();
    };
    
    initialize();
  }, [initialized]);

  useEffect(() => {
    if (initialized) {
      fetchVirtualUnits();
    }
  }, [filters, initialized]);

  return (
    <div className="App">
      {/* Admin Toggle */}
      <div className="admin-controls">
        <button 
          onClick={toggleAdminMode}
          className={`admin-toggle ${adminMode ? 'active' : ''}`}
        >
          {adminMode ? '👨‍💼 Admin Mode ON' : '👤 User Mode'}
        </button>
        {adminMode && (
          <button 
            onClick={() => setShowImageManager(true)}
            className="image-manager-btn"
          >
            🖼️ Manage Images
          </button>
        )}
      </div>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <h1>Premium RV & Boat Storage</h1>
          <p>Secure, flexible storage solutions with multiple booking options</p>
          {adminMode && <p className="admin-notice">🔧 Admin Mode: You can now change unit images</p>}
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
                <h2>Available Storage Units</h2>
                <p>{virtualUnits.length} units match your criteria</p>
              </div>

              <div className="units-grid">
                {virtualUnits.map(unit => (
                  <UnitCard
                    key={unit.id}
                    unit={unit}
                    onBook={handleBookUnit}
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

      {/* Features Section */}
      <section className="features">
        <h2>Why Choose Our Storage?</h2>
        <div className="features-grid">
          <div className="feature">
            <img src="https://images.unsplash.com/photo-1551313158-73d016a829ae" alt="Secure Storage" />
            <h3>Secure & Safe</h3>
            <p>24/7 security monitoring and controlled access</p>
          </div>
          <div className="feature">
            <img src="https://images.pexels.com/photos/13388790/pexels-photo-13388790.jpeg" alt="Flexible Options" />
            <h3>Flexible Booking</h3>
            <p>Pay now or later, move in when convenient</p>
          </div>
          <div className="feature">
            <img src="https://images.unsplash.com/photo-1711130361680-a3beb1369ef5" alt="Multiple Sizes" />
            <h3>Multiple Sizes</h3>
            <p>From small boats to large RVs, we have space for everything</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default App;