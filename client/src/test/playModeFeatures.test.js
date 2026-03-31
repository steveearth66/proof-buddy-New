/**
 * playModeFeatures.test.js
 *
 * Tests for all Play Mode UI features.
 *
 * Run with:
 *   npm test -- --testPathPattern=playModeFeatures
 *
 * Sections:
 *   A) ProofCard — "Run Proof" button appears on every card (Proofs.jsx)
 *   B) Single-line proof edge case — no greying, no buttons when premise-only
 *   C) Footer warning condition mirrors Continue button condition exactly
 *   D) Continue + Cancel buttons appear together or not at all
 *   E) Row number click blocking condition
 *   F) Full lifecycle: enter play mode → advance line-by-line → completion
 *   G) Full lifecycle: enter play mode → cancel mid-way
 *   H) Induction base/leap independence (four case+side combos independent)
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

import Proofs from '../pages/Proofs';

import {
  initPlayState,
  getLastRealIndex,
  showContinue,
  advancePlay,
  cancelPlay,
  visibleLineCount,
  isActive,
} from '../utils/playModeUtils';

// ── Mocks ────────────────────────────────────────────────────────────────────

// Proofs.jsx imports react-bootstrap/esm/Button (ESM build) which Jest cannot parse;
// redirect it to the CommonJS-compatible path.
jest.mock('react-bootstrap/esm/Button', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: function MockButton({ children, onClick, variant, style, disabled, size, className, 'aria-label': ariaLabel, animation }) {
      return React.createElement('button', { onClick, 'data-variant': variant, style, disabled, className, 'aria-label': ariaLabel }, children);
    },
  };
});

jest.mock('../layouts/MainLayout', () => {
  const React = require('react');
  return {
    __esModule: true,
    default: function MockMainLayout({ children }) {
      return React.createElement('div', { 'data-testid': 'main-layout' }, children);
    },
  };
});

jest.mock('../components/Pagination', () => ({
  __esModule: true,
  default: function MockPagination() { return null; },
}));

jest.mock('react-toastify', () => ({
  toast: { success: jest.fn(), error: jest.fn(), warning: jest.fn() },
}));

// Proofs.jsx imports erService (legacy) but routes dynamically through equationalService / inductionService
jest.mock('../services/erService', () => ({}));

jest.mock('../services/equationalService', () => ({
  getRacketProofs: jest.fn(),
  deleteRacketProof: jest.fn(),
}));

jest.mock('../services/inductionService', () => ({
  getInductionProofs: jest.fn(),
  deleteInductionProof: jest.fn(),
  clearInduction: jest.fn(),
}));

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Build a fields array: premise + N content lines + 1 empty trailing slot. */
function makeFields(contentLineCount) {
  const fields = [{ racket: '(f 0)', rule: 'Premise', deleted: false }];
  for (let i = 1; i <= contentLineCount; i++) {
    fields.push({ racket: `(expr ${i})`, rule: `rule${i}`, deleted: false });
  }
  fields.push({ racket: '', rule: '', deleted: false }); // always-present empty trailing
  return fields;
}

const SAMPLE_PROOF = {
  id: 42,
  name: 'appNull',
  tag: 'lemma1',
  lhs: '(append A null)',
  rhs: 'A',
  isComplete: false,
};

// ── A: ProofCard — Run Proof button ──────────────────────────────────────────

