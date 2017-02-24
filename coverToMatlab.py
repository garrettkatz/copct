def coverToMatlab(cover, fname):
    # cover is (u,k) pair
    matFile = open(fname, "w")
    matFile.write("% demo var d should be in calling workspace\n");
    matFile.write("e = struct('task',{});\n")
    for (u,k) in zip(cover[0],cover[1][1:]):
        print(u[1])
        taskstr = "e(end+1).task = HTN.groundedTask('%s', {"%u[1]
        for arg in u[2]:
            print(arg)
            if type(arg)==str:
                taskstr += "'%s', "%arg
            if type(arg) in [int, float]:
                taskstr += "%f, "%arg
            if type(arg)==tuple: # matrix or state
                if len(arg) > 0 and len(arg[0]) > 0 and type(arg[0][0]) == str: # state
                    taskstr += "d(%d).state, "%k # state index in demo
                else:
                    taskstr += "["
                    for r in range(len(arg)):
                        for c in range(len(arg[r])):
                            taskstr += "%f, "%arg[r][c]
                        taskstr += "; "
                    taskstr += "], ";
            if arg==None: # matching state
                taskstr += "d(%d).state, "%k # state index in demo
        taskstr += "});\n";
        matFile.write(taskstr)
        matFile.write("e(end).i = %d;\n"%k)
        matFile.write("e(end).state = d(%d).state;\n"%k)
    matFile.close()

def main():
    cover = (
        (None, "task1", (1,((1,2),(3,4)))),
        (None, "task2", (3,4,"a")),
    )
    coverToMatlab(cover,"testCover.m")
