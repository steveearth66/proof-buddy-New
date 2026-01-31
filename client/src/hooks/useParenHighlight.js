import { useState, useEffect, useRef } from 'react';
import { findMatchingParen } from '../utils/parenthesisMatching';

/**
 * Custom hook to manage parenthesis highlighting in text inputs
 * @param {string} value - The current input value
 * @returns {Object} - { highlightPositions, inputRef, handleInputChange, handleKeyUp }
 */
export const useParenHighlight = (value) => {
  const [highlightPositions, setHighlightPositions] = useState([]);
  const inputRef = useRef(null);
  const timeoutRef = useRef(null);

  /**
   * Handle key up events to detect when ')' is typed
   */
  const handleKeyUp = (e) => {
    const input = inputRef.current;
    if (!input) return;

    const cursorPos = input.selectionStart;
    const char = value[cursorPos - 1];

    // Check if user just typed a closing parenthesis
    if (char === ')') {
      const matchIdx = findMatchingParen(value, cursorPos - 1);
      
      if (matchIdx >= 0) {
        // Found a match - highlight both positions
        setHighlightPositions([matchIdx, cursorPos - 1]);
      } else {
        // No match found - could highlight just the closing paren in red
        setHighlightPositions([cursorPos - 1]);
      }
    } else {
      // Clear highlights on any other key
      setHighlightPositions([]);
    }
  };

  /**
   * Handle selection change to highlight matching parens on click/selection
   */
  const handleSelect = () => {
    const input = inputRef.current;
    if (!input) return;

    const cursorPos = input.selectionStart;
    const selectionLength = input.selectionEnd - input.selectionStart;

    // Only highlight if single cursor position (no text selected)
    if (selectionLength === 0 && cursorPos > 0 && cursorPos <= value.length) {
      // Check character before cursor
      const charBefore = value[cursorPos - 1];
      // Check character at cursor
      const charAt = value[cursorPos];

      let targetPos = -1;
      
      if (charBefore === '(' || charBefore === ')') {
        targetPos = cursorPos - 1;
      } else if (charAt === '(' || charAt === ')') {
        targetPos = cursorPos;
      }

      if (targetPos >= 0) {
        const matchIdx = findMatchingParen(value, targetPos);
        if (matchIdx >= 0) {
          setHighlightPositions([targetPos, matchIdx]);
        } else {
          setHighlightPositions([targetPos]);
        }
      } else {
        setHighlightPositions([]);
      }
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    highlightPositions,
    inputRef,
    handleKeyUp,
    handleSelect
  };
};
