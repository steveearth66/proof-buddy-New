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
]
