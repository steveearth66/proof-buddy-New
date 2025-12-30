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
    resultNode,
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
  
  // Build stable key from lineNum + side + equation hash
  const equationHash = equation ? equation.substring(0, 50) : '';
  const highlightKey = `${lineNum}-${side}-${equationHash}`;

  useEffect(() => { 
    setRule(ruleValue); 
  }, [ruleValue]);

  useEffect(() => {
    // Initialize selection; if startPosition is 0 and this isn't the premise, default to node 1
    if (startPosition === 0 && lineNum > 0 && jsonTree && jsonTree[0]) {
      // Non-premise lines should default to root node if no startPosition provided
      setSelected(0);
    } else {
      setSelected(startPosition);
    }
  }, [startPosition, lineNum, jsonTree])

  // Session storage management for highlights and selection
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

  // Load highlights from session storage (including selection)
  useEffect(() => {
    const savedHighlights = JSON.parse(sessionStorage.getItem("highlights") || "[]");
    const matchingHighlight = savedHighlights.find(
      highlight => highlight.key === highlightKey
    );

    if (matchingHighlight) {
      setHighlightedText(matchingHighlight.highlightedText);
      setSelectionRange(matchingHighlight.selectionRange);
      // Only restore selected from sessionStorage if startPosition is 0 (default/unset)
      // This prevents overwriting newly generated lines that have explicit startPosition
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

  // Determine border colors based on line numbers
  const currentLineColor = lineNum % 2 === 0 ? '#0066cc' : '#FF8F1C'; // blue for even, orange for odd
  const previousLineColor = (lineNum - 1) % 2 === 0 ? '#0066cc' : '#FF8F1C'; // color of line above

  return (
    <Row className="persistent-pad-row" style={{ alignItems: "flex-start" }}>
      <Col md={{ span: 10, offset: 2 }}>
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
            readOnly={isRuleReadOnly}
            isInvalid={isRuleInvalid}
            disabled={!isEditRow}
            style={{ 
              minHeight: '40px',
              resize: 'none',
              overflow: 'hidden',
              whiteSpace: 'pre-wrap',
              wordWrap: 'break-word'
            }}
            rows={1}
          />
          <label>{rulePlaceholder}</label>
          {isRuleInvalid && (
            <Form.Control.Feedback type="invalid" tooltip>
              {ruleValidationError}
            </Form.Control.Feedback>
          )}
        </Form.Floating>
        </div>
      </Col>
      <Col md="12">
        <div style={{ 
          borderLeft: `4px solid ${currentLineColor}`,
          paddingLeft: '8px'
        }}>
        <div
          id={`persistent-pad-${lineNumRef.current}`}
          ref={padDivRef}
          tabIndex={0}
          style={{ 
            wordWrap: 'break-word', 
            overflowWrap: 'break-word', 
            whiteSpace: 'normal',
            minHeight: '40px',
            border: '1px solid #ced4da',
            borderRadius: '4px',
            padding: '8px'
          }}
          {...props}
        >
          <DivMakerComponent
            expr={jsonTree}
            selected={selected}
            resultNode={resultNode}
            origTree={jsonTree}
            lineNumber={lineNumRef.current}
          />
        </div>
        </div>
      </Col>
    </Row>
  );
});

export default PersistentPad;