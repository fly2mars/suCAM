#!/usr/bin/env python

import cv2
import numpy as np
import math


def robot_command(method):
    def func_wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            print("Exception info:\n{0}".format(exc))

    return func_wrapper


def rotation_matrix(axis, angle):
    matrix = np.eye(3)
    c = np.cos(angle)
    s = np.sin(angle)
    if axis == 'x':
        matrix = [[1, 0, 0],
                  [0, c, -s],
                  [0, s, c]]
    elif axis == 'y':
        matrix = [[c, 0, s],
                  [0, 1, 0],
                  [-s, 0, c]]
    elif axis == 'z':
        matrix = [[c, -s, 0],
                  [s, c, 0],
                  [0, 0, 1]]

    return matrix


# Checks if a matrix is a valid rotation matrix.
def isRotationMatrix(R):
    Rt = np.transpose(R)
    shouldBeIdentity = np.dot(Rt, R)
    I = np.identity(3, dtype=R.dtype)
    n = np.linalg.norm(I - shouldBeIdentity)
    return n < 1e-6


def rotationMatrixToEulerAngles(R):
    sy = math.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

    singular = sy < 1e-6

    if not singular:
        x = math.atan2(R[2, 1], R[2, 2])
        y = math.atan2(-R[2, 0], sy)
        z = math.atan2(R[1, 0], R[0, 0])
    else:
        x = math.atan2(-R[1, 2], R[1, 1])
        y = math.atan2(-R[2, 0], sy)
        z = 0

    return np.array([x, y, z])


def pose2mat(pose):
    assert isinstance(pose, np.ndarray)
    r = cv2.Rodrigues(pose[3:])[0]
    h = np.array([[pose[0]], [pose[1]], [pose[2]]])
    rt = np.concatenate([r, h], axis=1)
    bottom_row = np.array([0, 0, 0, 1]).reshape((1, 4))
    rt = np.concatenate([rt, bottom_row], axis=0)
    return rt


def mat2pose(mat):
    assert isinstance(mat, np.ndarray)
    rvec = cv2.Rodrigues(mat[:3, :3])[0].reshape(1, 3)
    tvec = np.asarray(mat[:3, 3]).reshape(1, 3)
    pose = np.vstack([tvec, rvec]).reshape(6)
    return pose


def eulerAnglesToRotationMatrix(theta):
    R_x = np.array([[1, 0, 0],
                    [0, math.cos(theta[0]), -math.sin(theta[0])],
                    [0, math.sin(theta[0]), math.cos(theta[0])]
                    ])

    R_y = np.array([[math.cos(theta[1]), 0, math.sin(theta[1])],
                    [0, 1, 0],
                    [-math.sin(theta[1]), 0, math.cos(theta[1])]
                    ])

    R_z = np.array([[math.cos(theta[2]), -math.sin(theta[2]), 0],
                    [math.sin(theta[2]), math.cos(theta[2]), 0],
                    [0, 0, 1]
                    ])

    R = np.dot(R_z, np.dot(R_y, R_x))

    return R


