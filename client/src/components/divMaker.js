// DivMaker.js
function getClassNames(e, selected, prefix) {
  // return ["node", selected === e.startPosition ? "highlight" : "no-highlight"].join(" "); // removed to clean warnings
  const prefixClass = prefix ? `line-${prefix}` : null;
  return ["node", prefixClass, selected === e.startPosition ? "highlight" : "no-highlight"].filter(Boolean).join(" ");
}

function recurse(e, selected, jsonDict, prefix) {
  if (!e) {
    return <div>&nbsp;</div>;
  }

  const node = Object.create(e);
  node.children = node.children || [];

  const uniqueId = `${prefix}-${node.startPosition}`;

  if (Array.isArray(node.children) && node.children.length > 0) {
    return (
      <div className={getClassNames(node, selected, prefix)} id={uniqueId} key={uniqueId}>
        {node.data}{node.children.map((child) => 
          recurse(jsonDict[child], selected, jsonDict, prefix)
        )})
      </div>
    );
  }

  return (
    <div className={getClassNames(node, selected, prefix)} id={uniqueId} key={uniqueId}>
      &nbsp;{node.data}&nbsp;
    </div>
  );
}

export default function DivMakerComponent({ expr, selected, origTree, lineNumber = 0 }) {
  return recurse(expr[0], selected, origTree, lineNumber);
}