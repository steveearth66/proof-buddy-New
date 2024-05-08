from typing import Union, Tuple, List
from enum import Enum


class Type(Enum):
    TEMP = 'TEMP'
    BOOL = 'BOOL'
    INT = 'INT'
    LIST = 'LIST'
    PARAM = 'PARAM'
    ANY = 'ANY'
    ERROR = 'ERROR'
    NONE = 'NONE'
    FUNCTION = 'FUNCTION'  # this is only here for getType and should never be used directly

    def __str__(self):
        return self.value  # this makes it so that printing Type.INT will return the string 'INT'


RacType = Union[Tuple[None, Type], Tuple[Tuple['RacType', ...], Type]]

# TypeList is a list of strings of RacTypes, used for prettyprinting only


class TypeList:
    def __init__(self, value: list[RacType]):
        self.value = value

    def __str__(self):
        if self.value == None:
            return '[None]'
        else:
            return '[' + ', '.join(str(x) for x in self.value) + ']'


class RacType:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        if (val := self.value) == None:
            return "err: received nothing"
        if (tval := type(val)) != tuple:
            return f"err: expected tuple, got {tval}"
        if (n := len(val)) != 2:
            return f"err: expected tuple of len 2, got len {n}"
        if (domtup := val[0]) == None:
            return str(val[1])  # this is a base type, so there's no function
        if type(domtup) != tuple:
            return f"err: expected domain to be tuple/None, got {type(domtup)}"
        if len(domtup) == 0:
            return f"err: domain tuple was empty"
        outstr = str(val[1])
        if ">" in outstr:  # adding parens around the range if it's a function
            outstr = "("+outstr+")"
        if len(domtup) == 1 and ">" not in (sdom := str(domtup[0])):
            # don't need parens around domain if it's just one nonfunction
            return f"{sdom} > {outstr}"
        return f"({', '.join(str(x) for x in domtup)}) > {outstr}"

    def __eq__(self, other):
        if other == None:
            return False
        else:
            return str(self) == str(other)

    def getType(self) -> RacType:
        if self.value[0] == None:
            return self.value[1]
        return Type.FUNCTION

    def getDomain(self):
        if self.getType() != Type.FUNCTION:
            return None
        return list(self.value[0])

    def getRange(self) -> RacType:
        if self.getType() != Type.FUNCTION:
            return None
        return self.value[1]

    def isType(self, typeStr) -> bool:
        return str(self.getType()) == typeStr
