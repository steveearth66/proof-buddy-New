import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

/**
 * ProofLineComment
 *
 * A modal-based comment panel for each proof line, matching the Figma mockup.
 *
 * Features:
 *  - Speech-bubble icon (grey) or flag icon (red) toggling a modal
 *  - Orange asterisk (*) on button when an unsaved draft exists
 *  - Modal shows: read-only instructor comment, read-only student comment,
 *    new comment textarea (500 char), Ctrl+Enter shortcut, character counter
 *  - Copy-to-clipboard button on each displayed comment
 *  - "Last saved: HH:MM:SS" in footer (stored in localStorage)
 *  - Instructor-only correctness mark controls
 *  - Draft auto-saved to sessionStorage; cleared on submit
 *
 * Props:
 *   lineKey           - string  unique key e.g. "LHS-2"
 *   instructorComment - string
 *   studentComment    - string
 *   commentCorrect    - null | true | false
 *   isInstructor      - boolean
 *   onSave            - async (payload) => void
 *   disabled          - boolean
 */
const ProofLineComment = ({
  lineKey,
  instructorComment = '',
  studentComment = '',
  commentCorrect = null,
  isInstructor = false,
  onSave,
  disabled = false
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const storageKey = `plc_draft_${lineKey}`;
  const tsKey = `plc_ts_${lineKey}`;

  const getSavedDraft = () => {
    try {
      const s = sessionStorage.getItem(storageKey);
      return s ? JSON.parse(s) : null;
    } catch { return null; }
  };

  const initDraft = getSavedDraft() || {
    instructorText: instructorComment,
    studentText: studentComment,
    newComment: ''
  };

  const [instructorText, setInstructorText] = useState(initDraft.instructorText);
  const [studentText, setStudentText] = useState(initDraft.studentText);
  const [newComment, setNewComment] = useState(initDraft.newComment || '');
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [copySuccess, setCopySuccess] = useState('');
  const [lastSaved, setLastSaved] = useState(() => {
    try { return localStorage.getItem(tsKey); } catch { return null; }
  });

  const MAX_CHARS = 500;
  const hasDraft = newComment.trim().length > 0;

  const persistDraft = useCallback((iText, sText, nc) => {
    try {
      sessionStorage.setItem(storageKey, JSON.stringify({ instructorText: iText, studentText: sText, newComment: nc }));
    } catch { /* storage full */ }
  }, [storageKey]);

  const handleNewCommentChange = (e) => {
    const v = e.target.value.slice(0, MAX_CHARS);
    setNewComment(v);
    persistDraft(instructorText, studentText, v);
  };

  const handleInstructorTextChange = (e) => {
    const v = e.target.value;
    setInstructorText(v);
    persistDraft(v, studentText, newComment);
  };

  const handleSubmit = async () => {
    if (!onSave) return;
    if (!newComment.trim() && !(isInstructor && instructorText !== instructorComment)) return;
    setSaving(true);
    setSaveError('');
    setSaveSuccess(false);
    try {
      const payload = {};
      if (isInstructor && instructorText !== instructorComment) {
        payload.instructorComment = instructorText;
      }
      if (isInstructor && newComment.trim()) {
        payload.instructorComment = newComment.trim();
        setInstructorText(newComment.trim());
      }
      if (!isInstructor && newComment.trim()) {
        payload.studentComment = newComment.trim();
        setStudentText(newComment.trim());
      }
      if (Object.keys(payload).length === 0 && newComment.trim()) {
        payload.studentComment = newComment.trim();
      }
      await onSave(payload);
      try {
        sessionStorage.removeItem(storageKey);
        const now = new Date().toISOString();
        localStorage.setItem(tsKey, now);
        setLastSaved(now);
      } catch { /* ignore */ }
      setNewComment('');
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch {
      setSaveError('Failed to save. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleClose = () => { setIsOpen(false); setSaveError(''); };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleCopy = (text, key) => {
    try {
      navigator.clipboard.writeText(text);
      setCopySuccess(key);
      setTimeout(() => setCopySuccess(''), 1800);
    } catch { /* ignore */ }
  };

  const hasInstructorComment = !!(instructorComment && instructorComment.trim());
  const hasStudentComment = !!(studentComment && studentComment.trim());
  const hasAnyComment = hasInstructorComment || hasStudentComment;

  const correctnessDot = commentCorrect === true
    ? <span style={{ color: '#198754', fontSize: '0.6rem', marginLeft: '1px' }}>●</span>
    : commentCorrect === false
    ? <span style={{ color: '#dc3545', fontSize: '0.6rem', marginLeft: '1px' }}>●</span>
    : null;

  const toggleBtnStyle = {
    background: 'none', border: 'none', padding: '2px 4px', cursor: 'pointer',
    fontSize: '0.9rem', color: hasAnyComment ? '#dc3545' : '#adb5bd',
    lineHeight: 1, verticalAlign: 'middle',
    transition: 'color 0.15s, transform 0.1s',
    display: 'inline-flex', alignItems: 'center', gap: '1px'
  };

  const formatTs = (ts) => {
    if (!ts) return null;
    try { return new Date(ts).toLocaleTimeString(); } catch { return null; }
  };

  return (
    <span style={{ display: 'inline-block', verticalAlign: 'middle' }}>
      <button
        style={toggleBtnStyle}
        onClick={() => setIsOpen(true)}
        title={hasAnyComment ? 'View/edit comments' : 'Add a comment'}
        aria-label="Open comments"
        tabIndex={0}
        onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.15)'; }}
        onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
      >
        {hasAnyComment ? '\u{1F6A9}' : '\u{1F4AC}'}
        {correctnessDot}
        {hasDraft && (
          <span style={{ color: '#e65c00', fontSize: '0.65rem', fontWeight: 700, marginLeft: '1px' }} title="Unsaved draft">*</span>
        )}
      </button>

      <Modal show={isOpen} onHide={handleClose} centered size="lg" aria-labelledby={`comments-modal-${lineKey}`}>
        <Modal.Header style={{ borderBottom: '1px solid #dee2e6' }}>
          <Modal.Title id={`comments-modal-${lineKey}`} style={{ fontWeight: 600, fontSize: '1.1rem' }}>
            Comments
          </Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ padding: '20px 24px' }}>
          {/* Existing comments area */}
          <div style={{ background: '#f0f0f0', border: '1px solid #dee2e6', borderRadius: '6px', minHeight: '140px', maxHeight: '260px', overflowY: 'auto', padding: '14px 16px', marginBottom: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {!hasAnyComment ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100px', color: '#6c757d', fontWeight: 500 }}>
                There are no comments yet
              </div>
            ) : (
              <>
                {hasInstructorComment && (
                  <div>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#6610f2', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px' }}>
                      Instructor Comment
                    </div>
                    {isInstructor ? (
                      <textarea
                        style={{ width: '100%', borderRadius: '4px', border: '1px solid #b39ddb', padding: '6px 10px', fontSize: '0.875rem', resize: 'vertical', minHeight: '60px', background: '#ede7f6', fontFamily: 'inherit' }}
                        value={instructorText}
                        onChange={handleInstructorTextChange}
                        disabled={disabled || saving}
                        rows={2}
                        placeholder="Edit your instructor prompt..."
                      />
                    ) : (
                      <div style={{ background: '#ede7f6', border: '1px solid #b39ddb', borderRadius: '4px', padding: '8px 12px', color: '#4a148c', fontSize: '0.875rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '4px' }}>
                        <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{instructorComment}</span>
                        <button onClick={() => handleCopy(instructorComment, 'instructor')} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.75rem', color: copySuccess === 'instructor' ? '#198754' : '#6c757d', flexShrink: 0, padding: '0 2px' }} title="Copy">
                          {copySuccess === 'instructor' ? '\u2713' : '\u{1F4CB}'}
                        </button>
                      </div>
                    )}
                  </div>
                )}
                {hasStudentComment && (
                  <div>
                    <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#0d6efd', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      My Comment
                      {commentCorrect === true && <span style={{ background: '#198754', color: '#fff', borderRadius: '3px', padding: '0px 5px', fontSize: '0.65rem', fontWeight: 600 }}>\u2713 Correct</span>}
                      {commentCorrect === false && <span style={{ background: '#dc3545', color: '#fff', borderRadius: '3px', padding: '0px 5px', fontSize: '0.65rem', fontWeight: 600 }}>\u2717 Incorrect</span>}
                    </div>
                    <div style={{ background: '#ffffff', border: '1px solid #ced4da', borderRadius: '4px', padding: '8px 12px', color: '#212529', fontSize: '0.875rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '4px' }}>
                      <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{studentComment}</span>
                      <button onClick={() => handleCopy(studentComment, 'student')} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.75rem', color: copySuccess === 'student' ? '#198754' : '#6c757d', flexShrink: 0, padding: '0 2px' }} title="Copy">
                        {copySuccess === 'student' ? '\u2713' : '\u{1F4CB}'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Instructor correctness controls */}
          {isInstructor && hasStudentComment && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px', padding: '8px 12px', background: '#fff3cd', borderRadius: '6px', border: '1px solid #ffc107' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#664d03' }}>Mark student response:</span>
              <button className={`btn btn-sm ${commentCorrect === true ? 'btn-success' : 'btn-outline-success'}`} onClick={() => onSave && onSave({ commentCorrect: commentCorrect === true ? null : true })} disabled={disabled || saving}>\u2713 Correct</button>
              <button className={`btn btn-sm ${commentCorrect === false ? 'btn-danger' : 'btn-outline-danger'}`} onClick={() => onSave && onSave({ commentCorrect: commentCorrect === false ? null : false })} disabled={disabled || saving}>\u2717 Incorrect</button>
              {commentCorrect !== null && (
                <button className="btn btn-sm btn-outline-secondary" onClick={() => onSave && onSave({ commentCorrect: null })} disabled={disabled || saving}>Clear</button>
              )}
            </div>
          )}

          {/* New comment input */}
          <div>
            <textarea
              style={{ width: '100%', border: '1px solid #ced4da', borderRadius: '4px', padding: '10px 12px', fontSize: '0.875rem', resize: 'vertical', minHeight: '90px', fontFamily: 'inherit', outline: 'none' }}
              value={newComment}
              onChange={handleNewCommentChange}
              onKeyDown={handleKeyDown}
              disabled={disabled || saving}
              placeholder="Enter your comments here"
              maxLength={MAX_CHARS}
              onFocus={e => { e.target.style.borderColor = '#0d6efd'; }}
              onBlur={e => { e.target.style.borderColor = '#ced4da'; }}
            />
            <div style={{ textAlign: 'right', fontSize: '0.72rem', color: newComment.length >= MAX_CHARS ? '#dc3545' : '#6c757d', marginTop: '2px' }}>
              {newComment.length}/{MAX_CHARS} \u00b7 Ctrl+Enter to submit
            </div>
          </div>

          {saveSuccess && <div style={{ color: '#198754', fontSize: '0.82rem', marginTop: '6px', fontWeight: 500 }}>\u2713 Comment saved</div>}
          {saveError && <div style={{ color: '#dc3545', fontSize: '0.82rem', marginTop: '6px' }}>{saveError}</div>}
        </Modal.Body>

        <Modal.Footer style={{ borderTop: '1px solid #dee2e6', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <Button variant="danger" onClick={handleClose} style={{ background: '#e05c6a', border: 'none', borderRadius: '6px', padding: '7px 18px', fontWeight: 500 }}>
            Close Comments Window
          </Button>
          {formatTs(lastSaved) && (
            <span style={{ fontSize: '0.72rem', color: '#6c757d', alignSelf: 'center' }}>Last saved: {formatTs(lastSaved)}</span>
          )}
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={disabled || saving || (!newComment.trim() && !(isInstructor && instructorText !== instructorComment))}
            style={{ borderRadius: '6px', padding: '7px 18px', fontWeight: 500 }}
          >
            {saving ? 'Saving...' : 'Submit Comment'}
          </Button>
        </Modal.Footer>
      </Modal>
    </span>
  );
};

ProofLineComment.propTypes = {
  lineKey: PropTypes.string.isRequired,
  instructorComment: PropTypes.string,
  studentComment: PropTypes.string,
  commentCorrect: PropTypes.bool,
  isInstructor: PropTypes.bool,
  onSave: PropTypes.func,
  disabled: PropTypes.bool
};

export default ProofLineComment;
