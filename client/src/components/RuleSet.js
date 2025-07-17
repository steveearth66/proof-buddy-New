/**
 * @returns An array of two arrays of rule objects. First array is for eval rules, second is for apply rules.
 */
const ruleSet = () => {
  //just creates a ruleset for the ER Page. If new rules are added, they need only be added to this file

  return [
    [
      {
        procedure: "first",
        highlight: "(first '(a b c … z))",
        result: "a"
      },
      {
        procedure: "rest",
        highlight: "(rest '(a b c … z))",
        result: "'(b c … z)"
      },
      {
        procedure: "cons",
        highlight: "(cons a '(b c … z))",
        result: "'(a b c … z)"
      },
      {
        procedure: "if",
        highlight: "(if #t x y)",
        result: "x"
      },
      {
        procedure: "if",
        highlight: "(if #f x y)",
        result: "y"
      },
      {
        procedure: "if",
        highlight: "(if x y y)",
        result: "y"
      },
      {
        procedure: "null?",
        highlight: "(null? null)",
        result: "#t"
      },
      {
        procedure: "null?",
        highlight: "(null? (cons a L))",
        result: "#f"
      },
      {
        procedure: "zero?",
        highlight: "(zero? 0)",
        result: "#t"
      },
      {
        procedure: "zero?",
        highlight: "(zero? n), where n ≠ 0",
        result: "#f"
      },
      {
        procedure: "and",
        highlight: "(and p q)",
        result: "p ∧ q"
      },
      {
        procedure: "or",
        highlight: "(or p q)",
        result: "p ∨ q"
      },
      {
        procedure: "not",
        highlight: "(not p)",
        result: "¬p"
      },
      {
        procedure: "implies",
        highlight: "(implies p q)",
        result: "p → q"
      },
      {
        procedure: "xor",
        highlight: "(xor p q)",
        result: "p ⊕ q"
      },
      {
        procedure: "+, -, *, =, <, >, <=, >=",
        highlight: "(<function> a b)",
        result: "a <function> b"
      },
      {
        procedure: "quotient",
        highlight: "(quotient a b)",
        result: "⌊a / b⌋"
      },
      {
        procedure: "remainder",
        highlight: "(remainder a b)",
        result: "a % b"
      },
      {
        procedure: "expt",
        highlight: "(expt a b)",
        result: <>a<sup>b</sup></>
      }
    ],
    [
      {
        name: "cons",
        procedure: "cons-first-rest",
        highlight: "(cons (first L) (rest L))",
        result: "L"
      },
      {
        name: "first",
        procedure: "first-cons",
        highlight: "(first (cons x L))",
        result: "x"
      },
      {
        name: "rest",
        procedure: "rest-cons",
        highlight: "(rest (cons x L))",
        result: "L"
      },
      {
        procedure: "<function name>",
        highlight: "(<function name> ...)",
        result: "function definiton with parameters mapped to values"
      },
      {
        procedure: "<proof name>",
        highlight: "<proof LHS>",
        result: "<proof RHS>"
      },
      {
        procedure: "IH",
        highlight: "<IH LHS>",
        result: "<IH RHS>"
      },
      {
        procedure: "-+",
        highlight: "(- (+ k a) a), where a is any integer",
        result: <>k <em>(Note: this is just a special case of math)</em></>
      },
      {
        procedure: "math",
        highlight: "<mathematical expression>",
        result: "<equivalent mathematical expression>"
      }
    ]
  ];
}

export default ruleSet;
