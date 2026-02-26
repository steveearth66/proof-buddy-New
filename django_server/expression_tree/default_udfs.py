"""
Default User-Defined Functions (UDFs) for ProofBuddy

These UDFs are provided to all users and appear in the Definitions window.
Users can enable/disable them but cannot edit or delete them.
"""

DEFAULT_UDFS = [
    {
        "id": -1,  # Negative ID indicates non-database definition
        "label": "(length L)",
        "type": "LIST>INT",
        "expression": "(if (null? L) 0 (+ 1 (length (rest L))))",
        "notes": "Built-in function to calculate the length of a list",
        "applied": False,
        "is_default": True,
        "deletable": False,
    },
    {
        "id": -2,  # Negative ID indicates non-database definition
        "label": "(append L M)",
        "type": "(LIST, LIST)>LIST",
        "expression": "(if (null? L) M (cons (first L) (append (rest L) M)))",
        "notes": "Built-in function to append two lists together",
        "applied": False,
        "is_default": True,
        "deletable": False,
    },
    # {
    #     "id": -3,  # Negative ID indicates non-database definition
    #     "label": "(F a b)",
    #     "type": "(INT, INT)>INT",
    #     "expression": "(if (zero? b) a (+ 1 (F a (- b 1))))",
    #     "notes": "question 1 of lab9",
    #     "applied": False,
    #     "is_default": True,
    #     "deletable": False,
    # },
    # {
    #     "id": -4,  # Negative ID indicates non-database definition
    #     "label": "(H a b)",
    #     "type": "(INT, INT)>INT",
    #     "expression": "(if (< a b) 0 (+ 1 (H (- a b) b)))",
    #     "notes": "question 2 of lab9",
    #     "applied": False,
    #     "is_default": True,
    #     "deletable": False,
    # },
    # {
    #     "id": -5,  # Negative ID indicates non-database definition
    #     "label": "(Q a b)",
    #     "type": "(INT, INT)>INT",
    #     "expression": "(if (= b 1) a (+ a (Q a (- b 1))))",
    #     "notes": "question 3 of lab9",
    #     "applied": False,
    #     "is_default": True,
    #     "deletable": False,
    # },
    # {
    #     "id": -6,  # Negative ID indicates non-database definition
    #     "label": "(M x L)",
    #     "type": "(INT, LIST)>INT",
    #     "expression": "(if (zero? x) (first L) (M (- x 1) (rest L)))",
    #     "notes": "question 4 of lab9",
    #     "applied": False,
    #     "is_default": True,
    #     "deletable": False,
    # },
    {
        "id": -7,  # Negative ID indicates non-database definition
        "label": "(h x)",
        "type": "INT>INT",
        "expression": "(if (zero? x) 0 (+ (- (* 4 x) 5) (h (- x 1))))",
        "notes": "used for question1 of lab12",
        "applied": True,
        "is_default": True,
        "deletable": False,
    },
    {
        "id": -8,  # Negative ID indicates non-database definition
        "label": "(countTruthTableRows vars)",
        "type": "INT>INT",
        "expression": "(if (zero? vars) 1 (* 2 (countTruthTableRows (- vars 1))))",
        "notes": "counts the number of rows in a truth table with the given number of variables",
        "applied": False,
        "is_default": True,
        "deletable": False,
    },
]