def rg6_cmd(range_open, force=50):
    cmd_str = "def rg6ProgOpen():\n";
    cmd_str += "\ttextmsg(\"inside RG6 function called\")\n";

    cmd_str += "\ttarget_width={0}\n".format(range_open);
    cmd_str += "\ttarget_force={0}\n".format(force);
    cmd_str += "\tpayload=1.0\n";
    cmd_str += "\tset_payload1=False\n";
    cmd_str += "\tdepth_compensation=False\n";
    cmd_str += "\tslave=False\n";

    cmd_str += "\ttimeout = 0\n";
    cmd_str += "\twhile get_digital_in(9) == False:\n";
    cmd_str += "\t\ttextmsg(\"inside while\")\n";
    cmd_str += "\t\tif timeout > 400:\n";
    cmd_str += "\t\t\tbreak\n";
    cmd_str += "\t\tend\n";
    cmd_str += "\t\ttimeout = timeout+1\n";
    cmd_str += "\t\tsync()\n";
    cmd_str += "\tend\n";
    cmd_str += "\ttextmsg(\"outside while\")\n";

    cmd_str += "\tdef bit(input):\n";
    cmd_str += "\t\tmsb=65536\n";
    cmd_str += "\t\tlocal i=0\n";
    cmd_str += "\t\tlocal output=0\n";
    cmd_str += "\t\twhile i<17:\n";
    cmd_str += "\t\t\tset_digital_out(8,True)\n";
    cmd_str += "\t\t\tif input>=msb:\n";
    cmd_str += "\t\t\t\tinput=input-msb\n";
    cmd_str += "\t\t\t\tset_digital_out(9,False)\n";
    cmd_str += "\t\t\telse:\n";
    cmd_str += "\t\t\t\tset_digital_out(9,True)\n";
    cmd_str += "\t\t\tend\n";
    cmd_str += "\t\t\tif get_digital_in(8):\n";
    cmd_str += "\t\t\t\tout=1\n";
    cmd_str += "\t\t\tend\n";
    cmd_str += "\t\t\tsync()\n";
    cmd_str += "\t\t\tset_digital_out(8,False)\n";
    cmd_str += "\t\t\tsync()\n";
    cmd_str += "\t\t\tinput=input*2\n";
    cmd_str += "\t\t\toutput=output*2\n";
    cmd_str += "\t\t\ti=i+1\n";
    cmd_str += "\t\tend\n";
    cmd_str += "\t\treturn output\n";
    cmd_str += "\tend\n";
    cmd_str += "\ttextmsg(\"outside bit definition\")\n";

    cmd_str += "\ttarget_width=target_width+0.0\n";
    cmd_str += "\tif target_force>40:\n";
    cmd_str += "\t\ttarget_force=40\n";
    cmd_str += "\tend\n";

    cmd_str += "\tif target_force<4:\n";
    cmd_str += "\t\ttarget_force=4\n";
    cmd_str += "\tend\n";
    cmd_str += "\tif target_width>150:\n";
    cmd_str += "\t\ttarget_width=150\n";
    cmd_str += "\tend\n";
    cmd_str += "\tif target_width<0:\n";
    cmd_str += "\t\ttarget_width=0\n";
    cmd_str += "\tend\n";
    cmd_str += "\trg_data=floor(target_width)*4\n";
    cmd_str += "\trg_data=rg_data+floor(target_force/2)*4*111\n";
    cmd_str += "\tif slave:\n";
    cmd_str += "\t\trg_data=rg_data+16384\n";
    cmd_str += "\tend\n";

    cmd_str += "\ttextmsg(\"about to call bit\")\n";
    cmd_str += "\tbit(rg_data)\n";
    cmd_str += "\ttextmsg(\"called bit\")\n";

    cmd_str += "\tif depth_compensation:\n";
    cmd_str += "\t\tfinger_length = 55.0/1000\n";
    cmd_str += "\t\tfinger_heigth_disp = 5.0/1000\n";
    cmd_str += "\t\tcenter_displacement = 7.5/1000\n";

    cmd_str += "\t\tstart_pose = get_forward_kin()\n";
    cmd_str += "\t\tset_analog_inputrange(2, 1)\n";
    cmd_str += "\t\tzscale = (get_analog_in(2)-0.026)/2.976\n";
    cmd_str += "\t\tzangle = zscale*1.57079633-0.087266462\n";
    cmd_str += "\t\tzwidth = 5+110*sin(zangle)\n";

    cmd_str += "\t\tstart_depth = cos(zangle)*finger_length\n";

    cmd_str += "\t\tsync()\n";
    cmd_str += "\t\tsync()\n";
    cmd_str += "\t\ttimeout = 0\n";

    cmd_str += "\t\twhile get_digital_in(9) == True:\n";
    cmd_str += "\t\t\ttimeout=timeout+1\n";
    cmd_str += "\t\t\tsync()\n";
    cmd_str += "\t\t\tif timeout > 20:\n";
    cmd_str += "\t\t\t\tbreak\n";
    cmd_str += "\t\t\tend\n";
    cmd_str += "\t\tend\n";
    cmd_str += "\t\ttimeout = 0\n";
    cmd_str += "\t\twhile get_digital_in(9) == False:\n";
    cmd_str += "\t\t\tzscale = (get_analog_in(2)-0.026)/2.976\n";
    cmd_str += "\t\t\tzangle = zscale*1.57079633-0.087266462\n";
    cmd_str += "\t\t\tzwidth = 5+110*sin(zangle)\n";
    cmd_str += "\t\t\tmeasure_depth = cos(zangle)*finger_length\n";
    cmd_str += "\t\t\tcompensation_depth = (measure_depth - start_depth)\n";
    cmd_str += "\t\t\ttarget_pose = pose_trans(start_pose,p[0,0,-compensation_depth,0,0,0])\n";
    cmd_str += "\t\t\tif timeout > 400:\n";
    cmd_str += "\t\t\t\tbreak\n";
    cmd_str += "\t\t\tend\n";
    cmd_str += "\t\t\ttimeout=timeout+1\n";
    cmd_str += "\t\t\tservoj(get_inverse_kin(target_pose),0,0,0.008,0.033,1700)\n";
    cmd_str += "\t\tend\n";
    cmd_str += "\t\tnspeed = norm(get_actual_tcp_speed())\n";
    cmd_str += "\t\twhile nspeed > 0.001:\n";
    cmd_str += "\t\t\tservoj(get_inverse_kin(target_pose),0,0,0.008,0.033,1700)\n";
    cmd_str += "\t\t\tnspeed = norm(get_actual_tcp_speed())\n";
    cmd_str += "\t\tend\n";
    cmd_str += "\tend\n";
    cmd_str += "\tif depth_compensation==False:\n";
    cmd_str += "\t\ttimeout = 0\n";
    cmd_str += "\t\twhile get_digital_in(9) == True:\n";
    cmd_str += "\t\t\ttimeout = timeout+1\n";
    cmd_str += "\t\t\tsync()\n";
    cmd_str += "\t\t\tif timeout > 20:\n";
    cmd_str += "\t\t\t\tbreak\n";
    cmd_str += "\t\t\tend\n";
    cmd_str += "\t\tend\n";
    cmd_str += "\t\ttimeout = 0\n";
    cmd_str += "\t\twhile get_digital_in(9) == False:\n";
    cmd_str += "\t\t\ttimeout = timeout+1\n";
    cmd_str += "\t\t\tsync()\n";
    cmd_str += "\t\t\tif timeout > 400:\n";
    cmd_str += "\t\t\t\tbreak\n";
    cmd_str += "\t\t\tend\n";
    cmd_str += "\t\tend\n";
    cmd_str += "\tend\n";
    cmd_str += "\tif set_payload1:\n";
    cmd_str += "\t\tif slave:\n";
    cmd_str += "\t\t\tif get_analog_in(3) < 2:\n";
    cmd_str += "\t\t\t\tzslam=0\n";
    cmd_str += "\t\t\telse:\n";
    cmd_str += "\t\t\t\tzslam=payload\n";
    cmd_str += "\t\t\tend\n";
    cmd_str += "\t\telse:\n";
    cmd_str += "\t\t\tif get_digital_in(8) == False:\n";
    cmd_str += "\t\t\t\tzmasm=0\n";
    cmd_str += "\t\t\telse:\n";
    cmd_str += "\t\t\t\tzmasm=payload\n";
    cmd_str += "\t\t\tend\n";
    cmd_str += "\t\tend\n";
    cmd_str += "\t\tzsysm=0.0\n";
    cmd_str += "\t\tzload=zmasm+zslam+zsysm\n";
    cmd_str += "\t\tset_payload(zload)\n";
    cmd_str += "\tend\n";
    cmd_str += "end\n\n";

    return cmd_str


