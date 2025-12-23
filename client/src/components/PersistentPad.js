import "../scss/_persistent-pad.scss";
import { useState, useEffect, useRef, useCallback } from "react";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Form from "react-bootstrap/Form";
import DivMakerComponent from "./divMaker";
import React, { useImperativeHandle, forwardRef } from "react";

const PersistentPad = forwardRef(function PersistentPad(
  {
    equation,
    onHighlightChange,
    side,
    jsonTree,
    lineNum,
    // editableLineNum, // removed to clean warnings
    startPosition,
    ruleValue,
    onRuleChange,
    isRuleReadOnly,
    rulePlaceholder,
    isRuleInvalid,
    ruleValidationError,
    isEditRow,
    ...props
  },
  ref
) {
  const [highlightedText, setHighlightedText] = useState("");
  const [selectionRange, setSelectionRange] = useState({ start: 0, end: 0 });
  const [selected, setSelected] = useState(startPosition ?? 0);
  const [rule, setRule] = useState(ruleValue);
  
  const padDivRef = useRef(null);
  const lineNumRef = useRef(lineNum);

  useEffect(() => { 
    setRule(ruleValue); 
  }, [ruleValue]);

  useEffect(() => {
    setSelected(startPosition);
  }, [startPosition])

  // Session storage management for highlights
  useEffect(() => {
    if (!highlightedText) return;

    const savedHighlights = JSON.parse(sessionStorage.getItem("highlights") || "[]");
    const filteredHighlights = savedHighlights.filter(
      highlight => !(highlight.equation === equation && highlight.side === side)
    );

    filteredHighlights.push({
      equation,
      highlightedText,
      side,
      selectionRange
    });

    sessionStorage.setItem("highlights", JSON.stringify(filteredHighlights));
  }, [highlightedText, side, selectionRange, equation]);

  // Load highlights from session storage
  useEffect(() => {
    const savedHighlights = JSON.parse(sessionStorage.getItem("highlights") || "[]");
    const matchingHighlight = savedHighlights.find(
      highlight => highlight.equation === equation && highlight.side === side
    );

    if (matchingHighlight) {
      setHighlightedText(matchingHighlight.highlightedText);
      setSelectionRange(matchingHighlight.selectionRange);
    }
  }, [equation, side]);

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
    setStartPosition: setSelected
  }));

  const handleRuleChange = (e) => {
    let transformedValue = e.target.value;
    
    // Transform = to arrow if rule doesn't start with "eval"
    if (transformedValue.split(" ")[0] !== "eval") {
      transformedValue = transformedValue.replace(/=/g, "\u21A6");
    }
    
    setRule(transformedValue);
    
    // Create a new event with the transformed value
    const transformedEvent = {
      ...e,
      target: {
        ...e.target,
        value: transformedValue
      }
    };
    
    onRuleChange?.(transformedEvent);
  };

  return (
    <Row className="persistent-pad-row" style={{ alignItems: "center" }}>
      <Col>
        <div
          id={`persistent-pad-${lineNumRef.current}`}
          ref={padDivRef}
          tabIndex={0}
          {...props}
        >
          <DivMakerComponent
            expr={jsonTree}
            selected={selected}
            origTree={jsonTree}
            lineNumber={lineNumRef.current}
          />
        </div>
      </Col>
      <Col md="5">
        <Form.Floating className="mb-3">
          <Form.Control
            type="text"
            value={rule}
            placeholder={rulePlaceholder}
            onChange={handleRuleChange}
            readOnly={isRuleReadOnly}
            isInvalid={isRuleInvalid}
            disabled={!isEditRow}
          />
          <label>{rulePlaceholder}</label>
          {isRuleInvalid && (
            <Form.Control.Feedback type="invalid" tooltip>
              {ruleValidationError}
            </Form.Control.Feedback>
          )}
        </Form.Floating>
      </Col>
    </Row>
  );
});

export default PersistentPad;