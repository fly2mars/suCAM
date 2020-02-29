import urx
import math
import numpy as np


def PointsInCircum(r,n=100):
    pi = math.pi
    return [(math.cos(2*pi/n*x)*r,math.sin(2*pi/n*x)*r) for x in range(0,n+1)]


l = 0.05
v = 0.05
a = 0.3
rob = urx.Robot("192.168.56.102")
#rob = urx.Robot("192.168.1.11")
rob.set_tcp((0,0,0.115,0,0,0))
rob.set_payload(0.1, (0,0,0))
print(rob.secmon._dict)
print(rob.secmon.running)
rob.secmon.running = True
print(rob.secmon._parser.version)
try:
    l = 0.05
    v = 0.05
    a = 0.14
    pose = rob.getl()
    ori = pose.copy()
    print(type(pose))
    pose[1] += l
    print("absolute move in base coordinate ")
    rob.movel(pose, acc=a, vel=v)
    print("absolute move back in base coordinate ")
    pose = rob.getl()
    pose[1] -= l  
    rob.movel(pose, acc=a, vel=v)
    
    pose = rob.getl()
    path = np.array(PointsInCircum(0.1,10) ) # n*2
    path = path + pose[0:2]
    dp = pose.copy()
    for p in path:
        print("iter begin")       
        pose[0:2] = p
        rob.movel(pose, acc=a, vel=v)
        #print("relative move in base coordinate ")
        #rob.translate((l, 0, 0), acc=a, vel=v)
        #print("relative move back and forth in tool coordinate")
        #rob.translate_tool((0, -l, 0), acc=a, vel=v)
        #rob.translate_tool((0, -l, 0), acc=a, vel=v)
    rob.movel(ori, acc=a, vel=v)
except Exception as e:
    print("[Exception occured:\n{0}]\n".format(e))
finally:
    #rob.stop()
    rob.close()