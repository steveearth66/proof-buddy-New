/**
 * playMode.test.js
 *
 * Automated unit tests for playModeUtils.js.
 *
 * Run with:
 *   npm test -- --testPathPattern=playMode
 *
 * These tests cover the pure logic of play-mode state transitions.
 * No React, no DOM, no mock needed.
 *
 * ─────────────────────────────────────────────────
 * MANUAL TEST CHECKLIST (run after each UI step)
 * ─────────────────────────────────────────────────
 *
 * AFTER STEP 1 (Run Proof button in ProofCard):
 *   [ ] Open /proofs — each card shows "Open Proof" AND "▶ Run Proof" buttons
 *   [ ] "Open Proof" still works exactly as before (no regression)
 *   [ ] "▶ Run Proof" navigates to the proof page (proof loads, play mode not active yet)
 *   [ ] Button has a sideways-triangle (play) icon and the text "Run Proof"
 *
 * AFTER STEP 3 (ER: play state + line filtering + Continue button):
 *   [ ] Open an ER proof that has at least 3 proof lines via "Run Proof"
 *   [ ] Only line 000 (premise) is visible on arrival
 *   [ ] A "▶ Continue" button appears below the premise
 *   [ ] Click Continue → line 001 appears; Continue button moves below it
 *   [ ] Click Continue again → line 002 appears; repeat until last line
 *   [ ] After last line appears, Continue button is gone
 *   [ ] Opening the same proof via "Open Proof" shows all lines immediately (no regression)
 *   [ ] Refreshing the page while in play mode → returns to normal open (play mode is nav-state only)
 *
 * AFTER STEP 4 (ER: disable footer + Cancel button):
 *   [ ] In play mode: row-number input, Fill Values button, Generate & Check are all greyed out
 *   [ ] Clicking anywhere in the footer while in play mode has no effect
 *   [ ] A "✕ Cancel Play Mode" button is visible next to the proof content area
 *   [ ] Clicking "✕ Cancel Play Mode" reveals ALL remaining lines for the current side instantly
 *   [ ] After canceling: footer is fully active again, Cancel button disappears
 *   [ ] After the last Continue is clicked (all lines revealed): footer becomes active, Cancel disappears
 *
 * AFTER STEP 5 (ER: side-switching):
 *   [ ] Open ER proof via Run Proof; advance LHS to line 002 (showing premise + 2 lines)
 *   [ ] Switch to RHS → RHS starts fresh at line 000 (only premise visible, Continue shown)
 *   [ ] Switch back to LHS → still shows lines 000-002, Continue button for line 003 (or none if done)
 *   [ ] Complete LHS play mode (all lines revealed); switch to RHS and back to LHS
 *       → LHS has NO play mode, all lines visible, footer active
 *   [ ] Cancel RHS play mode; switch back to LHS and then RHS → RHS stays non-play-mode
 *
 * AFTER STEP 6 (Induction: base/leap dimension):
 *   [ ] Open an Induction proof via Run Proof — Base Case LHS starts with only premise
 *   [ ] Advance Base LHS partway; switch to Base RHS → Base RHS starts at line 000
 *   [ ] Switch to Leap step → Leap LHS starts at line 000 in play mode
 *   [ ] Switch Leap LHS/RHS, come back → progress preserved
 *   [ ] Return to Base LHS → still at progress point from earlier
 *   [ ] Complete Base LHS and Base RHS; switch to Leap LHS and cancel play mode there
 *   [ ] All four combinations (base/LHS, base/RHS, leap/LHS, leap/RHS) behave independently
 */

import {
  initPlayState,
  getPlayEntry,
  getLastRealIndex,
  advancePlay,
  cancelPlay,
  isActive,
  visibleLineCount,
  showContinue
} from '../utils/playModeUtils';

// ─── helpers ─────────────────────────────────────────────────────────────────

/** Build a minimal fields array: premise + N content lines + 1 empty trailing. */
function makeFields(contentLineCount) {
  const fields = [];
  // index 0 = premise
  fields.push({ racket: '(f 0)', rule: 'Premise', deleted: false });
  for (let i = 1; i <= contentLineCount; i++) {
    fields.push({ racket: `(expr ${i})`, rule: `rule${i}`, deleted: false });
  }
  // trailing empty field (always present)
  fields.push({ racket: '', rule: '', deleted: false });
  return fields;
}

// ─── initPlayState ────────────────────────────────────────────────────────────

