import "../scss/_persistent-pad.scss";
import { useState, useEffect, useRef, useCallback } from "react";
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
    editableLineNum,
    startPosition,
    ruleValue,
    onRuleChange,
    isRuleReadOnly,
    rulePlaceholder,
    isRuleInvalid,
    ruleValidationError,
    ...props
  },
  ref
) {
  const [highlightedText, setHighlightedText] = useState("");
  const [selectionRange, setSelectionRange] = useState({ start: 0, end: 0 });
  const [selected, setSelected] = useState(startPosition);

  const lineNumRef = useRef(lineNum);
  let origTree = jsonTree;

  // Expose moveSelection and focus to parent
  const padDivRef = useRef(null);
  useImperativeHandle(ref, () => ({
    moveSelection,
    focus: () => padDivRef.current && padDivRef.current.focus()
  }));

  useEffect(() => {
    const saveHighlightToSession = (highlightedText) => {
      const savedHighlights = JSON.parse(
        sessionStorage.getItem("highlights") || "[]"
      );

      savedHighlights.forEach((highlight, index) => {
        if (highlight.equation === equation && highlight.side === side) {
          savedHighlights.splice(index, 1);
        }
      });

      savedHighlights.push({
        equation,
        highlightedText,
        side,
        selectionRange
      });
      sessionStorage.setItem("highlights", JSON.stringify(savedHighlights));
    };

    if (highlightedText) {
      saveHighlightToSession(highlightedText);
    }
  }, [highlightedText, side, selectionRange, equation]);

  useEffect(() => {
    const savedHighlights = JSON.parse(
      sessionStorage.getItem("highlights") || "[]"
    );

    savedHighlights.forEach((highlight) => {
      if (highlight.equation === equation && highlight.side === side) {
        setHighlightedText(highlight.highlightedText);
        setSelectionRange(highlight.selectionRange);
      }
    });
  }, [equation, side]);

  const moveSelection = useCallback(
    (direction) => {
      let newSelected = selected;

      if (direction === "up") {
        newSelected = origTree[newSelected].parent ?? newSelected;
      } else if (direction === "down") {
        newSelected = origTree[newSelected].children[0] ?? newSelected;
      } else if (direction === "left") {
        newSelected = origTree[newSelected].leftSib ?? newSelected;
      } else if (direction === "right") {
        newSelected = origTree[newSelected].rightSib ?? newSelected;
      }

      onHighlightChange(newSelected);
      setSelected(newSelected);
    },
    [selected, origTree, onHighlightChange]
  );

  return (
    <Col xs={12}>
      <div
        id={`persistent-pad-${lineNumRef.current}`}
        ref={padDivRef}
        tabIndex={0}
        {...props}
      >
        <DivMakerComponent
          expr={jsonTree}
          selected={selected}
          origTree={origTree}
          lineNumber={lineNumRef.current}
        />
        <Form.Floating className="mb-3" style={{ marginTop: "1rem" }}>
          <Form.Control
            type="text"
            value={ruleValue}
            placeholder={rulePlaceholder}
            onChange={onRuleChange}
            readOnly={isRuleReadOnly}
            isInvalid={isRuleInvalid}
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
  );
});

export default PersistentPad;