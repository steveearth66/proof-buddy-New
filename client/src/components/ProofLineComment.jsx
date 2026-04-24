import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * ProofLineComment
 * 
 * An inline collapsible panel attached to a proof line that supports:
 *   - Instructor prompts (read-only for students, editable for instructors)
 *   - Student responses (editable for everyone)
 *   - AI/instructor correctness feedback badge
 *   - Auto-save draft to sessionStorage to survive page refreshes
 * 
 * Props:
 *   lineKey        - unique identifier string, e.g. "LHS-0" or "base-LHS-2"
 *   instructorComment - string (from backend)
 *   studentComment - string (from backend)
 *   commentCorrect - null | true | false
 *   isInstructor   - boolean
 *   onSave         - async ({ instructorComment?, studentComment?, commentCorrect? }) => void
 *   disabled       - boolean (disable inputs while a proof operation is in-flight)
 */
const ProofLineComment = ({
  lineKey,
  instructorComment = '',
  studentComment = '',
  commentCorrect = null,
  isInstructor = false,
  onSave,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  // Draft state – initialised from props, but auto-saved to sessionStorage
  const storageKey = `plc_draft_${lineKey}`;
  const getSavedDraft = () => {
    try {
      const saved = sessionStorage.getItem(storageKey);
      return saved ? JSON.parse(saved) : null;
    } catch { return null; }
  };

  const initDraft = getSavedDraft() || {
    instructorText: instructorComment,
    studentText: studentComment,
  };

  const [instructorText, setInstructorText] = useState(initDraft.instructorText);
  const [studentText, setStudentText] = useState(initDraft.studentText);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Persist drafts to sessionStorage on every change
  const persistDraft = useCallback((iText, sText) => {
    try {
      sessionStorage.setItem(storageKey, JSON.stringify({ instructorText: iText, studentText: sText }));
    } catch { /* storage full – ignore */ }
  }, [storageKey]);

  const handleInstructorChange = (e) => {
    const v = e.target.value;
    setInstructorText(v);
    persistDraft(v, studentText);
  };

  const handleStudentChange = (e) => {
    const v = e.target.value;
    setStudentText(v);
    persistDraft(instructorText, v);
  };

  const handleSave = async () => {
    if (!onSave) return;
    setSaving(true);
    setSaveError('');
    setSaveSuccess(false);
    try {
      const payload = {};
      if (isInstructor) payload.instructorComment = instructorText;
      payload.studentComment = studentText;
      await onSave(payload);
      // Clear session draft on successful save
      try { sessionStorage.removeItem(storageKey); } catch { /* ignore */ }
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (err) {
      setSaveError('Failed to save. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  // Count characters to show a badge on the toggle button
  const totalChars = instructorComment.length + studentComment.length;
  const hasContent = totalChars > 0;

  // Correctness badge
  const correctnessBadge = commentCorrect === true
    ? <span className="badge bg-success ms-1" title="Marked correct">✓</span>
    : commentCorrect === false
      ? <span className="badge bg-danger ms-1" title="Marked incorrect">✗</span>
      : null;

  const toggleButtonStyle = {
    background: 'none',
    border: hasContent ? '1px solid #0d6efd' : '1px solid #6c757d',
    borderRadius: '4px',
    padding: '1px 6px',
    cursor: 'pointer',
    fontSize: '0.75rem',
    color: hasContent ? '#0d6efd' : '#6c757d',
    marginLeft: '8px',
    verticalAlign: 'middle',
    transition: 'all 0.15s',
  };

  const panelStyle = {
    display: isOpen ? 'block' : 'none',
    background: '#f8f9fa',
    border: '1px solid #dee2e6',
    borderRadius: '0 0 6px 6px',
    padding: '10px 14px',
    marginTop: '2px',
    marginBottom: '6px',
    fontSize: '0.875rem',
  };

  const labelStyle = {
    display: 'block',
    fontWeight: 600,
    marginBottom: '3px',
    fontSize: '0.78rem',
    color: '#495057',
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  };

  const textareaStyle = {
    width: '100%',
    borderRadius: '4px',
    border: '1px solid #ced4da',
    padding: '5px 8px',
    fontSize: '0.85rem',
    resize: 'vertical',
    minHeight: '56px',
    fontFamily: 'inherit',
  };

  return (
    <div style={{ display: 'inline-block' }}>
      {/* Toggle button */}
      <button
        style={toggleButtonStyle}
        onClick={() => setIsOpen(!isOpen)}
        title={hasContent ? 'View/edit comment' : 'Add comment'}
        aria-expanded={isOpen}
      >
        💬{hasContent ? ` ${totalChars}c` : '+'}
      </button>
      {correctnessBadge}

      {/* Panel */}
      <div style={panelStyle}>
        {/* Instructor comment section */}
        <div style={{ marginBottom: '10px' }}>
          <label style={{ ...labelStyle, color: '#6610f2' }}>
            📋 Instructor prompt
          </label>
          {isInstructor ? (
            <textarea
              style={textareaStyle}
              value={instructorText}
              onChange={handleInstructorChange}
              disabled={disabled || saving}
              placeholder="Type a question or prompt for the student about this proof step..."
              rows={2}
            />
          ) : (
            <div style={{
              background: '#ede7f6',
              border: '1px solid #b39ddb',
              borderRadius: '4px',
              padding: '6px 10px',
              minHeight: '36px',
              color: instructorComment ? '#4a148c' : '#9e9e9e',
              fontStyle: instructorComment ? 'normal' : 'italic',
              whiteSpace: 'pre-wrap',
            }}>
              {instructorComment || 'No instructor comment for this step.'}
            </div>
          )}
        </div>

        {/* Student comment section */}
        <div style={{ marginBottom: '8px' }}>
          <label style={{ ...labelStyle, color: '#0d6efd' }}>
            ✏️ {isInstructor ? 'Student response' : 'Your note / response'}
          </label>
          <textarea
            style={textareaStyle}
            value={studentText}
            onChange={handleStudentChange}
            disabled={disabled || saving || (isInstructor && false)}
            placeholder={
              isInstructor
                ? "Student's response will appear here once they write one."
                : instructorComment
                  ? "Answer the instructor's question above..."
                  : "Add your own annotation about this proof step..."
            }
            rows={2}
            readOnly={isInstructor}
          />
          {isInstructor && (
            <div style={{ fontSize: '0.75rem', color: '#6c757d', marginTop: '2px' }}>
              Instructors can read but not overwrite student responses.
            </div>
          )}
        </div>

        {/* Correctness mark (instructor only) */}
        {isInstructor && (
          <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ ...labelStyle, margin: 0 }}>Mark response:</span>
            <button
              className={`btn btn-sm ${commentCorrect === true ? 'btn-success' : 'btn-outline-success'}`}
              onClick={() => onSave && onSave({ commentCorrect: commentCorrect === true ? null : true })}
              disabled={disabled || saving}
              title="Mark student response as correct"
            >
              ✓ Correct
            </button>
            <button
              className={`btn btn-sm ${commentCorrect === false ? 'btn-danger' : 'btn-outline-danger'}`}
              onClick={() => onSave && onSave({ commentCorrect: commentCorrect === false ? null : false })}
              disabled={disabled || saving}
              title="Mark student response as incorrect"
            >
              ✗ Incorrect
            </button>
            {commentCorrect !== null && (
              <button
                className="btn btn-sm btn-outline-secondary"
                onClick={() => onSave && onSave({ commentCorrect: null })}
                disabled={disabled || saving}
                title="Clear mark"
              >
                Clear
              </button>
            )}
          </div>
        )}

        {/* Save button and feedback */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {!isInstructor && (
            <button
              className="btn btn-sm btn-primary"
              onClick={handleSave}
              disabled={disabled || saving}
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          )}
          {isInstructor && (
            <button
              className="btn btn-sm btn-outline-primary"
              onClick={handleSave}
              disabled={disabled || saving}
            >
              {saving ? 'Saving prompt...' : 'Save prompt'}
            </button>
          )}
          {saveSuccess && (
            <span style={{ color: '#198754', fontSize: '0.8rem' }}>✓ Saved</span>
          )}
          {saveError && (
            <span style={{ color: '#dc3545', fontSize: '0.8rem' }}>{saveError}</span>
          )}
        </div>
      </div>
    </div>
  );
};

ProofLineComment.propTypes = {
  lineKey: PropTypes.string.isRequired,
  instructorComment: PropTypes.string,
  studentComment: PropTypes.string,
  commentCorrect: PropTypes.bool,
  isInstructor: PropTypes.bool,
  onSave: PropTypes.func,
  disabled: PropTypes.bool,
};

export default ProofLineComment;