describe('initPlayState', () => {
  test('creates inactive state when active=false (normal open)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], false);
    expect(state.base.LHS).toEqual({ active: false, lineIndex: 0 });
    expect(state.base.RHS).toEqual({ active: false, lineIndex: 0 });
  });

  test('creates active state when active=true (play mode open)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(state.base.LHS.active).toBe(true);
    expect(state.base.RHS.active).toBe(true);
  });

  test('creates all four case+side entries for induction', () => {
    const state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    expect(state.base.LHS.active).toBe(true);
    expect(state.base.RHS.active).toBe(true);
    expect(state.leap.LHS.active).toBe(true);
    expect(state.leap.RHS.active).toBe(true);
  });

  test('all lineIndex values start at 0', () => {
    const state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    expect(state.base.LHS.lineIndex).toBe(0);
    expect(state.leap.RHS.lineIndex).toBe(0);
  });
});

// ─── getLastRealIndex ─────────────────────────────────────────────────────────

describe('getLastRealIndex', () => {
  test('returns 0 for empty array', () => {
    expect(getLastRealIndex([])).toBe(0);
  });

  test('returns 0 when only premise exists (no proof lines yet)', () => {
    // fields: [premise, empty trailing]
    const fields = makeFields(0);
    expect(getLastRealIndex(fields)).toBe(0);
  });

  test('returns correct index for 3 content lines (lastRealIndex = 3)', () => {
    const fields = makeFields(3); // indices 0,1,2,3 have content; 4 is empty trailing
    expect(getLastRealIndex(fields)).toBe(3);
  });

  test('skips deleted lines', () => {
    const fields = makeFields(3);
    fields[3].deleted = true; // mark last content line as deleted
    expect(getLastRealIndex(fields)).toBe(2);
  });

  test('skips empty-racket lines', () => {
    const fields = makeFields(2);
    fields[2].racket = '   '; // whitespace only = empty
    expect(getLastRealIndex(fields)).toBe(1);
  });
});

// ─── advancePlay ─────────────────────────────────────────────────────────────

describe('advancePlay', () => {
  test('increments lineIndex by 1', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = advancePlay(state, 'base', 'LHS', 3);
    expect(next.base.LHS.lineIndex).toBe(1);
    expect(next.base.LHS.active).toBe(true);
  });

  test('deactivates when lineIndex reaches lastRealIndex', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    // Start at index 2, lastRealIndex = 3: next = 3 which equals lastRealIndex → deactivate
    const stateAt2 = { base: { LHS: { active: true, lineIndex: 2 }, RHS: { active: true, lineIndex: 0 } } };
    const next = advancePlay(stateAt2, 'base', 'LHS', 3);
    expect(next.base.LHS.lineIndex).toBe(3);
    expect(next.base.LHS.active).toBe(false);
  });

  test('does not change state when already inactive', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], false);
    const next = advancePlay(state, 'base', 'LHS', 3);
    expect(next.base.LHS).toEqual(state.base.LHS);
  });

  test('does not mutate original state (immutability)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = advancePlay(state, 'base', 'LHS', 3);
    expect(state.base.LHS.lineIndex).toBe(0); // original unchanged
    expect(next.base.LHS.lineIndex).toBe(1);
  });

  test('only modifies the targeted case+side', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = advancePlay(state, 'base', 'LHS', 3);
    expect(next.base.RHS).toEqual(state.base.RHS); // RHS unchanged
  });
});

// ─── cancelPlay ──────────────────────────────────────────────────────────────

describe('cancelPlay', () => {
  test('sets active to false for the targeted side', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(next.base.LHS.active).toBe(false);
  });

  test('sets lineIndex to Infinity (show all lines)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(next.base.LHS.lineIndex).toBe(Infinity);
  });

  test('does not affect the other side', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(next.base.RHS.active).toBe(true);
  });

  test('does not affect the other case (induction)', () => {
    const state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(next.leap.LHS.active).toBe(true);
  });
});

// ─── isActive ────────────────────────────────────────────────────────────────

describe('isActive', () => {
  test('returns true when active', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(isActive(state, 'base', 'LHS')).toBe(true);
  });

  test('returns false when not active', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], false);
    expect(isActive(state, 'base', 'LHS')).toBe(false);
  });

  test('returns false after cancelPlay', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(isActive(next, 'base', 'LHS')).toBe(false);
  });

  test('returns false after advancePlay to last line', () => {
    const state = { base: { LHS: { active: true, lineIndex: 2 }, RHS: { active: true, lineIndex: 0 } } };
    const next = advancePlay(state, 'base', 'LHS', 3); // last = 3, new = 3 → deactivate
    expect(isActive(next, 'base', 'LHS')).toBe(false);
  });
});

