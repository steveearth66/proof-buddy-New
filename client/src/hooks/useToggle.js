import { useState } from 'react';

/**
 * A generic custom hook for managing boolean toggle states.
 * @param {boolean} initialState - Initial state value, defaults to false
 * @returns {Array} Array containing [state, toggle] where toggle is a function to toggle the state
 */
const useToggle = (initialState = false) => {
  const [state, setState] = useState(initialState);

  const toggle = () => setState(prev => !prev);
  const setTrue = () => setState(true);
  const setFalse = () => setState(false);

  return [state, toggle, setTrue, setFalse];
};

export { useToggle };
