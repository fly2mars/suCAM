#https://github.com/thegrims/gcodesender.py
import time
import serial

ser = None
try:
        
    ser = serial.Serial(
        port='\\\\.\\COM4',
        baudrate=115200,
        parity=serial.PARITY_ODD,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS)
    if ser.isOpen():
        ser.close()
    ser.open()
    ser.isOpen()
    
    ser.write("M119\r")
    out = ''# let's wait one second before reading output (let's give device time to answer)
    time.sleep(1)
    while ser.inWaiting() > 0:
        out += ser.read(40)
    if out != '':
        print(">>" + out)
except Exception as e:
    print("[Exception occured:\n{0}]\n".format(e))
finally:
    if ser != None:
        ser.close()