// ─── visibleLineCount ─────────────────────────────────────────────────────────

describe('visibleLineCount', () => {
  test('returns null when not in play mode (show all)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], false);
    expect(visibleLineCount(state, 'base', 'LHS')).toBeNull();
  });

  test('returns 1 at lineIndex 0 (premise only)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(visibleLineCount(state, 'base', 'LHS')).toBe(1);
  });

  test('returns lineIndex + 1', () => {
    const state = { base: { LHS: { active: true, lineIndex: 2 }, RHS: { active: false, lineIndex: 0 } } };
    expect(visibleLineCount(state, 'base', 'LHS')).toBe(3);
  });

  test('returns null after cancelPlay (Infinity lineIndex)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(visibleLineCount(next, 'base', 'LHS')).toBeNull();
  });
});

// ─── showContinue ─────────────────────────────────────────────────────────────

describe('showContinue', () => {
  test('returns true when active and lineIndex < lastRealIndex', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true); // lineIndex = 0
    expect(showContinue(state, 'base', 'LHS', 3)).toBe(true); // 0 < 3
  });

  test('returns false when active but lineIndex === lastRealIndex (all revealed)', () => {
    const state = { base: { LHS: { active: true, lineIndex: 3 }, RHS: { active: false, lineIndex: 0 } } };
    expect(showContinue(state, 'base', 'LHS', 3)).toBe(false);
  });

  test('returns false when not active', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], false);
    expect(showContinue(state, 'base', 'LHS', 3)).toBe(false);
  });

  test('returns false after cancelPlay', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(showContinue(next, 'base', 'LHS', 3)).toBe(false);
  });

  test('returns false when proof has no lines beyond premise (lastRealIndex = 0)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(showContinue(state, 'base', 'LHS', 0)).toBe(false);
  });
});

// ─── full walkthrough scenario ────────────────────────────────────────────────

describe('full play-mode walkthrough (3 content lines)', () => {
  // fields: [premise, line1, line2, line3, empty_trailing]
  // lastRealIndex = 3
  const LAST = 3;

  test('advance through all lines one by one', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);

    // Initial state: only premise visible
    expect(visibleLineCount(state, 'base', 'LHS')).toBe(1);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);

    // Advance 1: show lines 0-1
    state = advancePlay(state, 'base', 'LHS', LAST);
    expect(visibleLineCount(state, 'base', 'LHS')).toBe(2);
    expect(isActive(state, 'base', 'LHS')).toBe(true);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);

    // Advance 2: show lines 0-2
    state = advancePlay(state, 'base', 'LHS', LAST);
    expect(visibleLineCount(state, 'base', 'LHS')).toBe(3);
    expect(isActive(state, 'base', 'LHS')).toBe(true);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);

    // Advance 3: show lines 0-3 → deactivate (all lines shown)
    state = advancePlay(state, 'base', 'LHS', LAST);
    expect(visibleLineCount(state, 'base', 'LHS')).toBeNull(); // active=false → show all
    expect(isActive(state, 'base', 'LHS')).toBe(false);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('cancel mid-way immediately shows all lines', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST); // lineIndex = 1

    state = cancelPlay(state, 'base', 'LHS');
    expect(visibleLineCount(state, 'base', 'LHS')).toBeNull();
    expect(isActive(state, 'base', 'LHS')).toBe(false);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);

    // RHS still in play mode
    expect(isActive(state, 'base', 'RHS')).toBe(true);
  });

  test('induction: each of the four case+side entries is independent', () => {
    let state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);

    // Advance base/LHS twice
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST);
    expect(state.base.LHS.lineIndex).toBe(2);

    // Cancel leap/RHS
    state = cancelPlay(state, 'leap', 'RHS');

    // All other entries unchanged
    expect(state.base.LHS.lineIndex).toBe(2);
    expect(state.base.LHS.active).toBe(true);
    expect(state.base.RHS.active).toBe(true);
    expect(state.base.RHS.lineIndex).toBe(0);
    expect(state.leap.LHS.active).toBe(true);
    expect(state.leap.LHS.lineIndex).toBe(0);
    expect(state.leap.RHS.active).toBe(false);
  });
});
