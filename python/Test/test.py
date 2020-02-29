# Test socket connection with UR
import numpy as np
import socket 
import time
HOST = "192.168.56.102" # The remote host 
PORT = 30002 # The same port as used by the server 
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
s.connect((HOST, PORT)) 

s.send("set_digital_out(2,True)\n".encode()) 

#s.send(b"set_tcp(p[-0.11324,0.0,0.11216,0.0,-0.757,0.0])\n")
data = s.recv(1024) 

s.send(b"movel([10,20,0, 0,0,1], a=1.2, v=0.25, t=0, r=0)")
s.send(b"movel([10,20,100, 0,0,1], a=1.2, v=0.25, t=0, r=0)")

data = s.recv(1024) 
s.close() 

print ("Starting new procedure")
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
count = 0v
while (count < 10):    
    time.sleep(0.05)
    s.send(b"set_digital_out(2,True)\n")
    time.sleep(0.1)
    print ("0.2 seconds are up already")
    s.send(b"set_digital_out(7,True)\n")
    time.sleep(2)
    s.send(b"movej([-0.5405182705025187, -2.350330184112267, -1.316631037266588, -2.2775736604458237, 3.3528323423665642, -1.2291967454894914], a=1.3962634015954636, v=1.0471975511965976)\n")
    time.sleep(2)
    s.send(b"movej([-0.7203210737806529, -1.82796919039503, -1.8248107684866093, -1.3401161163439792, 3.214294414832996, -0.2722986670990757], a=1.3962634015954636, v=1.0471975511965976)\n")
    time.sleep(2)
    s.send(b"movej([-0.5405182705025187, -2.350330184112267, -1.316631037266588, -2.2775736604458237, 3.3528323423665642, -1.2291967454894914], a=1.3962634015954636, v=1.0471975511965976)\n")
    time.sleep(2)
    s.send(b"movej([-0.720213311630304, -1.8280069071476523, -1.8247689994680725, -1.3396385689499288, 3.215063610324356, -0.27251695975573664], a=1.3962634015954636, v=1.0471975511965976)\n")
    time.sleep(2)
    s.send(b"movej([-0.540537125683036, -2.2018732555807086, -1.0986348160112505, -2.6437150406384227, 3.352864759694935, -1.2294883935868013], a=1.3962634015954636, v=1.0471975511965976)\n")
    time.sleep(2)
    s.send(b"movej([-0.5405182705025187, -2.350330184112267, -1.316631037266588, -2.2775736604458237, 3.3528323423665642, -1.2291967454894914], a=1.3962634015954636, v=1.0471975511965976)\n")
    time.sleep(2)
    s.send(b"movej([-0.7203210737806529, -1.570750000000000, -1.570750000000000, -1.3401161163439792, 3.2142944148329960, -0.2722986670990757], t=4.0000000000000000, r=0.0000000000000000)\n")
    time.sleep(4)
    s.send(b"set_digital_out(2,False)\n")
    time.sleep(0.05)
    print ("0.2 seconds are up already")
    s.send(b"set_digital_out(7,False)\n")
    time.sleep(1)
    count = count + 1
    print ("The count is: {}".format(count))
    time.sleep(1)
    data = s.recv(1024)
    print ("Received", repr(data))
s.close()

