import { useToggle } from './useToggle';

/**
 * A custom hook for managing definitions window visibility state.
 * @param {boolean} initialState - Initial visibility state, defaults to false
 * @returns {Array} Array containing [isActive, toggle] where toggle is a function to toggle the state
 */
const useDefinitionsWindow = (initialState = false) => {
  const [isDefinitionsWindowActive, toggleDefinitionsWindow] = useToggle(initialState);
  return [isDefinitionsWindowActive, toggleDefinitionsWindow];
};

export { useDefinitionsWindow };
