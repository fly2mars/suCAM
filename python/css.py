'''
Compute CSS point

example:
    kappa, smooth = compute_curve_css(c,3)
    css_idx = find_css_point(kappa)
'''
import pathengine
import cv2
import numpy as np
from scipy.signal import savgol_filter

def get_gaussian_kernel(sigma, M):
    '''
    refer to https://cedar.buffalo.edu/~srihari/CSE555/Normal2.pdf
    '''
    L = int((M - 1) / 2);
    sigma_sq = sigma * sigma;
    sigma_quad = sigma_sq*sigma_sq;
    dg = np.zeros([M])
    d2g = np.zeros([M])
    gaussian = np.zeros([M])
   
    g = cv2.getGaussianKernel(M, sigma)
    g.reshape(len(g))
    
    for i in range(2*L+1):
        x = i-L
        gaussian[i] = g[i]
        dg[i] = (-x/sigma_sq) * g[i]
        d2g[i] = (-sigma_sq + x*x)/sigma_quad * g[i]
    return gaussian.reshape((1,M)), dg.reshape((1,M)), d2g.reshape((1,M))

def smooth_curve(curve, sigma, is_open = False):
    '''
    By refer to https://www.sciencedirect.com/science/article/pii/S0031320301000401
    According to the properties of convolution, the derivatives of g(x) * u(x) 
    can be calculated easily computed by g'(x) * u(x)
    '''
    M = round((10.0*sigma+1.0) / 2.0) * 2 - 1;
    assert(M % 2 == 1)
    g, dg, d2g = get_gaussian_kernel(sigma, M)
    X = curve[:,0]
    Y = curve[:,1]
    
    id_list = list(range(M))
    id_list = list(np.array(id_list) - int(M/2))
    id_list.reverse()
    xM = np.zeros( (M, len(X)) )
    yM = np.zeros( (M, len(X)) )
    row = 0
    for i in id_list:
        xM[row] = np.roll(X, i)
        yM[row] = np.roll(Y, i)
        row += 1     
    if(is_open):
        #todo: regulate xM, yM
        i=0
   
        
    gX  = np.vstack((np.sum(g.dot( xM), axis = 0), np.sum(g.dot(yM), axis = 0) ) ) 

    dX  = np.sum(dg.dot(xM), axis = 0)
    dY  = np.sum(dg.dot(yM), axis = 0)
    dXX = np.sum(d2g.dot(xM), axis = 0)
    dYY = np.sum(d2g.dot(yM), axis = 0)
    
    return gX.T, dX, dY, dXX, dYY
def compute_curve_css(curve, sigma, is_open=False):
   
    smooth, dX, dY, dXX, dYY = smooth_curve(curve, sigma)
    
    kappa = (dX*dYY - dXX*dY) / np.power(dX*dX + dY*dY, 1.5);
 
    return kappa, smooth

    
def find_css_point(kappa):
    idx_list = []
    for i in range(len(kappa)-1):
        if (kappa[i] < 0 and kappa[i+1] > 0) or (kappa[i] > 0 and kappa[i+1] < 0):
            idx_list.append(i)
    return idx_list
    
if __name__ == '__main__':
    
    filepath = "E:/git/suCAM/python/images/slice.png"
    reverseImage = True
    
    pe = pathengine.pathEngine()  
    pe.generate_contours_from_img(filepath, reverseImage)
    pe.im = cv2.cvtColor(pe.im, cv2.COLOR_GRAY2BGR)
    contour_tree = pe.convert_hiearchy_to_PyPolyTree() 
    pe.path2d.group_boundary = pe.get_contours_from_each_connected_region(contour_tree, '0')
    
    c = pe.path2d.group_boundary['0-0'][0]
    c = pathengine.suPath2D.resample_curve_by_equal_dist(c, 10)
    
    # a circle
    #x = [x*np.pi/9 for x in range(18)]
    #c = [np.cos(x) * 50 + 100, np.sin(x) * 50 + 100]
    #c = np.array(c).T.astype(int) 
    
    kappa, smooth = compute_curve_css(c,3)
    #kappa = savgol_filter(kappa, 5, 1)
    pathengine.suPath2D.draw_line(np.vstack([c, c[0]]), pe.im, (255,255,0))
    pathengine.suPath2D.draw_line(np.vstack([smooth, smooth[0]]), pe.im, (0,0,255))
    css_idx = find_css_point(kappa)
    
    colors = pathengine.suPath2D.generate_RGB_list(30)
    cv2.circle(pe.im, tuple(smooth[0].astype(int)), 10, colors[29])
    print(kappa)
    i=0
    for idx in css_idx:
        cv2.circle(pe.im, tuple(smooth[idx].astype(int)), 4, colors[i])
        i += 1
    cv2.imshow("Art", pe.im)
    cv2.waitKey(0)             
    
   
    