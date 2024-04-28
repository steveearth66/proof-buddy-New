from recParser import buildTree, preProcess
from Labeler import labelTree#, fillPositions
from Decorator import decorateTree, remTemps, checkFunctions

# builds AST from a FLAWLESS string
def fastNode(myStr):
    decTree = decorateTree(labelTree(buildTree(preProcess(myStr,[])[0],)[0]),[])[0]
    errLog = remTemps(decTree, [])
    return checkFunctions(decTree,errLog)[0]

myTree=fastNode("(+ x 2)")
myTree.fullDebug(True)
print(myTree)