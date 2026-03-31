/**
 * playModeUtils.js
 *
 * Pure functions for managing "Play Mode" state in proof pages.
 *
 * Play state structure:
 *   {
 *     base: { LHS: { active: bool, lineIndex: int }, RHS: { active: bool, lineIndex: int } },
 *     leap: { LHS: { active: bool, lineIndex: int }, RHS: { active: bool, lineIndex: int } }
 *   }
 *
 * - EquationalReasoningNew.js uses only the 'base' case key.
 * - InductionRacket.js uses both 'base' (anchor/base case) and 'leap' (leap step).
 * - lineIndex: the highest line index (0-based) currently visible.
 *     Index 0 = only the premise is shown.
 *     Index 1 = premise + first proof line shown. Etc.
 * - active: true while the user has not yet seen all lines for that case+side.
 */

/**
 * Create an initial play state for the given case keys and sides.
 *
 * @param {string[]} caseKeys - e.g. ['base'] for ER, ['base', 'leap'] for Induction
 * @param {string[]} sides    - e.g. ['LHS', 'RHS']
 * @param {boolean}  active   - true when entering play mode, false for normal open
 * @returns {object} playState
 */
function initPlayState(caseKeys, sides, active = false) {
  const state = {};
  for (const caseKey of caseKeys) {
    state[caseKey] = {};
    for (const side of sides) {
      state[caseKey][side] = { active, lineIndex: 0 };
    }
  }
  return state;
}

/**
 * Retrieve the play entry for a specific case and side.
 *
 * @param {object} playState
 * @param {string} caseKey - 'base' or 'leap'
 * @param {string} side    - 'LHS' or 'RHS'
 * @returns {{ active: boolean, lineIndex: number }}
 */
function getPlayEntry(playState, caseKey, side) {
  return playState?.[caseKey]?.[side] ?? { active: false, lineIndex: 0 };
}

/**
 * Given the racketRuleFields array for a side, return the index of the last
 * line that has actual content (non-empty racket, not deleted).
 * The trailing empty field is excluded.
 *
 * @param {Array} fields - racketRuleFields[side]
 * @returns {number} lastRealIndex, or 0 if only the premise exists
 */
function getLastRealIndex(fields) {
  if (!fields || fields.length === 0) return 0;
  for (let i = fields.length - 1; i >= 0; i--) {
    const f = fields[i];
    if (f && !f.deleted && f.racket && f.racket.trim() !== '') {
      return i;
    }
  }
  return 0;
}

/**
 * Advance play mode by one line.
 * If the resulting lineIndex equals lastRealIndex, deactivate play mode for that entry
 * (the user has now seen all lines).
 *
 * @param {object} playState
 * @param {string} caseKey
 * @param {string} side
 * @param {number} lastRealIndex - index of the last line with content
 * @returns {object} new playState (immutable update)
 */
function advancePlay(playState, caseKey, side, lastRealIndex) {
  const entry = getPlayEntry(playState, caseKey, side);
  if (!entry.active) return playState;
  const newLineIndex = entry.lineIndex + 1;
  const nowComplete = newLineIndex >= lastRealIndex;
  return {
    ...playState,
    [caseKey]: {
      ...playState[caseKey],
      [side]: {
        active: !nowComplete,
        lineIndex: newLineIndex
      }
    }
  };
}

/**
 * Cancel play mode for a specific case+side, immediately revealing all lines.
 * Sets active to false; lineIndex is set to Infinity so visibleLineCount returns null.
 *
 * @param {object} playState
 * @param {string} caseKey
 * @param {string} side
 * @returns {object} new playState
 */
function cancelPlay(playState, caseKey, side) {
  return {
    ...playState,
    [caseKey]: {
      ...playState[caseKey],
      [side]: { active: false, lineIndex: Infinity }
    }
  };
}

/**
 * Whether play mode is currently active for a specific case+side.
 *
 * @param {object} playState
 * @param {string} caseKey
 * @param {string} side
 * @returns {boolean}
 */
function isActive(playState, caseKey, side) {
  return getPlayEntry(playState, caseKey, side).active === true;
}

/**
 * How many lines should be visible for a case+side.
 * Returns null if play mode is not active (meaning show all lines).
 * Returns lineIndex + 1 if active (show lines 0..lineIndex inclusive).
 *
 * @param {object} playState
 * @param {string} caseKey
 * @param {string} side
 * @returns {number|null} count of lines to show, or null for "show all"
 */
function visibleLineCount(playState, caseKey, side) {
  const entry = getPlayEntry(playState, caseKey, side);
  if (!entry.active) return null;
  return entry.lineIndex + 1;
}

/**
 * Whether the "Continue" button should be shown for a case+side.
 * True when: play mode is active AND the next line (lineIndex+1) exists
 * and has content (i.e., lineIndex < lastRealIndex).
 *
 * @param {object} playState
 * @param {string} caseKey
 * @param {string} side
 * @param {number} lastRealIndex
 * @returns {boolean}
 */
function showContinue(playState, caseKey, side, lastRealIndex) {
  const entry = getPlayEntry(playState, caseKey, side);
  return entry.active && entry.lineIndex < lastRealIndex;
}

export {
  initPlayState,
  getPlayEntry,
  getLastRealIndex,
  advancePlay,
  cancelPlay,
  isActive,
  visibleLineCount,
  showContinue
};
