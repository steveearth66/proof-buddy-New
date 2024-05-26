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

    const selectedText = equation.substring(
      selectionRange.start,
      selectionRange.end
    );

    if (selectedText.charAt(0) === "(") {
      levels.push(selectedText);
      const beforeCollapse = equation.substring(0, selectionRange.start);
      const afterCollapse = equation.substring(selectionRange.end);
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
          equation: withCollapse,
          selectionRange: {
            start: beforeCollapse.length,
            end: beforeCollapse.length + keyword.length + 2
          }
        };
      }
    }

    if (selectedText.charAt(0) === "[") {
      const beforeBrackets = equation.substring(0, selectionRange.start);
      const afterBrackets = equation.substring(selectionRange.end);
      const restored =
        beforeBrackets + levels[levels.length - 1] + afterBrackets;

      return {
        equation: restored,
        selectionRange: {
          start: beforeBrackets.length,
          end: beforeBrackets.length + levels[levels.length - 1].length
        }
      };
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
