import React, { useState } from "react";
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

  const onSearch = (e) => {
    const searchValue = e.target.value;
    const rules = ruleSet();
    const filteredRules = [];
    rules.forEach(ruleSet => 
      filteredRules.push(ruleSet.filter((rule) => {
        return (
          rule.name ? rule.name.toLowerCase().includes(searchValue.toLowerCase()) : false ||
          rule.procedure.toLowerCase().includes(searchValue.toLowerCase()) ||
          rule.highlight.toLowerCase().includes(searchValue.toLowerCase()) ||
          rule.result.toLowerCase().includes(searchValue.toLowerCase())
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
    >
      <OffCanvas.Body>
        <Form.Control
          type="text"
          placeholder="Search"
          className="search-input"
          onChange={onSearch}
        />
        <p>
          <strong>Rules must be in the form "<em>&lt;prefix&gt; &lt;name&gt;</em>", 
          where <em>&lt;prefix&gt;</em> is the appropriate prefix (either "eval" or "apply")
          and <em>&lt;name&gt;</em> is the rule name of the procedure.</strong><br />
          <strong>Examples:</strong> "eval +", "apply first" 
        </p>
        <p>Note: any rule can be done in “reverse” (i.e. selecting result to get the highlight) by using the “Substitution” button</p>
        <h3>"Eval" Procedures:</h3>
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>Rule Name/Procedure</th>
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
        <h3>"Apply" Procedures:</h3>
        <Table striped bordered hover>
          <thead>
            <tr>
              <th style={{ width: "10%" }}>Rule Name</th>
              <th style={{ width: "10%" }}>Procedure</th>
              <th>Highlight</th>
              <th>Result</th>
            </tr>
          </thead>
          <tbody>
            {applyRules.map((rule, index) => (
              <tr key={index}>
                {rule.name ? (
                  <>
                    <td>{rule.name}</td>
                    <td>{rule.procedure}</td>
                  </>
                ) : (
                  <td colSpan="2" align="center">{rule.procedure}</td>
                )}
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
