import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const AdminLocations = () => {
  const [locations, setLocations] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [showAddLocation, setShowAddLocation] = useState(false);
  const [newLocation, setNewLocation] = useState({
    name: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    phone: '',
    email: '',
    manager_name: '',
    description: '',
    amenities: [],
    hours_of_operation: {
      monday: '6AM-10PM',
      tuesday: '6AM-10PM',
      wednesday: '6AM-10PM',
      thursday: '6AM-10PM',
      friday: '6AM-10PM',
      saturday: '7AM-9PM',
      sunday: '8AM-8PM'
    }
  });

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API}/locations`);
      setLocations(response.data);
    } catch (err) {
      console.error('Failed to fetch locations:', err);
    }
  };

  const createLocation = async () => {
    try {
      await axios.post(`${API}/locations`, newLocation);
      setNewLocation({
        name: '',
        address: '',
        city: '',
        state: '',
        zip_code: '',
        phone: '',
        email: '',
        manager_name: '',
        description: '',
        amenities: [],
        hours_of_operation: {
          monday: '6AM-10PM',
          tuesday: '6AM-10PM',
          wednesday: '6AM-10PM',
          thursday: '6AM-10PM',
          friday: '6AM-10PM',
          saturday: '7AM-9PM',
          sunday: '8AM-8PM'
        }
      });
      setShowAddLocation(false);
      fetchLocations();
    } catch (err) {
      alert('Failed to create location: ' + (err.response?.data?.detail || err.message));
    }
  };

  const updateLocation = async (locationId, updatedLocation) => {
    try {
      await axios.put(`${API}/locations/${locationId}`, updatedLocation);
      fetchLocations();
      setSelectedLocation(null);
    } catch (err) {
      alert('Failed to update location: ' + (err.response?.data?.detail || err.message));
    }
  };

  const toggleAmenity = (amenity) => {
    const current = newLocation.amenities;
    if (current.includes(amenity)) {
      setNewLocation({
        ...newLocation,
        amenities: current.filter(a => a !== amenity)
      });
    } else {
      setNewLocation({
        ...newLocation,
        amenities: [...current, amenity]
      });
    }
  };

  const updateHours = (day, hours) => {
    setNewLocation({
      ...newLocation,
      hours_of_operation: {
        ...newLocation.hours_of_operation,
        [day]: hours
      }
    });
  };

  const availableAmenities = [
    '24/7_access', 'security_cameras', 'gated', 'climate_control',
    'boat_launch', 'power_washing', 'covered_parking', 'electric_hookup',
    'dump_station', 'security_patrol', 'office_on_site', 'restrooms'
  ];

  useEffect(() => {
    fetchLocations();
  }, []);

  return (
    <div className="locations-tab">
      <h3>🏢 Location Management</h3>
      
      <div className="locations-controls">
        <button 
          onClick={() => setShowAddLocation(true)}
          className="add-location-btn"
        >
          ➕ Add New Location
        </button>
      </div>

      <div className="locations-grid">
        {locations.map(location => (
          <div key={location.id} className="location-card">
            <div className="location-header">
              <h4>{location.name}</h4>
              <span className={`status-badge ${location.is_active ? 'active' : 'inactive'}`}>
                {location.is_active ? '🟢 Active' : '🔴 Inactive'}
              </span>
            </div>
            
            <div className="location-details">
              <p className="address">
                📍 {location.address}, {location.city}, {location.state} {location.zip_code}
              </p>
              <p className="contact">
                📞 {location.phone} | 📧 {location.email}
              </p>
              {location.manager_name && (
                <p className="manager">👤 Manager: {location.manager_name}</p>
              )}
              <p className="description">{location.description}</p>
            </div>

            <div className="location-amenities">
              <h5>Amenities:</h5>
              <div className="amenities-list">
                {location.amenities.map(amenity => (
                  <span key={amenity} className="amenity-tag">
                    {amenity.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>

            <div className="location-hours">
              <h5>Hours:</h5>
              <div className="hours-summary">
                <span>Mon-Fri: {location.hours_of_operation?.monday || 'N/A'}</span>
                <span>Sat: {location.hours_of_operation?.saturday || 'N/A'}</span>
                <span>Sun: {location.hours_of_operation?.sunday || 'N/A'}</span>
              </div>
            </div>

            <div className="location-actions">
              <button 
                onClick={() => setSelectedLocation(location)}
                className="edit-location-btn"
              >
                ✏️ Edit
              </button>
              <button 
                onClick={() => updateLocation(location.id, {...location, is_active: !location.is_active})}
                className="toggle-status-btn"
              >
                {location.is_active ? '⏸️ Deactivate' : '▶️ Activate'}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Add/Edit Location Modal */}
      {(showAddLocation || selectedLocation) && (
        <div className="modal-overlay">
          <div className="modal-content large-modal">
            <h3>{showAddLocation ? 'Add New Location' : 'Edit Location'}</h3>
            
            <div className="location-form">
              <div className="form-section">
                <h4>Basic Information</h4>
                <div className="form-row">
                  <input
                    type="text"
                    placeholder="Location Name"
                    value={showAddLocation ? newLocation.name : selectedLocation?.name || ''}
                    onChange={(e) => {
                      if (showAddLocation) {
                        setNewLocation({...newLocation, name: e.target.value});
                      } else {
                        setSelectedLocation({...selectedLocation, name: e.target.value});
                      }
                    }}
                  />
                  <input
                    type="text"
                    placeholder="Manager Name"
                    value={showAddLocation ? newLocation.manager_name : selectedLocation?.manager_name || ''}
                    onChange={(e) => {
                      if (showAddLocation) {
                        setNewLocation({...newLocation, manager_name: e.target.value});
                      } else {
                        setSelectedLocation({...selectedLocation, manager_name: e.target.value});
                      }
                    }}
                  />
                </div>
                
                <input
                  type="text"
                  placeholder="Address"
                  value={showAddLocation ? newLocation.address : selectedLocation?.address || ''}
                  onChange={(e) => {
                    if (showAddLocation) {
                      setNewLocation({...newLocation, address: e.target.value});
                    } else {
                      setSelectedLocation({...selectedLocation, address: e.target.value});
                    }
                  }}
                />
                
                <div className="form-row">
                  <input
                    type="text"
                    placeholder="City"
                    value={showAddLocation ? newLocation.city : selectedLocation?.city || ''}
                    onChange={(e) => {
                      if (showAddLocation) {
                        setNewLocation({...newLocation, city: e.target.value});
                      } else {
                        setSelectedLocation({...selectedLocation, city: e.target.value});
                      }
                    }}
                  />
                  <input
                    type="text"
                    placeholder="State"
                    value={showAddLocation ? newLocation.state : selectedLocation?.state || ''}
                    onChange={(e) => {
                      if (showAddLocation) {
                        setNewLocation({...newLocation, state: e.target.value});
                      } else {
                        setSelectedLocation({...selectedLocation, state: e.target.value});
                      }
                    }}
                  />
                  <input
                    type="text"
                    placeholder="ZIP Code"
                    value={showAddLocation ? newLocation.zip_code : selectedLocation?.zip_code || ''}
                    onChange={(e) => {
                      if (showAddLocation) {
                        setNewLocation({...newLocation, zip_code: e.target.value});
                      } else {
                        setSelectedLocation({...selectedLocation, zip_code: e.target.value});
                      }
                    }}
                  />
                </div>
                
                <div className="form-row">
                  <input
                    type="tel"
                    placeholder="Phone"
                    value={showAddLocation ? newLocation.phone : selectedLocation?.phone || ''}
                    onChange={(e) => {
                      if (showAddLocation) {
                        setNewLocation({...newLocation, phone: e.target.value});
                      } else {
                        setSelectedLocation({...selectedLocation, phone: e.target.value});
                      }
                    }}
                  />
                  <input
                    type="email"
                    placeholder="Email"
                    value={showAddLocation ? newLocation.email : selectedLocation?.email || ''}
                    onChange={(e) => {
                      if (showAddLocation) {
                        setNewLocation({...newLocation, email: e.target.value});
                      } else {
                        setSelectedLocation({...selectedLocation, email: e.target.value});
                      }
                    }}
                  />
                </div>
                
                <textarea
                  placeholder="Description"
                  value={showAddLocation ? newLocation.description : selectedLocation?.description || ''}
                  onChange={(e) => {
                    if (showAddLocation) {
                      setNewLocation({...newLocation, description: e.target.value});
                    } else {
                      setSelectedLocation({...selectedLocation, description: e.target.value});
                    }
                  }}
                />
              </div>

              <div className="form-section">
                <h4>Amenities</h4>
                <div className="amenities-selection">
                  {availableAmenities.map(amenity => (
                    <label key={amenity} className="amenity-checkbox">
                      <input
                        type="checkbox"
                        checked={showAddLocation ? 
                          newLocation.amenities.includes(amenity) : 
                          selectedLocation?.amenities?.includes(amenity) || false
                        }
                        onChange={() => {
                          if (showAddLocation) {
                            toggleAmenity(amenity);
                          } else {
                            const current = selectedLocation?.amenities || [];
                            if (current.includes(amenity)) {
                              setSelectedLocation({
                                ...selectedLocation,
                                amenities: current.filter(a => a !== amenity)
                              });
                            } else {
                              setSelectedLocation({
                                ...selectedLocation,
                                amenities: [...current, amenity]
                              });
                            }
                          }
                        }}
                      />
                      {amenity.replace('_', ' ')}
                    </label>
                  ))}
                </div>
              </div>

              <div className="form-section">
                <h4>Hours of Operation</h4>
                <div className="hours-grid">
                  {['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].map(day => (
                    <div key={day} className="hours-row">
                      <label>{day.charAt(0).toUpperCase() + day.slice(1)}</label>
                      <input
                        type="text"
                        placeholder="e.g., 6AM-10PM"
                        value={showAddLocation ? 
                          newLocation.hours_of_operation[day] : 
                          selectedLocation?.hours_of_operation?.[day] || ''
                        }
                        onChange={(e) => {
                          if (showAddLocation) {
                            updateHours(day, e.target.value);
                          } else {
                            setSelectedLocation({
                              ...selectedLocation,
                              hours_of_operation: {
                                ...selectedLocation.hours_of_operation,
                                [day]: e.target.value
                              }
                            });
                          }
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="modal-actions">
                <button 
                  onClick={() => {
                    setShowAddLocation(false);
                    setSelectedLocation(null);
                  }} 
                  className="cancel-btn"
                >
                  Cancel
                </button>
                <button 
                  onClick={() => {
                    if (showAddLocation) {
                      createLocation();
                    } else {
                      updateLocation(selectedLocation.id, selectedLocation);
                    }
                  }} 
                  className="save-btn"
                >
                  {showAddLocation ? 'Create Location' : 'Update Location'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminLocations;