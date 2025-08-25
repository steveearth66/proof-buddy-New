// DivMaker.js
function getClassNames(e, selected, blueHighlightPosition) {
    const classes = ["node"];
    if (selected === e.startPosition) {
        classes.push("highlight");
    } else {
        classes.push("no-highlight");
    }
    if (blueHighlightPosition === e.startPosition) {
        classes.push("blue-highlight");
    }
    return classes.join(" ");
}

function recurse(e, selected, blueHighlightPosition, jsonDict, prefix) {
  if (!e) {
    return <div>&nbsp;</div>;
  }

  const node = Object.create(e);
  node.children = node.children || [];

  const uniqueId = `${prefix}-${node.startPosition}`;

  if (Array.isArray(node.children) && node.children.length > 0) {
    return (
        <div className={getClassNames(node, selected, blueHighlightPosition)} id={uniqueId} key={uniqueId}>
            {node.data}{node.children.map((child) =>
            recurse(jsonDict[child], selected, blueHighlightPosition, jsonDict, prefix)
        )})
      </div>
    );
  }

  return (
      <div className={getClassNames(node, selected, blueHighlightPosition)} id={uniqueId} key={uniqueId}>
      &nbsp;{node.data}&nbsp;
    </div>
  );
}

export default function DivMakerComponent({ expr, selected, blueHighlightPosition, origTree, lineNumber = 0 }) {
    return recurse(expr[0], selected, blueHighlightPosition, origTree, lineNumber);
}