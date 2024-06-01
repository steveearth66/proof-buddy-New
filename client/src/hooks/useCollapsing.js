import { useState } from "react";

const useCollapsing = () => {
  const [levels, setLevels] = useState([]);

  const collapse = (equation, selectionRange) => {
    const keywords = [
      "length",
      "rest",
      "append",
      "null?",
      "null",
      "if",
      "first",
      "+",
      "Î»"
    ];
    try {
      const selectedText = findSelectionParenthesis(equation, selectionRange);
      let collapsedText;

      if (!checkParenthesisConsistency(selectedText)) {
        collapsedText = balanceParenthesis(equation, selectedText);
      } else {
        collapsedText = selectedText;
      }

      if (collapsedText && collapsedText.charAt(0) === "(") {
        const startIndex = equation.indexOf(collapsedText);
        const endIndex = startIndex + collapsedText.length;
        const beforeCollapse = equation.substring(0, startIndex);
        const afterCollapse = equation.substring(endIndex);
        let keywordPosition = 2;
        let keyword = collapsedText.substring(1, keywordPosition);

        while (!keywords.includes(keyword)) {
          keywordPosition++;
          if (keywordPosition > 20) {
            break;
          }
          keyword = collapsedText.substring(1, keywordPosition);
        }

        if (collapsedText.charAt(keywordPosition) === "?") {
          keyword = keyword + "?";
        }

        if (keywordPosition < 20) {
          const withCollapse =
            beforeCollapse + "[" + keyword + "]" + afterCollapse;

          const level = {
            collapsedText,
            range: {
              start: withCollapse.indexOf("[" + keyword + "]"),
              end:
                withCollapse.indexOf("[" + keyword + "]") + keyword.length + 2
            }
          };
          setLevels((prev) => [...prev, level]);

          return {
            result: withCollapse,
            collapseRange: {
              start: beforeCollapse.length,
              end: beforeCollapse.length + keyword.length + 2
            }
          };
        }
      }
    } catch (error) {
      console.error("Error collapsing brackets: ", error);
      return equation;
    }
  };

  const restore = (equation, selectionRange) => {
    try {
      const bracketText = findSelectionBrackets(equation, selectionRange);
      const startIndex = equation.indexOf(bracketText);
      const endIndex = startIndex + bracketText.length;
      const toRestore = levels.filter(
        (level) =>
          level.range.start === startIndex && level.range.end === endIndex
      )[0]?.collapsedText;

      if (toRestore && bracketText && bracketText.charAt(0) === "[") {
        const beforeBrackets = equation.substring(0, startIndex);
        const afterBrackets = equation.substring(endIndex);

        const restored = beforeBrackets + toRestore + afterBrackets;

        setLevels((prev) =>
          prev.filter(
            (level) =>
              level.range.start !== startIndex && level.range.end !== endIndex
          )
        );

        return {
          result: restored
        };
      }
    } catch (error) {
      console.error("Error restoring brackets: ", error);
      return equation;
    }
  };

  const findSelectionParenthesis = (equation, selectionRange) => {
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

  const checkParenthesisConsistency = (selectedText) => {
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

  const balanceParenthesis = (equation, selectedText) => {
    try {
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

      if (!checkParenthesisConsistency(expression)) {
        expression = balanceParenthesis(expression);
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
    } catch (error) {
      console.error("Error balancing parenthesis: ", error);
      return equation;
    }
  };

  const findSelectionBrackets = (equation, selectionRange) => {
    const start = selectionRange.start;
    const end = selectionRange.end;
    let openBracketIndex = -1;
    let closeBracketIndex = -1;

    for (let i = start; i >= 0; i--) {
      if (equation[i] === "[") {
        openBracketIndex = i;
        break;
      }
    }

    for (let i = end; i < equation.length; i++) {
      if (equation[i] === "]") {
        closeBracketIndex = i;
        break;
      }
    }

    if (openBracketIndex !== -1 && closeBracketIndex !== -1) {
      return equation.substring(openBracketIndex, closeBracketIndex + 1);
    }
  };

  // const handleDoubleClick = (element) => {

  //   const keywords = ['length', 'rest', 'append', 'null?', 'null', 'if', 'first', '+', 'Î»']; //d
  //   //console.log(levels.length);
  //   //var fullText= element.target.value;
  //   var selectedText = (element.target.value).substring(element.target.selectionStart, element.target.selectionEnd);
  //   //console.log(selectedText);
  //   //console.log('DoubleClickHook: ' + selectedText);
  //   if(selectedText.charAt(0) == '(') {
  //     levels.push(selectedText);
  //     var beforeCollapse = (element.target.value).substring(0, element.target.selectionStart);
  //     var afterCollapse = (element.target.value).substring(element.target.selectionEnd);
  //     var keywordPosition = 2;
  //     var keyword = selectedText.substring(1, keywordPosition);

  //     while (!keywords.includes(keyword)){
  //       keywordPosition++;
  //       if(keywordPosition > 20){
  //         break;
  //       }
  //       keyword = selectedText.substring(1, keywordPosition);
  //       //console.log(keyword.length);
  //     }
  //     if (selectedText.charAt(keywordPosition) == '?'){
  //       keyword = keyword + '?';
  //     }
  //     if(keywordPosition < 20){
  //       var withCollapse = beforeCollapse + '[' + keyword + ']' + afterCollapse;
  //       element.target.value = withCollapse;
  //       element.target.setSelectionRange(beforeCollapse.length, beforeCollapse.length + keyword.length + 2);
  //       element.target.style.setProperty('--selectBGColor', 'Pink');
  //     }
  //   }
  //   if(selectedText.charAt(0) == '[') {
  //     //console.log('Should Restore: ' + levels[levels.length - 1]);
  //     var beforeBrackets = (element.target.value).substring(0, element.target.selectionStart);
  //     var afterBrackets = (element.target.value).substring(element.target.selectionEnd);

  //     var restored = beforeBrackets + levels[levels.length - 1] + afterBrackets;

  //     element.target.value = restored;
  //     element.target.setSelectionRange(beforeBrackets.length, beforeBrackets.length + levels[levels.length - 1].length);
  //     element.target.style.setProperty('--selectBGColor', 'Cyan');

  //     levels.splice(length - 1, 1)
  //   }
  // }
  return {
    collapse,
    restore,
    findSelectionParenthesis,
    checkParenthesisConsistency,
    balanceParenthesis
  };
};
export { useCollapsing };
