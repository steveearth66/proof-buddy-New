//import "../scss/_persistent-pad.scss";

function enrich(expr) {
  // root has no parent or sibs
  if (expr === null || expr === undefined || expr === "") { // somewhere in the code it is calling before expr gets defined... this is a hack to prevent crashing
    return;
  }
  expr.parent = null;
  expr.leftSib = null;
  expr.rightSib = null;

  let queue = [expr];

  let id = 0;
  let e;

  // breadth-first traversal so we can track parents and sibs
  while (queue.length > 0) {
    e = queue.shift(); // TODO O(n) dequeue
    e.id = id++;

    for (let i = 0; i < e.children.length; i++) {
      let child = e.children[i];

      child.parent = e;

      if (i === 0) {
        child.leftSib = null;
      } else {
        child.leftSib = e.children[i - 1];
      }
      if (i === e.children.length - 1) {
        child.rightSib = null;
      } else {
        child.rightSib = e.children[i + 1];
      }

      queue.push(child);
    }
  }
}
function getClassNames(e, selected) {
  // no-highlight gives unselected nodes invisible border
  // if we had no border previously, elements would shift slightly when selected changes
  // since highlight gives visible border

  // return "node highlight"; // Steve's test until we get arrow selection working to know what's selected
  // /*
  //if (e === null || e === undefined || e === ""||selected === null || selected === undefined || selected === "") { // somewhere in the code it is calling before e gets defined... this is a hack to prevent crashing
  //  return "node highlight";
  //}
  return ["node", selected.id === e.id ? "highlight" : "no-highlight"].join(
    " "
  );
  // */
}
function recurse(e, selected) {
  // if has children, is expression, so surround with parens, no data to display
  // if no children, is value, so display its data without parens, no children to display
  // ids not necessary, just for debugging keys
  if (e === null || e === undefined || e === "") { // somewhere in the code it is calling before e gets defined... this is a hack to prevent crashing
    return <div>&nbsp;</div>;
  }
  if (e.children.length > 0) {
    return (
      <div className={getClassNames(e, selected)} id={e.id} key={e.id}>
        ({e.children.map((child) => recurse(child, false))})
      </div>
    );
  } else {
    return (
      <div className={getClassNames(e, selected)} id={e.id} key={e.id}> 
        &nbsp;{e.data}&nbsp; 
      </div>// added spaces to make it easier to see the values
    );
  }
}

export default function makeDivs(expr, selected) {
  enrich(expr);
  return recurse(expr, selected);
}