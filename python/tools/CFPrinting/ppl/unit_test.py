import sys, os

if __name__ == "__main__":
    #print(sys.path)
    #sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
    print(os.path.realpath(__file__))
    print(os.path.dirname(os.path.realpath(__file__)))
    print(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
    print(sys.path)
    #sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
    if os.path.dirname(os.path.realpath(__file__)) not in sys.path:
        sys.path.append(os.path.dirname(os.path.realpath(__file__)))    
    else:
        print("Already added")