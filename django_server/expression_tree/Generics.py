from .ERCommon import Type, RacType
import sympy as sp

class Generic:
    def __init__(self, type):
        self._racType = type
    
    @property
    def racType(self):
        return self._racType

class GenericInt(Generic):
    def __init__(self, assumption: str = 'Non-negative'):
        super().__init__(RacType((None, Type.INT)))
        self._assumption = assumption
        match self._assumption:
            case 'Positive':
                self._minVal = 1
                self._maxVal = float('inf')
            case 'Non-negative':
                self._minVal = 0
                self._maxVal = float('inf')
            case 'Non-positive':
                self._minVal = float('-inf')
                self._maxVal = 0
            case 'Negative':
                self._minVal = float('-inf')
                self._maxVal = -1
            case 'None':
                self._minVal = float('-inf')
                self._maxVal = float('inf')    
    
    @property
    def assumption(self):
        return self._assumption
    
    @property
    def minVal(self):
        return self._minVal
    
    @property
    def maxVal(self):
        return self._maxVal
    
    def __lt__(self, other):
        if isinstance(other, GenericInt):
            return self.maxVal < other.minVal
        if isinstance(other, int):
            return self.maxVal < other
    
    def __le__(self, other):
        if isinstance(other, GenericInt):
            return self.maxVal <= other.minVal
        if isinstance(other, int):
            return self.maxVal <= other
    
    def __gt__(self, other):
        if isinstance(other, GenericInt):
            return self.minVal > other.maxVal
        if isinstance(other, int):
            return self.minVal > other
    
    def __ge__(self, other):
        if isinstance(other, GenericInt):
            return self.minVal >= other.maxVal
        if isinstance(other, int):
            return self.minVal >= other
    
    def __eq__(self, other):
        if isinstance(other, GenericInt):
            return self.minVal == other.minVal == self.maxVal == other.maxVal
        if isinstance(other, int):
            return self.minVal == other and self.maxVal == other
    
    def __ne__(self, other):
        if isinstance(other, GenericInt):
            return self.maxVal < other.minVal or self.minVal > other.maxVal
        if isinstance(other, int):
            return self.minVal > other or self.maxVal < other

class GenericBool(Generic):
    def __init__(self):
        super().__init__(RacType((None, Type.BOOL)))

class GenericList(Generic):
    def __init__(self, neverNull: bool = True):
        super().__init__(RacType((None, Type.LIST)))
        self._neverNull = neverNull
    
    @property
    def neverNull(self):
        return self._neverNull
class GenericAny(Generic):
    def __init__(self):
        super().__init__(RacType((None, Type.ANY)))
    
    def treatAsInt(self):
        return GenericInt()
    
    def treatAsBool(self):
        return GenericBool()
    
    def treatAsList(self):
        return GenericList()