describe('A — ProofCard: Run Proof button', () => {
  const equationalService = require('../services/equationalService');

  beforeEach(() => {
    equationalService.getRacketProofs.mockResolvedValue({
      proofs: [SAMPLE_PROOF],
      currentPage: 1,
      totalPages: 1,
    });
  });

  afterEach(() => jest.clearAllMocks());

  function renderProofs() {
    return render(
      <MemoryRouter initialEntries={['/proofs']}>
        <Proofs />
      </MemoryRouter>
    );
  }

  test('each proof card renders both "Open Proof" and "Run Proof" buttons', async () => {
    renderProofs();
    await waitFor(() => expect(screen.getByText('Open Proof')).toBeInTheDocument());
    expect(screen.getByText('Run Proof')).toBeInTheDocument();
  });

  test('"Run Proof" and "Open Proof" are separate anchor links', async () => {
    renderProofs();
    await waitFor(() => expect(screen.getByText('Run Proof')).toBeInTheDocument());
    const openAnchor = screen.getByText('Open Proof').closest('a');
    const runAnchor = screen.getByText('Run Proof').closest('a');
    expect(openAnchor).toBeTruthy();
    expect(runAnchor).toBeTruthy();
    expect(openAnchor).not.toBe(runAnchor);
  });

  test('both links point to the same route (/equational-reasoning-new)', async () => {
    renderProofs();
    await waitFor(() => expect(screen.getByText('Run Proof')).toBeInTheDocument());
    const openHref = screen.getByText('Open Proof').closest('a').getAttribute('href');
    const runHref  = screen.getByText('Run Proof').closest('a').getAttribute('href');
    expect(openHref).toBe('/equational-reasoning-new');
    expect(runHref).toBe('/equational-reasoning-new');
  });

  test('proof card displays proof name and tag', async () => {
    renderProofs();
    await waitFor(() => expect(screen.getByText(/appNull/)).toBeInTheDocument());
    expect(screen.getByText(/lemma1/)).toBeInTheDocument();
  });

  test('multiple proof cards each get their own Run Proof button', async () => {
    equationalService.getRacketProofs.mockResolvedValue({
      proofs: [
        SAMPLE_PROOF,
        { ...SAMPLE_PROOF, id: 43, name: 'appCons', tag: 'lemma2' },
      ],
      currentPage: 1,
      totalPages: 1,
    });
    renderProofs();
    await waitFor(() => {
      const runButtons = screen.getAllByText('Run Proof');
      expect(runButtons).toHaveLength(2);
    });
  });
});

// ── B: Single-line proof edge case ───────────────────────────────────────────

describe('B — Single-line proof (premise only): no buttons, no greying', () => {
  const fields = makeFields(0); // [premise, empty trailing]

  test('getLastRealIndex is 0 for premise-only proof', () => {
    expect(getLastRealIndex(fields)).toBe(0);
  });

  test('showContinue is false when play mode is active but proof has no lines beyond premise', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(showContinue(state, 'base', 'LHS', 0)).toBe(false);
  });

  test('footer warning condition (showContinue) is false → footer not greyed', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const lastReal = getLastRealIndex(fields);
    expect(showContinue(state, 'base', 'LHS', lastReal)).toBe(false);
  });

  test('row number click is not blocked for premise-only proof in play mode', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const lastReal = getLastRealIndex(fields);
    const blocked = showContinue(state, 'base', 'LHS', lastReal);
    expect(blocked).toBe(false);
  });

  test('visibleLineCount is 1 (premise shown) but showContinue is still false', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(visibleLineCount(state, 'base', 'LHS')).toBe(1);
    expect(showContinue(state, 'base', 'LHS', 0)).toBe(false);
  });
});

// ── C: Footer warning condition mirrors Continue button condition ─────────────

describe('C — Footer warning condition mirrors Continue button condition exactly', () => {
  const fields = makeFields(3);
  const LAST = getLastRealIndex(fields); // 3

  test('both true when active and lines remain', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    // showContinue drives both the button row and the footer warning
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);
  });

  test('both false when not in play mode (normal open)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], false);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('both false after natural play-mode completion', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST); // reaches LAST → deactivates
    expect(isActive(state, 'base', 'LHS')).toBe(false);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('both false after cancel', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST); // partway through
    state = cancelPlay(state, 'base', 'LHS');
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('RHS condition is independent from LHS condition', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = cancelPlay(state, 'base', 'LHS'); // cancel LHS
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false); // LHS: no warning/buttons
    expect(showContinue(state, 'base', 'RHS', LAST)).toBe(true);  // RHS: still warning/buttons
  });
});

// ── D: Continue + Cancel appear together or not at all ───────────────────────

