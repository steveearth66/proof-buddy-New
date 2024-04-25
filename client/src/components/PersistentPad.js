import "../scss/_persistent-pad.scss";
import { useState } from "react";
import Col from "react-bootstrap/Col";
import logger from "../utils/logger";

export default function PersistentPad({ equation, onHighlightChange }) {
  const [highlightedText, setHighlightedText] = useState("");

  const handelSelection = () => {
    try {
      setHighlightedText("");
      const range = window.getSelection().getRangeAt(0);
      const startOffset = range.startOffset;
      const endOffset = range.endOffset;

      const selectionRange = { start: startOffset, end: endOffset };
      handelHighlight(selectionRange);
    } catch (error) {
      logger.log("Error in handelSelection: ", error);
    }
  };

  const handelHighlight = (selectionRange) => {
    const selectedPart = findSelectionParenthesis(selectionRange);
    if (!checkParenthesesConsistency(selectedPart)) {
      const highlighted = balanceParentheses(selectedPart);
      setHighlightedText(highlighted);
      onHighlightChange(getStartIndex(highlighted));
    } else {
      setHighlightedText(selectedPart);
      onHighlightChange(getStartIndex(selectedPart));
    }
  };

  const getStartIndex = (selectedText) => {
    return equation.indexOf(selectedText);
  };

  const findSelectionParenthesis = (selectionRange) => {
    const start = selectionRange.start;
    const end = selectionRange.end;
    let openParenthesisIndex = -1;
    let closeParenthesisIndex = -1;

    for (let i = start; i >= 0; i--) {
      if (equation[i] === "(") {
        openParenthesisIndex = i;
        break;
      }
    }

    for (let i = end; i < equation.length; i++) {
      if (equation[i] === ")") {
        closeParenthesisIndex = i;
        break;
      }
    }

    if (openParenthesisIndex !== -1 && closeParenthesisIndex !== -1) {
      return equation.substring(
        openParenthesisIndex,
        closeParenthesisIndex + 1
      );
    }
  };

  const checkParenthesesConsistency = (selectedText) => {
    if (!selectedText) {
      return;
    }

    const stack = [];

    for (let i = 0; i < selectedText.length; i++) {
      const char = selectedText[i];
      if (char === "(") {
        stack.push(char);
      } else if (char === ")") {
        if (stack.length === 0) {
          return false; // More closing parentheses than opening ones
        }
        stack.pop();
      }
    }

    return stack.length === 0; // Return true if stack is empty, false otherwise
  };

  const balanceParentheses = (selectedText) => {
    const stack = [];

    // Find the starting index of the selected text in the equation
    const startIndex = equation.indexOf(selectedText);
    if (startIndex === -1) {
      // Selected text not found in equation
      return selectedText;
    }

    // Find the start index of the expression containing the selected text
    let start = startIndex;
    while (start > 0 && equation[start] !== "(") {
      start--;
    }

    // Find the end index of the expression containing the selected text
    let end = startIndex + selectedText.length;
    while (end < equation.length && equation[end] !== ")") {
      end++;
    }

    // Extract the entire expression containing the selected text
    let expression = equation.substring(start, end + 1);

    if (!checkParenthesesConsistency(expression)) {
      expression = balanceParentheses(expression);
    }

    // Push opening parentheses onto the stack
    for (let i = 0; i < expression.length; i++) {
      const char = expression[i];
      if (char === "(") {
        stack.push(char);
      } else if (char === ")") {
        if (stack.length === 0) {
          // Add an opening parenthesis to balance
          expression = expression.slice(0, i) + "(" + expression.slice(i);
          stack.push("(");
        } else {
          stack.pop();
        }
      }
    }

    // Add missing closing parentheses to balance
    while (stack.length > 0) {
      expression += ")";
      stack.pop();
    }
    return expression;
  };

  return (
    <Col xs={8}>
      <p
        onMouseUp={handelSelection}
        dangerouslySetInnerHTML={{
          __html: highlightedText
            ? equation.replace(
                highlightedText,
                `<span class="highlight">${highlightedText}</span>`
              )
            : equation
        }}
        className="pad"
      />
    </Col>
  );
}
