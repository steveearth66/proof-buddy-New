import React from 'react';

/**
 * ClickableRowNumber component renders a clickable row number with hover effects
 * @param {Object} props - Component props
 * @param {number} props.padIndex - The row index to display
 * @param {boolean} props.isClickable - Whether the row number should be clickable
 * @param {function} props.onClick - Click handler function
 * @param {string} props.title - Tooltip text
 */
const ClickableRowNumber = ({ padIndex, isClickable, onClick, title }) => {
  return (
    <div 
      className={`main-grid-column ${isClickable ? 'clickable-row-number' : ''}`}
      onClick={() => isClickable && onClick()}
      title={title}
      style={{
        cursor: isClickable ? 'pointer' : 'default',
        userSelect: 'none',
        transition: 'all 0.2s ease',
        borderRadius: '4px',
        padding: '8px',
        backgroundColor: isClickable ? '#f8f9fa' : 'transparent',
        border: isClickable ? '1px solid #dee2e6' : '1px solid transparent'
      }}
      onMouseEnter={(e) => {
        if (isClickable) {
          e.target.style.backgroundColor = '#e9ecef';
          e.target.style.borderColor = '#adb5bd';
          e.target.style.transform = 'translateY(-1px)';
          e.target.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
        }
      }}
      onMouseLeave={(e) => {
        if (isClickable) {
          e.target.style.backgroundColor = '#f8f9fa';
          e.target.style.borderColor = '#dee2e6';
          e.target.style.transform = 'translateY(0)';
          e.target.style.boxShadow = 'none';
        }
      }}
    >
      {padIndex.toString().padStart(3, "0")}
    </div>
  );
};

export default ClickableRowNumber;