describe('D — Continue and Cancel share the same visibility condition', () => {
  const LAST = 3;

  test('condition true → both buttons shown (active, lines hidden)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);
  });

  test('condition false → neither button shown (normal open)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], false);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('condition false → neither button shown (premise-only in play mode)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(showContinue(state, 'base', 'LHS', 0)).toBe(false);
  });

  test('condition becomes false on the final Continue click', () => {
    const state = {
      base: {
        LHS: { active: true, lineIndex: LAST - 1 },
        RHS: { active: true, lineIndex: 0 },
      },
    };
    const next = advancePlay(state, 'base', 'LHS', LAST);
    expect(showContinue(next, 'base', 'LHS', LAST)).toBe(false);
  });

  test('condition becomes false immediately on cancel', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(showContinue(next, 'base', 'LHS', LAST)).toBe(false);
  });
});

// ── E: Row number click blocking ─────────────────────────────────────────────

describe('E — Row number click blocking (guard: showContinue)', () => {
  const LAST = 3;

  test('click IS blocked when lines still hidden', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);
  });

  test('click IS blocked mid-play after some lines revealed', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST); // one line revealed, 2 still hidden
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);
  });

  test('click is NOT blocked after all lines revealed naturally', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    for (let i = 0; i < LAST; i++) {
      state = advancePlay(state, 'base', 'LHS', LAST);
    }
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('click is NOT blocked after cancel', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(showContinue(next, 'base', 'LHS', LAST)).toBe(false);
  });

  test('click is NOT blocked in normal open (not play mode)', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], false);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('click is NOT blocked for premise-only proof even in play mode', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(showContinue(state, 'base', 'LHS', 0)).toBe(false);
  });
});

// ── F: Full lifecycle — advance to completion ─────────────────────────────────

describe('F — Lifecycle: advance line-by-line to natural completion', () => {
  const fields = makeFields(3);
  const LAST = getLastRealIndex(fields); // 3

  test('only premise visible on play mode entry', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    expect(visibleLineCount(state, 'base', 'LHS')).toBe(1);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);
  });

  test('each Continue reveals exactly one more line', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    for (let shown = 1; shown <= LAST; shown++) {
      expect(visibleLineCount(state, 'base', 'LHS')).toBe(shown);
      state = advancePlay(state, 'base', 'LHS', LAST);
    }
    // After last advance: inactive → show all (null)
    expect(visibleLineCount(state, 'base', 'LHS')).toBeNull();
  });

  test('after last Continue: play deactivates, footer re-enabled, no buttons', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST);
    expect(isActive(state, 'base', 'LHS')).toBe(false);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);   // no buttons
    expect(visibleLineCount(state, 'base', 'LHS')).toBeNull();       // all lines shown
  });

  test('completing LHS does not affect RHS play mode', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST);
    // LHS done
    expect(isActive(state, 'base', 'LHS')).toBe(false);
    // RHS still in play mode, still only shows premise
    expect(isActive(state, 'base', 'RHS')).toBe(true);
    expect(visibleLineCount(state, 'base', 'RHS')).toBe(1);
  });
});

// ── G: Full lifecycle — cancel ────────────────────────────────────────────────

describe('G — Lifecycle: cancel mid-play', () => {
  const LAST = 3;

  test('cancel after first Continue: all lines instantly visible', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST); // one line shown
    state = cancelPlay(state, 'base', 'LHS');
    expect(visibleLineCount(state, 'base', 'LHS')).toBeNull(); // show all
    expect(isActive(state, 'base', 'LHS')).toBe(false);
  });

  test('cancel immediately re-enables footer (showContinue becomes false)', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = cancelPlay(state, 'base', 'LHS');
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('cancel immediately lifts row-click blocking', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = cancelPlay(state, 'base', 'LHS');
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(false);
  });

  test('cancel on LHS leaves RHS fully in play mode', () => {
    let state = initPlayState(['base'], ['LHS', 'RHS'], true);
    state = cancelPlay(state, 'base', 'LHS');
    expect(isActive(state, 'base', 'RHS')).toBe(true);
    expect(showContinue(state, 'base', 'RHS', LAST)).toBe(true);
    expect(visibleLineCount(state, 'base', 'RHS')).toBe(1);
  });

  test('cancel from the very start (lineIndex=0) still works', () => {
    const state = initPlayState(['base'], ['LHS', 'RHS'], true);
    const next = cancelPlay(state, 'base', 'LHS');
    expect(visibleLineCount(next, 'base', 'LHS')).toBeNull();
    expect(showContinue(next, 'base', 'LHS', LAST)).toBe(false);
  });
});

