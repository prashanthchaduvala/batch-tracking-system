import { useState, useEffect, useCallback } from 'react';
import { batchService } from '../services/api';

const useBatches = (initialFilters = {}) => {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState(initialFilters);
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    pageSize: 20,
  });
  const [optimisticUpdates, setOptimisticUpdates] = useState({});

  const fetchBatches = useCallback(async (page = 1, appliedFilters = filters) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await batchService.getBatches(appliedFilters, page);
      setBatches(response.data.results || response.data);
      
      // Handle pagination if present
      if (response.data.count !== undefined) {
        setPagination({
          currentPage: page,
          totalPages: Math.ceil(response.data.count / 20),
          totalItems: response.data.count,
          pageSize: 20,
        });
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch batches');
      
      // Handle specific error cases
      if (err.response?.status === 401) {
        setError('Your session has expired. Please log in again.');
      }
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Optimistic status update
  const updateStatusOptimistically = useCallback(async (id, newStatus) => {
    // Store original state for rollback
    const originalBatches = [...batches];
    const originalBatch = batches.find(b => b.id === id);
    
    // Optimistically update UI
    setBatches(prev => prev.map(batch => 
      batch.id === id ? { ...batch, status: newStatus } : batch
    ));
    
    try {
      const response = await batchService.updateStatus(id, newStatus);
      // Update with server response
      setBatches(prev => prev.map(batch =>
        batch.id === id ? response.data : batch
      ));
      setOptimisticUpdates(prev => ({ ...prev, [id]: null }));
    } catch (err) {
      // Rollback on failure
      setBatches(originalBatches);
      setError(`Failed to update status: ${err.response?.data?.error || err.message}`);
      return Promise.reject(err);
    }
  }, [batches]);

  useEffect(() => {
    fetchBatches(1);
  }, [fetchBatches]);

  return {
    batches,
    loading,
    error,
    filters,
    setFilters,
    pagination,
    fetchBatches,
    updateStatusOptimistically,
    clearError: () => setError(null),
  };
};

export default useBatches;