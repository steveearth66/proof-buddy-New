import React from 'react';
import Form from 'react-bootstrap/Form';
import './RacketInput.scss';

/**
 * A Form.Control wrapper that highlights matching parentheses
 * @param {Object} props - All Form.Control props plus highlightPositions and inputRef
 */
const RacketInput = React.forwardRef(({
  value = '',
  highlightPositions = [],
  onKeyUp,
  onClick,
  ...otherProps
}, ref) => {
  
  const handleClick = (e) => {
    if (onClick) onClick(e);
  };

  return (
    <div className="racket-input-wrapper" style={{ width: '100%', display: 'block' }}>
      <div className="racket-input-highlight-layer">
        <div className="highlight-content">
          {value.split('').map((char, index) => {
            const isHighlighted = highlightPositions.includes(index);
            return (
              <span
                key={index}
                className={isHighlighted ? 'highlight-paren' : ''}
              >
                {char}
              </span>
            );
          })}
        </div>
      </div>
      <Form.Control
        {...otherProps}
        ref={ref}
        value={value}
        onKeyUp={onKeyUp}
        onClick={handleClick}
        className="racket-input-field"
      />
    </div>
  );
});

RacketInput.displayName = 'RacketInput';

export default RacketInput;
