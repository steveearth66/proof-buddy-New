/**
 * Find the matching parenthesis for a given position in a string
 * @param {string} text - The input text
 * @param {number} position - The position of the parenthesis to match
 * @returns {number} - The index of the matching parenthesis, or -1 if not found
 */
export const findMatchingParen = (text, position) => {
  if (!text || position < 0 || position >= text.length) {
    return -1;
  }

  const char = text[position];
  
  // Determine if we're matching forward or backward
  let isOpening = false;
  let openChar, closeChar;
  
  if (char === '(') {
    isOpening = true;
    openChar = '(';
    closeChar = ')';
  } else if (char === ')') {
    isOpening = false;
    openChar = '(';
    closeChar = ')';
  } else {
    // Not a parenthesis
    return -1;
  }

  let count = 1;
  let step = isOpening ? 1 : -1;
  let i = position + step;

  while (i >= 0 && i < text.length) {
    if (text[i] === openChar) {
      count += isOpening ? 1 : -1;
    } else if (text[i] === closeChar) {
      count += isOpening ? -1 : 1;
    }

    if (count === 0) {
      return i;
    }

    i += step;
  }

  // No matching parenthesis found
  return -1;
};

/**
 * Get all parenthesis positions in a string for visualization
 * @param {string} text - The input text
 * @returns {Array} - Array of objects with {index, char, matchIndex}
 */
export const getAllParenPositions = (text) => {
  if (!text) return [];
  
  const positions = [];
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '(' || text[i] === ')') {
      positions.push({
        index: i,
        char: text[i],
        matchIndex: findMatchingParen(text, i)
      });
    }
  }
  return positions;
};
