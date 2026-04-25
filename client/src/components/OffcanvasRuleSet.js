import React, { useState, useCallback, useEffect } from "react";
import OffCanvas from "react-bootstrap/Offcanvas";
import Table from "react-bootstrap/Table";
import ruleSet from "./RuleSet";
import Form from "react-bootstrap/Form";

/**
 *  OffcanvasRuleSet component that displays at the bottom of the application in the "er-racket" page when the user presses the "View Rule Set" Button.
 * It uses react-bootstrap's components.
 */

const OffcanvasRuleSet = ({ isActive, toggleFunction }) => {
  const [filteredRules, setFilteredRules] = useState(ruleSet());
  const [evalRules, applyRules] = filteredRules;
  /* Present list of Rules for View Rule Set Offcanvas */

  const [height, setHeight] = useState(window.innerHeight * 0.3);
  const [isResizing, setIsResizing] = useState(false);

  const startResizing = useCallback((e) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback(
    (e) => {
      if (isResizing) {
        // Calculate height: Viewport height minus the current mouse Y position
        const newHeight = window.innerHeight - e.clientY;
        
        // Constraints: Min 150px, Max 90% of screen (do not increase to 100% or user will be unable to close)
        if (newHeight > 150 && newHeight < window.innerHeight * 0.9) {
          setHeight(newHeight);
        }
      }
    },
    [isResizing]
  );

  useEffect(() => {
    if (isResizing) {
      window.addEventListener("mousemove", resize);
      window.addEventListener("mouseup", stopResizing);
    } else {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    }
    return () => {
      window.removeEventListener("mousemove", resize);
      window.removeEventListener("mouseup", stopResizing);
    };
  }, [isResizing, resize, stopResizing]);

  const onSearch = (e) => {
    const searchValue = e.target.value.toLowerCase();
    if (!searchValue) {
      setFilteredRules(ruleSet());
      return;
    }

    const rules = ruleSet();
    const filteredRules = [];
    rules.forEach(ruleSet => 
      filteredRules.push(ruleSet.filter((rule) => {
        return (
          (rule.name ? rule.name.toLowerCase().includes(searchValue.toLowerCase()) : false) ||
              String(rule.procedure).toLowerCase().includes(searchValue.toLowerCase()) ||
              String(rule.highlight).toLowerCase().includes(searchValue.toLowerCase()) ||
              String(rule.result).toLowerCase().includes(searchValue.toLowerCase())
        );
      }))
    );
    setFilteredRules(filteredRules);
  };

  return (
    <OffCanvas
      className="Offcanvas"
      id="rule-set"
      show={isActive}
      onHide={toggleFunction}
      scroll="true"
      placement="bottom"
      style={{ 
        height: `${height}px`, 
        transition: isResizing ? "none" : "transform 0.3s ease-in-out" 
      }}
    >
      <div
        onMouseDown={startResizing}
        style={{
          height: "10px",
          cursor: "ns-resize",
          width: "100%",
          position: "absolute",
          top: 0,
          left: 0,
          zIndex: 1051,
          backgroundColor: isResizing ? "rgba(0,123,255,0.2)" : "transparent"
        }}
      />
      <OffCanvas.Body>
        <Form.Control
          type="text"
          placeholder="Search"
          className="search-input"
          onChange={onSearch}
        />
        <p>
          <strong>Rules must be in the form "<em>&lt;prefix&gt; &lt;name&gt;</em>",
            where <em>&lt;prefix&gt;</em> is the appropriate prefix ("eval", "rewrite", or "apply")
          and <em>&lt;name&gt;</em> is the rule name of the procedure.</strong><br />
          <strong>Examples:</strong> "eval +", "rewrite first-cons", "apply F" (where F is a definition)
        </p>
        <p>Note: any rule can be done in “reverse” (i.e. selecting result to get the highlight) by using the “Substitution” button</p>
        <h3>"Eval" Procedures:</h3>
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>Name/Procedure</th>
              <th>Highlight</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {evalRules.map((rule, index) => (
              <tr key={index}>
                <td>{rule.procedure}</td>
                <td>{rule.highlight}</td>
                <td>{rule.result}</td>
              </tr>
            ))}
          </tbody>
        </Table>
        <h3>Rewrite Rules:</h3>
        <Table striped bordered hover>
          <thead>
            <tr>
              <th style={{ width: "10%" }}>Rule Name</th>
              <th>Highlight</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {applyRules.map((rule, index) => (
              <tr key={index}>
                <td>{rule.procedure}</td>
                <td>{rule.highlight}</td>
                <td>{rule.result}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </OffCanvas.Body>
    </OffCanvas>
  );
};

export default OffcanvasRuleSet;
