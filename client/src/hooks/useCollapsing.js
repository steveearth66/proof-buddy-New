const useCollapsing = () => {
  const levels = [];

  const handleCollapsing = (equation, selectionRange) => {
    console.log("Collapsing: ", equation, selectionRange);
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

    const selectedText = findSelectionParenthesis(equation, selectionRange);
    const bracketText = findSelectionBrackets(equation, selectionRange);
    console.log(bracketText);

    if (selectedText.charAt(0) === "(") {
      levels.push(selectedText);
      const startIndex = equation.indexOf(selectedText);
      const endIndex = startIndex + selectedText.length;
      const beforeCollapse = equation.substring(0, startIndex);
      const afterCollapse = equation.substring(endIndex);
      let keywordPosition = 2;
      let keyword = selectedText.substring(1, keywordPosition);

      while (!keywords.includes(keyword)) {
        keywordPosition++;
        if (keywordPosition > 20) {
          break;
        }
        keyword = selectedText.substring(1, keywordPosition);
      }

      if (selectedText.charAt(keywordPosition) === "?") {
        keyword = keyword + "?";
      }

      if (keywordPosition < 20) {
        const withCollapse =
          beforeCollapse + "[" + keyword + "]" + afterCollapse;

        return {
          result: withCollapse,
          collapse: {
            start: beforeCollapse.length,
            end: beforeCollapse.length + keyword.length + 2
          }
        };
      }
    }

    if (bracketText.charAt(0) === "[") {
      const beforeBrackets = equation.substring(0, selectionRange.start);
      const afterBrackets = equation.substring(selectionRange.end);
      const restored =
        beforeBrackets + levels[levels.length - 1] + afterBrackets;
      console.log("Restored: ", restored);
      return {
        result: restored,
        collapse: {
          start: beforeBrackets.length,
          end: beforeBrackets.length + levels[levels.length - 1].length
        }
      };
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
  return { handleCollapsing };
};
export { useCollapsing };
