import logging
import os
import sys
import time
import numpy as np

def unimplemented(func):
    '''
    A decorator function for print the current running function's name
    Just for the debug process. 
    '''
    def wrap_func(*args, **kwargs):               
        logging.info('{}({}) is not implemented.'.format(func.__name__, args))
        func(*args, **kwargs)
    return wrap_func
    
    
def show_memory_info(hint):
    '''
    Show memory used by current 
    '''
    pid = os.getpid()
    p = psutil.Process(pid)
    
    info = p.memory_full_info()
    memory = info.uss / 1024. / 1024
    logging.info('{} memory used: {} MB'.format(hint, memory))
    
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='/domain-result.log',
                        filemode='w')
    
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # add the handler to the root logger
    logging.getLogger().addHandler(console)  
    list_1 = (i for i in range(100000))
    show_memory_info('After generated list_1')
    cwd = os.getcwd()
    print('current dir is ' + cwd)
    new_path = os.path.join(cwd, "nw")
    print('new dir is ' + new_path)