def find_aruco(marker_size, blocking=False):
    # read camera intrinsic parameters
    fs = cv2.FileStorage("./intr.yml", cv2.FILE_STORAGE_READ)
    cam_mat = fs.getNode("camera_matrix").mat()
    # print "Camera matrix: {0}".format(cam_mat)

    # read data
    cv2.namedWindow('find_aruco')
    # img = cv2.imread('./aruco.png', cv2.IMREAD_GRAYSCALE)
    cap = cv2.VideoCapture(2)
    rvec, tvec, corners = None, None, None

    while True:
        ret, img = cap.read()

        aruco_dict = cv2.aruco.Dictionary_get(cv2.aruco.DICT_6X6_250)
        parameters = cv2.aruco.DetectorParameters_create()

        # lists of ids and the corners beloning to each id
        corners, ids, rejected = cv2.aruco.detectMarkers(img, aruco_dict, parameters=parameters)
        if len(corners) > 0:
            img = cv2.aruco.drawDetectedMarkers(img, corners, ids, borderColor=(0, 0, 255))
            distCoeffs = None
            rvec, tvec, _ = cv2.aruco.estimatePoseSingleMarkers(corners, marker_size, cam_mat, distCoeffs)

            if rvec is not None and tvec is not None:
                cv2.aruco.drawAxis(img, cam_mat, distCoeffs, rvec, tvec, 0.1)

        cv2.imshow('find_aruco', img)
        k = cv2.waitKey(1)

        if k == ord('q'):
            if not blocking:
                cv2.destroyAllWindows()
            break

    return tvec, rvec, corners, cam_mat
