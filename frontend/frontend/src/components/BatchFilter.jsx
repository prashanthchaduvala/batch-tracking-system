import React, { useState } from 'react';

const BatchFilter = ({ filters, onFilterChange }) => {
  const [status, setStatus] = useState(filters.status || '');
  const [type, setType] = useState(filters.type || '');

  const handleSubmit = (e) => {
    e.preventDefault();
    const newFilters = {};
    if (status) newFilters.status = status;
    if (type) newFilters.type = type;
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    setStatus('');
    setType('');
    onFilterChange({});
  };

  return (
    <form onSubmit={handleSubmit} className="filter-form">
      <div className="filter-group">
        <label htmlFor="status-filter">Status</label>
        <select
          id="status-filter"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="filter-select"
        >
          <option value="">All Statuses</option>
          <option value="queued">Queued</option>
          <option value="processing">Processing</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="type-filter">Batch Type</label>
        <input
          id="type-filter"
          type="text"
          value={type}
          onChange={(e) => setType(e.target.value)}
          placeholder="Filter by type..."
          className="filter-input"
        />
      </div>

      <div className="filter-actions">
        <button type="submit" className="btn-primary">Apply Filters</button>
        <button type="button" onClick={handleReset} className="btn-secondary">
          Reset
        </button>
      </div>
    </form>
  );
};

export default BatchFilter;