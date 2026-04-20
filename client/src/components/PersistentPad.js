// PersistentPad.jsx

import "../scss/_persistent-pad.scss";
import { useState, useEffect, useRef, useCallback } from "react";
import { Row, Col, Form, Button, OverlayTrigger, Tooltip } from 'react-bootstrap';
import { Eye, EyeSlash } from "react-bootstrap-icons";
import DivMakerComponent from "./divMaker";
import React, { useImperativeHandle, forwardRef } from "react";

const PersistentPad = forwardRef(function PersistentPad(
  {
    equation,
    onHighlightChange,
    side,
    jsonTree,
    lineNum,
    startPosition,
    resultNode,
    ruleValue,
    onRuleChange,
    onRuleKeyDown,
    isRuleReadOnly,
    rulePlaceholder,
    isRuleInvalid,
    ruleValidationError,
    isEditRow,
    showEyeButtons = false,
    currentUserType,
    hideExpression = false,
    hideJustification = false,
    onRuleHiddenToggle,
    onExpressionHiddenToggle,
    ...props
  },
  ref
) {
  const [highlightedText, setHighlightedText] = useState("");
  const [selectionRange, setSelectionRange] = useState({ start: 0, end: 0 });
  const [selected, setSelected] = useState(startPosition ?? 0);
  const [rule, setRule] = useState(ruleValue);
  const [localEquation, setLocalEquation] = useState(equation);
  
  const [showRule, setShowRule] = useState(!hideJustification);
  const [showExpression, setShowExpression] = useState(!hideExpression);
  
  const padDivRef = useRef(null);
  const lineNumRef = useRef(lineNum);
  
  const equationHash = equation ? equation.substring(0, 50) : '';
  const highlightKey = `${lineNum}-${side}-${equationHash}`;

  useEffect(() => { 
    setRule(ruleValue); 
  }, [ruleValue]);

  useEffect(() => {
    setLocalEquation(equation);
  }, [equation]);

  useEffect(() => {
    setShowRule(hideJustification !== true);
  }, [hideJustification]);

  useEffect(() => {
    setShowExpression(hideExpression !== true);
  }, [hideExpression]);

  useEffect(() => {
    if (startPosition === 0 && lineNum > 0 && jsonTree && jsonTree[0]) {
      setSelected(0);
    } else {
      setSelected(startPosition);
    }
  }, [startPosition, lineNum, jsonTree]);

  useEffect(() => {
    const savedHighlights = JSON.parse(sessionStorage.getItem("highlights") || "[]");
    const filteredHighlights = savedHighlights.filter(
      h => h.key !== highlightKey
    );

    filteredHighlights.push({
      key: highlightKey,
      equation,
      highlightedText,
      side,
      selectionRange,
      selected
    });

    sessionStorage.setItem("highlights", JSON.stringify(filteredHighlights));
  }, [highlightedText, side, selectionRange, selected, equation, highlightKey]);

  useEffect(() => {
    const savedHighlights = JSON.parse(sessionStorage.getItem("highlights") || "[]");
    const matchingHighlight = savedHighlights.find(
      highlight => highlight.key === highlightKey
    );

    if (matchingHighlight) {
      setHighlightedText(matchingHighlight.highlightedText);
      setSelectionRange(matchingHighlight.selectionRange);
      if (typeof matchingHighlight.selected === 'number' && startPosition === 0) {
        setSelected(matchingHighlight.selected);
      }
    }
  }, [highlightKey, startPosition]);

  const moveSelection = useCallback((direction) => {
    const directionMap = {
      up: 'parent',
      down: 'children',
      left: 'leftSib',
      right: 'rightSib'
    };

    const property = directionMap[direction];
    if (!property) return;

    let newSelected = selected;
    if (property === 'children') {
      newSelected = jsonTree[selected]?.children?.[0] ?? selected;
    } else {
      newSelected = jsonTree[selected]?.[property] ?? selected;
    }

    onHighlightChange(newSelected);
    setSelected(newSelected);
  }, [selected, jsonTree, onHighlightChange]);

  useImperativeHandle(ref, () => ({
    moveSelection,
    focus: () => padDivRef.current?.focus(),
    getRuleValue: () => rule,
    setRuleValue: setRule,
    getStartPosition: () => selected,
    setStartPosition: setSelected,
    getEquationValue: () => localEquation
  }));

  const handleEquationChange = (e) => {
    setLocalEquation(e.target.value);
  };

  const handleRuleChange = (e) => {
    let transformedValue = e.target.value;
    
    if (transformedValue.split(" ")[0] !== "eval") {
      transformedValue = transformedValue.replace(/=/g, "\u21A6");
    }
    
    setRule(transformedValue);
    
    const transformedEvent = {
      ...e,
      target: {
        ...e.target,
        value: transformedValue
      }
    };
    
    onRuleChange?.(transformedEvent);
  };

  const colors = ['#DAA520', '#0066cc', '#cc0000', '#228B22'];
  const currentLineColor = colors[lineNum % 4];
  const previousLineColor = colors[(lineNum - 1) % 4];

  // Determine if content should be hidden based on:
  // 1. Student account type: Use database flags (hideExpression/hideJustification)
  // 2. Non-student (instructor/admin): Use local toggles (can temporarily override)
  const isStudent = currentUserType?.is_student === true;
  const shouldHideRule = isStudent ? hideJustification : !showRule;
  const shouldHideExpression = isStudent ? hideExpression && !isEditRow : !showExpression;

  const handleRuleVisibilityToggle = async () => {
    if (onRuleHiddenToggle) {
      try {
        const isNowHidden = await onRuleHiddenToggle();
      } catch (error) {
        console.warn("Toggle failed, maintaining current UI state.");
      }
    }
  }

  const handleExpressionVisibilityToggle = async () => {
    if (onExpressionHiddenToggle) {
      try {
        const isNowHidden = await onExpressionHiddenToggle();
      } catch (error) {
        console.warn("Toggle failed, maintaining current UI state.");
      }
    }
  }
  
  return (
    <Row className="persistent-pad-row" style={{ alignItems: "flex-start" }}>
      <Col md={{ span: 11, offset: 1 }}>
        <div style={{ 
          borderLeft: `4px solid transparent`,
          borderImage: `linear-gradient(to bottom, ${previousLineColor} 50%, ${currentLineColor} 50%) 1`,
          paddingLeft: '8px'
        }}>
        <Form.Floating className="mb-2">
          <Form.Control
            as="textarea"
            value={rule}
            placeholder={rulePlaceholder}
            onChange={handleRuleChange}
            onKeyDown={onRuleKeyDown}
            readOnly={isRuleReadOnly}
            isInvalid={isRuleInvalid}
            disabled={!isEditRow}
            style={{ 
              minHeight: '40px',
              resize: 'none',
              overflow: 'hidden',
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word',
              paddingRight: '2.5rem',
              borderColor: !isStudent && shouldHideRule ? '#ff9090' : '',
              WebkitTextSecurity: isStudent && shouldHideRule ? "disc" : "none"
            }}
            rows={1}
          />
          <label>{rulePlaceholder}</label>
          
          {/* Only show eye button for non-students */}
          {lineNum !== 0 && showEyeButtons && !isStudent && (rule !== '') && (
            <OverlayTrigger
              popperConfig={{ strategy: 'fixed' }}
              overlay={
                <Tooltip id={`tooltip-hide-row-${lineNum}`}>
                {showRule ? "Hide" : "Unhide"} Rule
                </Tooltip>
              }
            >
              <Button
                variant="outline-secondary"
                onClick={handleRuleVisibilityToggle}
                style={{
                  position: 'absolute',
                  top: '50%',
                  right: '0.25rem',
                  transform: 'translateY(-50%)',
                  height: 'calc(100% - 0.5rem)',
                  padding: '0 0.5rem',
                  borderRadius: '0.25rem',
                  zIndex: 2
                }}
                tabIndex={-1}
              >
                {showRule ? <EyeSlash /> : <Eye />}
              </Button>
            </OverlayTrigger>
            
          )}

          {isRuleInvalid && (
            <Form.Control.Feedback type="invalid" tooltip>
              {ruleValidationError}
            </Form.Control.Feedback>
          )}
        </Form.Floating>
        </div>
      </Col>
      <Col md="12">
        <div
          style={{ 
            position: 'relative',
            borderLeft: `4px solid ${currentLineColor}`,
            paddingLeft: '8px',
            marginBottom: '0.5rem'
          }}
        >
          {isEditRow && hideExpression && isStudent ? (
            /* RENDER EDITABLE INPUT WHEN HIDDEN & EDITING */
            <Form.Control
              as="textarea"
              value={localEquation}
              onChange={handleEquationChange}
              rows={1}
              style={{
                wordWrap: 'break-word',
                minHeight: '40px',
                paddingRight: '2.5rem',
                resize: 'none'
              }}
              placeholder="Enter expression..."
            />
          ) : (
            /* RENDER STANDARD READONLY VIEW */
            <div
              id={`persistent-pad-${lineNumRef.current}`}
              ref={padDivRef}
              tabIndex={0}
              style={{ 
                wordWrap: 'break-word', 
                overflowWrap: 'break-word', 
                whiteSpace: 'normal',
                minHeight: '40px',
                border: '1px solid',
                borderColor: !isStudent && shouldHideExpression ? '#ff9090' : '#ced4da',
                borderRadius: '4px',
                padding: '8px',
                paddingRight: '2.5rem',
                WebkitTextSecurity: isStudent && shouldHideExpression ? "disc" : "none"
              }}
              {...props}
            >
              {jsonTree && jsonTree[0] ? (
                <DivMakerComponent
                  expr={jsonTree}
                  selected={selected}
                  resultNode={resultNode}
                  origTree={jsonTree}
                  lineNumber={lineNumRef.current}
                />
              ) : (
                <div>{equation || '\u00A0'}</div>
              )}
            </div>
          )}
          
          {/* Only show eye button for non-students */}
          {showEyeButtons && !isStudent && equation !== '' && (
            <OverlayTrigger
              popperConfig={{ strategy: 'fixed' }}
              overlay={
                <Tooltip id={`tooltip-hide-row-${lineNum}`}>
                {showExpression ? "Hide" : "Unhide"} Expression
                </Tooltip>
              }
            >
              <Button
                variant="outline-secondary"
                onClick={handleExpressionVisibilityToggle}
                style={{ 
                  position: 'absolute',
                  top: '50%',
                  right: '0.25rem',
                  transform: 'translateY(-50%)',
                  height: 'calc(100% - 0.5rem)',
                  padding: '0 0.75rem',
                  borderRadius: '0.25rem',
                  zIndex: 2
                }}
                tabIndex={-1}
              >
                {showExpression ? <EyeSlash /> : <Eye />}
              </Button>
            </OverlayTrigger>
          )}
        </div>
      </Col>
    </Row>
  );
});

export default PersistentPad;