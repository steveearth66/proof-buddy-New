from .ERCommon import Type, RacType

class ERGeneric:
    """Base class for generics"""
    def __init__(self, type):
        self._racType = type
    
    @property
    def racType(self):
        return self._racType

class GenericInt(ERGeneric):
    """
    Class for generic integers\n
    Can be used with comparison operators against matching types/classes (int, GenericInt, GenericAny)\n
    Comparison evaluating to false means that it is not guaranteed to be true, not that it is guaranteed to be false
    
    Attributes:
        assumption: a string out of five valid strings: 'Positive', 'Negative', 'Non-negative', 'Non-positive', and 'None'. \
            'Non-negative' by default
        minVal: the minimum possible value of the GenericInt, currently assigned by providing an assumption
        maxVal: the maximum possible value of the GenericInt, currently assigned by providing an assumption
    """
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
            case _:
                raise ValueError('Invalid string for GenericInt assumption')
    
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
        if isinstance(other, GenericAny):
            return self < GenericInt()
    
    def __le__(self, other):
        if isinstance(other, GenericInt):
            return self.maxVal <= other.minVal
        if isinstance(other, int):
            return self.maxVal <= other
        if isinstance(other, GenericAny):
            return self <= GenericInt()
    
    def __gt__(self, other):
        if isinstance(other, GenericInt):
            return self.minVal > other.maxVal
        if isinstance(other, int):
            return self.minVal > other
        if isinstance(other, GenericAny):
            return self > GenericInt()
    
    def __ge__(self, other):
        if isinstance(other, GenericInt):
            return self.minVal >= other.maxVal
        if isinstance(other, int):
            return self.minVal >= other
        if isinstance(other, GenericAny):
            return self >= GenericInt()
    
    def __eq__(self, other):
        if isinstance(other, GenericInt):
            return self.minVal == other.minVal == self.maxVal == other.maxVal
        if isinstance(other, int):
            return self.minVal == other and self.maxVal == other
        if isinstance(other, GenericAny):
            return self == GenericInt()
    
    def __ne__(self, other):
        if isinstance(other, GenericInt):
            return self.maxVal < other.minVal or self.minVal > other.maxVal
        if isinstance(other, int):
            return self.minVal > other or self.maxVal < other
        if isinstance(other, GenericAny):
            return self != GenericInt()

class GenericBool(ERGeneric):
    """Class for generic booleans"""
    def __init__(self):
        super().__init__(RacType((None, Type.BOOL)))

class GenericList(ERGeneric):
    """
    Class for generic lists\n
    Attributes:
        neverNull: boolean value indicating whether the list can never be empty. True by default
    """
    def __init__(self, neverNull: bool = True):
        super().__init__(RacType((None, Type.LIST)))
        self._neverNull = neverNull
    
    @property
    def neverNull(self):
        return self._neverNull

class GenericAny(ERGeneric):
    """Class for symbols that can be any type\n
    An instance of GenericAny assumes the behavior of a default instance of other 
    generic classes when interpreted in the appropriate context: e.g GenericInt when used 
    with comparison operators and GenericList when null checking"""
    def __init__(self):
        super().__init__(RacType((None, Type.ANY)))
    
    def __lt__(self, other):
        if isinstance(other, GenericAny):
            return False
        if isinstance(other, (GenericInt, int)):
            return GenericInt() < other
    
    def __le__(self, other):
        if isinstance(other, GenericAny):
            return False
        if isinstance(other, (GenericInt, int)):
            return GenericInt() <= other
    
    def __gt__(self, other):
        if isinstance(other, GenericAny):
            return False
        if isinstance(other, (GenericInt, int)):
            return GenericInt() > other
        
    def __ge__(self, other):
        if isinstance(other, GenericAny):
            return False
        if isinstance(other, (GenericInt, int)):
            return GenericInt() >= other
        
    def __eq__(self, other):
        if isinstance(other, GenericAny):
            return False
        if isinstance(other, (GenericInt, int)):
            return GenericInt() == other

    def __ne__(self, other):
        if isinstance(other, GenericAny):
            return False
        if isinstance(other, (GenericInt, int)):
            return GenericInt() != other       

    @property
    def neverNull(self):
        return GenericList().neverNull