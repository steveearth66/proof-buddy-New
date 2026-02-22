import { useState, useMemo } from 'react';

export default function useSortableTable(data, initialConfig = null) {
  const [sortConfig, setSortConfig] = useState(initialConfig);

  // 1. Sort the data based on the current config
  const sortedData = useMemo(() => {
    let sortableItems = [...data];

    if (sortConfig !== null && sortConfig.direction !== 'none') {
      sortableItems.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // Handle specific edge cases like dates automatically
        if (sortConfig.key.toLowerCase().includes('date')) {
          aValue = new Date(aValue);
          bValue = new Date(bValue);
        }

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return sortableItems;
  }, [data, sortConfig]);

  // 2. The function to call when a header is clicked
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig && sortConfig.key === key) {
      if (sortConfig.direction === 'asc') direction = 'desc';
      else if (sortConfig.direction === 'desc') direction = 'none';
    }
    setSortConfig({ key, direction });
  };

  // 3. The function to get the correct FontAwesome icon
  const getSortIcon = (key) => {
    if (!sortConfig || sortConfig.key !== key || sortConfig.direction === 'none') {
      return "fa-solid fa-sort text-muted";
    }
    return sortConfig.direction === 'asc'
      ? 'fa-solid fa-sort-up text-primary'
      : 'fa-solid fa-sort-down text-primary';
  };

  // 4. Utility to prevent highlight on double-click
  const handleMouseDown = (e) => {
    if (e.detail > 1) e.preventDefault();
  };

  return {
    sortedData,
    handleSort,
    getSortIcon,
    handleMouseDown,
    sortConfig
  };
}