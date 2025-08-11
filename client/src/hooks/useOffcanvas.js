import { useToggle } from './useToggle';

/**
 * A custom hook for managing offcanvas visibility state.
 * @param {boolean} initialState - Initial visibility state, defaults to false
 * @returns {Array} Array containing [isActive, toggle] where toggle is a function to toggle the state
 */
const useOffcanvas = (initialState = false) => {
  const [isOffcanvasActive, toggleOffcanvas] = useToggle(initialState);
  return [isOffcanvasActive, toggleOffcanvas];
};

export { useOffcanvas };