// ── H: Induction base/leap independence ──────────────────────────────────────

describe('H — Induction: all four case+side combinations are independent', () => {
  const LAST = 3;

  test('all four combos start in play mode', () => {
    const state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);
    expect(showContinue(state, 'base', 'RHS', LAST)).toBe(true);
    expect(showContinue(state, 'leap', 'LHS', LAST)).toBe(true);
    expect(showContinue(state, 'leap', 'RHS', LAST)).toBe(true);
  });

  test('advancing base/LHS does not change the other three combos', () => {
    let state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST);
    expect(state.base.LHS.lineIndex).toBe(2);
    // All others still at lineIndex 0
    expect(state.base.RHS.lineIndex).toBe(0);
    expect(state.leap.LHS.lineIndex).toBe(0);
    expect(state.leap.RHS.lineIndex).toBe(0);
  });

  test('canceling leap/LHS does not affect base/RHS', () => {
    let state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    state = cancelPlay(state, 'leap', 'LHS');
    expect(showContinue(state, 'base', 'RHS', LAST)).toBe(true);
    expect(isActive(state, 'base', 'RHS')).toBe(true);
  });

  test('completing base/RHS naturally does not end leap/LHS', () => {
    let state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    for (let i = 0; i < LAST; i++) state = advancePlay(state, 'base', 'RHS', LAST);
    expect(isActive(state, 'base', 'RHS')).toBe(false);   // completed
    expect(isActive(state, 'leap', 'LHS')).toBe(true);    // still active
  });

  test('each combo can be canceled independently, leaving others active', () => {
    let state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    state = cancelPlay(state, 'base', 'LHS');
    state = cancelPlay(state, 'leap', 'RHS');
    expect(isActive(state, 'base', 'LHS')).toBe(false);
    expect(isActive(state, 'leap', 'RHS')).toBe(false);
    expect(isActive(state, 'base', 'RHS')).toBe(true);
    expect(isActive(state, 'leap', 'LHS')).toBe(true);
  });

  test('switching from base to leap mid-play preserves base progress (side-switching)', () => {
    let state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    // Advance base/LHS twice (simulating user advancing before switching to Leap tab)
    state = advancePlay(state, 'base', 'LHS', LAST);
    state = advancePlay(state, 'base', 'LHS', LAST);
    const savedIndex = state.base.LHS.lineIndex; // 2

    // "switch" to leap — read leap/LHS state
    expect(state.leap.LHS.lineIndex).toBe(0);
    expect(showContinue(state, 'leap', 'LHS', LAST)).toBe(true);

    // "switch back" — base/LHS still exactly where it was
    expect(state.base.LHS.lineIndex).toBe(savedIndex);
    expect(showContinue(state, 'base', 'LHS', LAST)).toBe(true);
  });

  test('completing all four combos results in fully inactive state', () => {
    let state = initPlayState(['base', 'leap'], ['LHS', 'RHS'], true);
    const combos = [
      ['base', 'LHS'], ['base', 'RHS'],
      ['leap', 'LHS'], ['leap', 'RHS'],
    ];
    for (const [caseKey, side] of combos) {
      for (let i = 0; i < LAST; i++) {
        state = advancePlay(state, caseKey, side, LAST);
      }
    }
    for (const [caseKey, side] of combos) {
      expect(isActive(state, caseKey, side)).toBe(false);
      expect(showContinue(state, caseKey, side, LAST)).toBe(false);
    }
  });
});
