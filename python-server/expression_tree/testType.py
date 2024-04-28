from typeFile import *

err_objs=[
    (RacType("tuple"),"err: expected tuple, got <class 'str'>"),
    (RacType((5)), "err: expected tuple, got <class 'int'>"),
    (RacType((1,2,3)), "err: expected tuple of len 2, got len 3"),
    (RacType((1,)), "err: expected tuple of len 2, got len 1"),
    (RacType(tuple([])), "err: expected tuple of len 2, got len 0"),
    (RacType(None), "err: received nothing"),
    (RacType((tuple([]),Type.INT)),"err: domain tuple was empty"),
    (RacType((0,Type.INT)), "err: expected domain to be tuple/None, got <class 'int'>")
]

good_objs=[
(RacType((None,Type.INT)),"INT"),
(RacType(((RacType((None, Type.BOOL)),), RacType((None, Type.INT)))), "BOOL > INT"),
(RacType(((RacType((None, Type.INT)),),RacType(((RacType((None, Type.BOOL)),), RacType((None, Type.INT)))))), "INT > (BOOL > INT)"),
(RacType(((RacType((None, Type.INT)), RacType((None, Type.LIST))), RacType(((RacType((None, Type.BOOL)),), RacType((None, Type.INT)))))),"(INT, LIST) > (BOOL > INT)"),
(RacType(((RacType((None, Type.INT)), RacType((None, Type.LIST))),RacType((None, Type.BOOL)))),"(INT, LIST) > BOOL"),
(RacType(((RacType(((RacType((None, Type.INT)),), RacType((None, Type.BOOL)))),), RacType((None, Type.LIST)))),"(INT > BOOL) > LIST"),
(RacType(((RacType(((RacType((None, Type.INT)),), RacType((None, Type.BOOL)))),RacType((None, Type.LIST))), RacType(((RacType((None, Type.LIST)), \
    RacType((None, Type.INT))), RacType((None, Type.BOOL)))))),"(INT > BOOL, LIST) > ((LIST, INT) > BOOL)")
]

print("\nTESTING: Type printing:\n")
fails = 0
for trial in err_objs+good_objs:
    obj,expected = trial
    print("input:","ILLFORMED" if "err" in (ans := str(obj)) else ans)
    word = "err" if "err" in ans else "output"
    if ans == expected:
        print(f"PASS: expected {word}: {ans[5:]}\n")
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        fails=+1
print("all tests passed!\n" if fails==0 else f"number of fails: {fails}\n")

for t in good_objs:
    obj=t[0]
    print(f"object {obj} is type {obj.getType()}, domainList = {TypeList(obj.getDomain())}, range = {obj.getRange()}")
    print(f"obj is an INT: {obj.isType('INT')}, obj is a FUNCTION: {obj.isType('FUNCTION')}")