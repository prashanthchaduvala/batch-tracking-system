import React, { useState } from 'react';
import BatchFilter from './BatchFilter';
import BatchStatusBadge from './BatchStatusBadge';
import useBatches from '../hooks/useBatches';

const BatchList = () => {
  const {
    batches,
    loading,
    error,
    filters,
    setFilters,
    pagination,
    fetchBatches,
    updateStatusOptimistically,
    clearError,
  } = useBatches();

  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');

  const handleFilter = (newFilters) => {
    setFilters(newFilters);
  };

  const handlePageChange = (page) => {
    fetchBatches(page);
  };

  const handleStatusChange = async (id, newStatus) => {
    try {
      await updateStatusOptimistically(id, newStatus);
    } catch (error) {
      // Error already handled in hook with rollback
    }
  };

  if (loading && batches.length === 0) {
    return (
      <div className="loading-container">
        <div className="loader">Loading batches...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p className="error-message">{error}</p>
        <button onClick={clearError} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="batch-list-container">
      <div className="header">
        <h1>Diagnostic Batches</h1>
      </div>

      <BatchFilter 
        filters={filters}
        onFilterChange={handleFilter}
      />

      {batches.length === 0 && !loading ? (
        <div className="empty-state">
          <p>No batches found matching your criteria.</p>
        </div>
      ) : (
        <>
          <div className="batch-grid">
            {batches.map((batch) => (
              <div key={batch.id} className="batch-card">
                <div className="batch-header">
                  <h3>Batch {batch.sample_id}</h3>
                  <BatchStatusBadge status={batch.status} />
                </div>
                <div className="batch-details">
                  <p><strong>Type:</strong> {batch.batch_type}</p>
                  <p><strong>Submitted by:</strong> {batch.submitted_by}</p>
                  <p><strong>Created:</strong> {new Date(batch.created_at).toLocaleDateString()}</p>
                  {batch.result && (
                    <p><strong>Result:</strong> {JSON.stringify(batch.result)}</p>
                  )}
                </div>
                <div className="batch-actions">
                  <select 
                    value={batch.status}
                    onChange={(e) => handleStatusChange(batch.id, e.target.value)}
                    disabled={loading}
                  >
                    <option value="queued">Queued</option>
                    <option value="processing">Processing</option>
                    <option value="completed">Completed</option>
                    <option value="failed">Failed</option>
                  </select>
                </div>
              </div>
            ))}
          </div>

          {pagination.totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => handlePageChange(pagination.currentPage - 1)}
                disabled={pagination.currentPage === 1}
              >
                Previous
              </button>
              <span>
                Page {pagination.currentPage} of {pagination.totalPages}
              </span>
              <button
                onClick={() => handlePageChange(pagination.currentPage + 1)}
                disabled={pagination.currentPage === pagination.totalPages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default BatchList;