import React, { useState, useCallback } from 'react';
import PropTypes from 'prop-types';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';

/**
 * ProofLineComment
 *
 * A modal-based comment panel attached to a proof line, matching the Figma mockup.
 * Features:
 * - Toggled by a speech-bubble icon button next to the proof line
 * - Shows "Comments" modal header
 * - Displays instructor comments and student comments in a read-only area
 * - New comment textarea for student/instructor input
 * - Auto-saves draft to sessionStorage
 * - Instructor can mark student responses correct/incorrect
 * - Character count indicator on textarea
 * - Keyboard shortcut: Ctrl+Enter to submit
 *
 * Props:
 *   lineKey          - unique identifier string, e.g. "LHS-0"
 *   instructorComment - string (from backend)
 *   studentComment    - string (from backend)
 *   commentCorrect    - null | true | false
 *   isInstructor      - boolean
 *   onSave           - async (payload) => void
 *   disabled         - boolean
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

    // Draft state with sessionStorage persistence
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
          newComment: ''
    };

    const [instructorText, setInstructorText] = useState(initDraft.instructorText);
    const [studentText, setStudentText] = useState(initDraft.studentText);
    const [newComment, setNewComment] = useState(initDraft.newComment || '');
    const [saving, setSaving] = useState(false);
    const [saveError, setSaveError] = useState('');
    const [saveSuccess, setSaveSuccess] = useState(false);
    const MAX_CHARS = 500;

    const persistDraft = useCallback((iText, sText, nc) => {
          try {
                  sessionStorage.setItem(storageKey, JSON.stringify({
                            instructorText: iText,
                            studentText: sText,
                            newComment: nc
                  }));
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
          if (!newComment.trim() && !isInstructor) return;
          setSaving(true);
          setSaveError('');
          setSaveSuccess(false);
          try {
                  const payload = {};
                  if (isInstructor && instructorText !== instructorComment) {
                            payload.instructorComment = instructorText;
                  }
                  if (!isInstructor && newComment.trim()) {
                            payload.studentComment = newComment.trim();
                            setStudentText(newComment.trim());
                  }
                  if (isInstructor && newComment.trim()) {
                            payload.instructorComment = newComment.trim();
                            setInstructorText(newComment.trim());
                  }
                  if (Object.keys(payload).length === 0 && newComment.trim()) {
                            payload.studentComment = newComment.trim();
                  }
                  await onSave(payload);
                  try { sessionStorage.removeItem(storageKey); } catch { /* ignore */ }
                  setNewComment('');
                  setSaveSuccess(true);
                  setTimeout(() => setSaveSuccess(false), 2500);
          } catch {
                  setSaveError('Failed to save. Please try again.');
          } finally {
                  setSaving(false);
          }
    };

    const handleClose = () => {
          setIsOpen(false);
          setSaveError('');
    };

    // Keyboard shortcut: Ctrl+Enter submits
    const handleKeyDown = (e) => {
          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  handleSubmit();
          }
    };

    // Determine if there are existing comments to display
    const hasInstructorComment = !!(instructorComment && instructorComment.trim());
    const hasStudentComment = !!(studentComment && studentComment.trim());
    const hasAnyComment = hasInstructorComment || hasStudentComment;

    // Correctness badge for the toggle button
    const correctnessDot = commentCorrect === true
      ? <span style={{ color: '#198754', fontSize: '0.6rem', marginLeft: '1px' }}>●</span>span>
          : commentCorrect === false
      ? <span style={{ color: '#dc3545', fontSize: '0.6rem', marginLeft: '1px' }}>●</span>span>
          : null;

    // Toggle button: speech bubble icon, colored if has content
    const toggleBtnStyle = {
          background: 'none',
          border: 'none',
          padding: '2px 4px',
          cursor: 'pointer',
          fontSize: '0.9rem',
          color: hasAnyComment ? '#dc3545' : '#adb5bd',
          lineHeight: 1,
          verticalAlign: 'middle',
          transition: 'color 0.15s, transform 0.1s',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '1px'
    };

    return (
          <span style={{ display: 'inline-block', verticalAlign: 'middle' }}>
            {/* Toggle trigger button */}
                  <button
                            style={toggleBtnStyle}
                            onClick={() => setIsOpen(true)}
                            title={hasAnyComment ? 'View/edit comments' : 'Add a comment'}
                            aria-label="Open comments"
                            tabIndex={0}
                            onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.15)'; }}
                            onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
                          >
                    {/* Flag icon if comments exist, speech bubble otherwise */}
                    {hasAnyComment ? '🚩' : '💬'}
                    {correctnessDot}
                  </button>button>
          
            {/* Comments Modal */}
                <Modal
                          show={isOpen}
                          onHide={handleClose}
                          centered
                          size="lg"
                          aria-labelledby={`comments-modal-title-${lineKey}`}
                        >
                        <Modal.Header style={{ borderBottom: '1px solid #dee2e6', paddingBottom: '12px' }}>
                                  <Modal.Title
                                                id={`comments-modal-title-${lineKey}`}
                                                style={{ fontWeight: 600, fontSize: '1.1rem' }}
                                              >
                                              Comments
                                  </Modal.Title>Modal.Title>
                        </Modal.Header>Modal.Header>
                
                        <Modal.Body style={{ padding: '20px 24px' }}>
                          {/* Existing Comments Display Area */}
                                  <div style={{
                                      background: '#f0f0f0',
                                      border: '1px solid #dee2e6',
                                      borderRadius: '6px',
                                      minHeight: '140px',
                                      maxHeight: '260px',
                                      overflowY: 'auto',
                                      padding: '14px 16px',
                                      marginBottom: '16px',
                                      display: 'flex',
                                      flexDirection: 'column',
                                      gap: '10px'
                        }}>
                                    {!hasAnyComment ? (
                                        <div style={{
                                                          display: 'flex',
                                                          alignItems: 'center',
                                                          justifyContent: 'center',
                                                          height: '100px',
                                                          color: '#6c757d',
                                                          fontWeight: 500,
                                                          fontSize: '0.95rem'
                                        }}>
                                                        There are no comments yet
                                        </div>div>
                                      ) : (
                                        <>
                                          {hasInstructorComment && (
                                                            <div>
                                                                                <div style={{
                                                                                    fontSize: '0.72rem',
                                                                                    fontWeight: 700,
                                                                                    color: '#6610f2',
                                                                                    textTransform: 'uppercase',
                                                                                    letterSpacing: '0.05em',
                                                                                    marginBottom: '4px'
                                                              }}>
                                                                                                      Instructor Comment
                                                                                  </div>div>
                                                              {isInstructor ? (
                                                                                    <textarea
                                                                                                              style={{
                                                                                                                                          width: '100%',
                                                                                                                                          borderRadius: '4px',
                                                                                                                                          border: '1px solid #b39ddb',
                                                                                                                                          padding: '6px 10px',
                                                                                                                                          fontSize: '0.875rem',
                                                                                                                                          resize: 'vertical',
                                                                                                                                          minHeight: '60px',
                                                                                                                                          background: '#ede7f6',
                                                                                                                                          fontFamily: 'inherit'
                                                                                                                }}
                                                                                                              value={instructorText}
                                                                                                              onChange={handleInstructorTextChange}
                                                                                                              disabled={disabled || saving}
                                                                                                              rows={2}
                                                                                                              placeholder="Edit your instructor prompt..."
                                                                                                            />
                                                                                  ) : (
                                                                                    <div style={{
                                                                                                              background: '#ede7f6',
                                                                                                              border: '1px solid #b39ddb',
                                                                                                              borderRadius: '4px',
                                                                                                              padding: '8px 12px',
                                                                                                              color: '#4a148c',
                                                                                                              fontSize: '0.875rem',
                                                                                                              whiteSpace: 'pre-wrap',
                                                                                                              wordBreak: 'break-word'
                                                                                      }}>
                                                                                      {instructorComment}
                                                                                      </div>div>
                                                                                )}
                                                            </div>div>
                                                        )}
                                        
                                          {hasStudentComment && (
                                                            <div>
                                                                                <div style={{
                                                                                    fontSize: '0.72rem',
                                                                                    fontWeight: 700,
                                                                                    color: '#0d6efd',
                                                                                    textTransform: 'uppercase',
                                                                                    letterSpacing: '0.05em',
                                                                                    marginBottom: '4px',
                                                                                    display: 'flex',
                                                                                    alignItems: 'center',
                                                                                    gap: '6px'
                                                              }}>
                                                                                                      My Comment
                                                                                  {commentCorrect === true && (
                                                                                      <span style={{
                                                                                                                  background: '#198754',
                                                                                                                  color: '#fff',
                                                                                                                  borderRadius: '3px',
                                                                                                                  padding: '0px 5px',
                                                                                                                  fontSize: '0.65rem',
                                                                                                                  fontWeight: 600
                                                                                        }}>✓ Correct</span>span>
                                                                                                      )}
                                                                                  {commentCorrect === false && (
                                                                                      <span style={{
                                                                                                                  background: '#dc3545',
                                                                                                                  color: '#fff',
                                                                                                                  borderRadius: '3px',
                                                                                                                  padding: '0px 5px',
                                                                                                                  fontSize: '0.65rem',
                                                                                                                  fontWeight: 600
                                                                                        }}>✗ Incorrect</span>span>
                                                                                                      )}
                                                                                  </div>div>
                                                                                <div style={{
                                                                                    background: '#ffffff',
                                                                                    border: '1px solid #ced4da',
                                                                                    borderRadius: '4px',
                                                                                    padding: '8px 12px',
                                                                                    color: '#212529',
                                                                                    fontSize: '0.875rem',
                                                                                    whiteSpace: 'pre-wrap',
                                                                                    wordBreak: 'break-word'
                                                              }}>
                                                                                  {studentComment}
                                                                                  </div>div>
                                                            </div>div>
                                                        )}
                                        </>>
                                      )}
                                  </div>div>
                        
                          {/* Instructor correctness controls */}
                          {isInstructor && hasStudentComment && (
                                      <div style={{
                                                      display: 'flex',
                                                      alignItems: 'center',
                                                      gap: '8px',
                                                      marginBottom: '14px',
                                                      padding: '8px 12px',
                                                      background: '#fff3cd',
                                                      borderRadius: '6px',
                                                      border: '1px solid #ffc107'
                                      }}>
                                                    <span style={{ fontSize: '0.8rem', fontWeight: 600, color: '#664d03' }}>
                                                                    Mark student response:
                                                    </span>span>
                                                    <button
                                                                      className={`btn btn-sm ${commentCorrect === true ? 'btn-success' : 'btn-outline-success'}`}
                                                                      onClick={() => onSave && onSave({ commentCorrect: commentCorrect === true ? null : true })}
                                                                      disabled={disabled || saving}
                                                                      title="Mark as correct"
                                                                    >
                                                                    ✓ Correct
                                                    </button>button>
                                                    <button
                                                                      className={`btn btn-sm ${commentCorrect === false ? 'btn-danger' : 'btn-outline-danger'}`}
                                                                      onClick={() => onSave && onSave({ commentCorrect: commentCorrect === false ? null : false })}
                                                                      disabled={disabled || saving}
                                                                      title="Mark as incorrect"
                                                                    >
                                                                    ✗ Incorrect
                                                    </button>button>
                                        {commentCorrect !== null && (
                                                        <button
                                                                            className="btn btn-sm btn-outline-secondary"
                                                                            onClick={() => onSave && onSave({ commentCorrect: null })}
                                                                            disabled={disabled || saving}
                                                                            title="Clear mark"
                                                                          >
                                                                          Clear
                                                        </button>button>
                                                    )}
                                      </div>div>
                                  )}
                        
                          {/* New Comment Input Area */}
                                  <div style={{ position: 'relative' }}>
                                              <textarea
                                                              style={{
                                                                                width: '100%',
                                                                                border: '1px solid #ced4da',
                                                                                borderRadius: '4px',
                                                                                padding: '10px 12px',
                                                                                fontSize: '0.875rem',
                                                                                resize: 'vertical',
                                                                                minHeight: '90px',
                                                                                fontFamily: 'inherit',
                                                                                outline: 'none',
                                                                                transition: 'border-color 0.15s'
                                                              }}
                                                              value={newComment}
                                                              onChange={handleNewCommentChange}
                                                              onKeyDown={handleKeyDown}
                                                              disabled={disabled || saving}
                                                              placeholder="Enter your comments here"
                                                              maxLength={MAX_CHARS}
                                                              onFocus={e => { e.target.style.borderColor = '#0d6efd'; }}
                                                              onBlur={e => { e.target.style.borderColor = '#ced4da'; }}
                                                            />
                                              <div style={{
                                        textAlign: 'right',
                                        fontSize: '0.72rem',
                                        color: newComment.length >= MAX_CHARS ? '#dc3545' : '#6c757d',
                                        marginTop: '2px'
                        }}>
                                                {newComment.length}/{MAX_CHARS} · Ctrl+Enter to submit
                                              </div>div>
                                  </div>div>
                        
                          {/* Feedback messages */}
                          {saveSuccess && (
                                      <div style={{
                                                      color: '#198754',
                                                      fontSize: '0.82rem',
                                                      marginTop: '6px',
                                                      fontWeight: 500
                                      }}>
                                                    ✓ Comment saved successfully
                                      </div>div>
                                  )}
                          {saveError && (
                                      <div style={{
                                                      color: '#dc3545',
                                                      fontSize: '0.82rem',
                                                      marginTop: '6px'
                                      }}>
                                        {saveError}
                                      </div>div>
                                  )}
                        </Modal.Body>Modal.Body>
                
                        <Modal.Footer style={{ borderTop: '1px solid #dee2e6', justifyContent: 'space-between' }}>
                                  <Button
                                                variant="danger"
                                                onClick={handleClose}
                                                style={{
                                                                background: '#e05c6a',
                                                                border: 'none',
                                                                borderRadius: '6px',
                                                                padding: '7px 18px',
                                                                fontWeight: 500
                                                }}
                                              >
                                              Close Comments Window
                                  </Button>Button>
                                  <Button
                                                variant="primary"
                                                onClick={handleSubmit}
                                                disabled={disabled || saving || (!newComment.trim() && !(isInstructor && instructorText !== instructorComment))}
                                                style={{
                                                                borderRadius: '6px',
                                                                padding: '7px 18px',
                                                                fontWeight: 500
                                                }}
                                              >
                                    {saving ? 'Saving...' : 'Submit Comment'}
                                  </Button>Button>
                        </Modal.Footer>Modal.Footer>
                </Modal>Modal>
          </span>span>
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
