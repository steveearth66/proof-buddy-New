from .ERCommon import Type, RacType
import sympy as sp

class Generic:
    def __init__(self, type: RacType = RacType((None, Type.ANY))):
        self._racType = type
    
    @property
    def racType(self):
        return self._racType

class GenericInt(Generic):
    def __init__(self, assumption: str = 'Non-negative'):
        super().__init__(RacType((None, Type.INT)))
        self.__assumption = assumption
        match self.__assumption:
            case 'Positive':
                self.__minVal = 1
                self.__maxVal = float('inf')
            case 'Non-negative':
                self.__minVal = 0
                self.__maxVal = float('inf')
            case 'Non-positive':
                self.__minVal = float('-inf')
                self.__maxVal = 0
            case 'Negative':
                self.__minVal = float('-inf')
                self.__maxVal = -1
            case 'None':
                self.__minVal = float('-inf')
                self.__maxVal = float('inf')    
    
    def __lt__(self, other):
        if isinstance(other, GenericInt):
            return self.__maxVal < other.__minVal
        if isinstance(other, int):
            return self.__maxVal < other
    
    def __le__(self, other):
        if isinstance(other, GenericInt):
            return self.__maxVal <= other.__minVal
        if isinstance(other, int):
            return self.__maxVal <= other
    
    def __gt__(self, other):
        if isinstance(other, GenericInt):
            return self.__minVal > other.maxVal
        if isinstance(other, int):
            return self.__minVal > other
    
    def __ge__(self, other):
        if isinstance(other, GenericInt):
            return self.__minVal >= other.maxVal
        if isinstance(other, int):
            return self.__minVal >= other
    
    def __eq__(self, other):
        if isinstance(other, GenericInt):
            return self.__minVal == other.__minVal == self.__maxVal == other.__maxVal
        if isinstance(other, int):
            return self.__minVal == other and self.__maxVal == other
    
    def __ne__(self, other):
        if isinstance(other, GenericInt):
            return self.__maxVal < other.__minVal or self.__minVal > other.__maxVal
        if isinstance(other, int):
            return self.__minVal > other or self.__maxVal < other

class GenericBool(Generic):
    def __init__(self):
        super().__init__(RacType((None, Type.BOOL)))

class GenericList(Generic):
    def __init__(self, neverNull: bool = False):
        super().__init__(RacType((None, Type.LIST)))
        self.neverNull = neverNull
