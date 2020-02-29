#!/usr/bin/env python

from struct import *
import time

from ..adapter import *
from ..utils import *


class Ur3(Adapter):

    def __init__(self, ip, port_write, port_read):
        """
        Connects the UR3 robot.
        :param ip: IP of a robot.
        :param port_read: Port for reading data from robot.
        :param port_write: Port for writing data to robot.
        """
        Adapter.__init__(self, ip, port_read, port_write)
        self.chunk_size = 8
        self.num_chunks = 6
        self.start_chunk_cartesian = 444
        self.start_chunk_joint = 252
        self.stop_chunk_cartesian = self.start_chunk_cartesian + self.num_chunks * self.chunk_size
        self.stop_chunk_joint = self.start_chunk_joint + self.num_chunks * self.chunk_size
        self.ur_package_size = 1060
        self.vec = None

    @robot_command
    def get_pose(self):
        """
        Returns a pose of a connected robot.
        :return: np.array with 6 elements: [x, y, z, a, b, c]
        """
        # read package from UR3 -> 1060 bytes as list()
        msg_byte = list(self.socket_read.recv(self.ur_package_size))

        # crop data - pick only XYZABC values from package
        pose = self.get_data_from_ur3_package(msg_byte, self.start_chunk_cartesian, self.stop_chunk_cartesian,
                                              self.num_chunks, self.chunk_size)

        return np.asarray(pose)

    @robot_command
    def get_joints(self, deg=False):
        """
        Returns joint coordinates of a connected robot.
        :return: np.array with 6 elements [j1, j2, j3, j4, j5, j6]
        """
        # read package from UR3 -> 1060 bytes as list()
        msg_byte = list(self.socket_read.recv(self.ur_package_size))

        # crop data - pick only XYZABC values from package
        joints = self.get_data_from_ur3_package(msg_byte, self.start_chunk_joint, self.stop_chunk_joint,
                                                self.num_chunks, self.chunk_size)

        if deg:
            joints = [np.rad2deg(joint) for joint in joints]

        return np.asarray(joints)

    @robot_command
    def move(self, trajectory, is_movej=True, is_pose=True, a=1, v=1, use_mapping=False):
        """
        Moves a connected robot.
        :param trajectory: list of poses/joint coordinates.
        :param is_movej: bool
        :param is_pose: bool
        :param a: acceleration
        :param v: velocity
        :param use_mapping: bool. Specify if you want to set points in the external coordinate system (see set_mapping(..))
        :return: void
        """
        assert isinstance(trajectory, list)
        assert len(trajectory) > 0
        assert isinstance(is_movej, bool)
        assert isinstance(is_pose, bool)
        assert isinstance(trajectory[0], np.ndarray)
        assert trajectory[0].size == 6

        # if user provides coordinates expressed not in robot system transform them to proper system
        if use_mapping:
            assert self.coordinates_mapping is not None
            assert self.coordinates_mapping.shape == (4, 4)

        print ("Trajectory has {0} target points".format(len(trajectory)) )
        for i, point in enumerate(trajectory):

            command = ""

            if is_movej:
                command += "movej("
            else:
                command += "movel("

            if is_pose:
                command += "p"

            if use_mapping and is_pose:
                point = mat2pose(np.linalg.inv(self.coordinates_mapping).dot(pose2mat(point)))

            print (point)
            command += "[{}, {}, {}, {}, {}, {}], ".format(*point)
            command += "a={0},v={1}".format(a, v)
            command += ")\n"

            self.socket_write.send(command)
            self.wait_for_move_end(point, is_pose)
            print ("Achieved {0} target points".format(i))

    def wait_for_move_end(self, target_position, is_pose):
        start_time = time.time()
        while True:
            is_in_position = True
            if is_pose:
                current_position = self.get_pose()
            else:
                current_position = self.get_joints()

            for i, el in enumerate(target_position):
                if (target_position[i] < current_position[i] - 0.07) or (
                        target_position[i] > current_position[i] + 0.07):
                    is_in_position = False
            elapsed_time = time.time() - start_time
            if is_in_position or elapsed_time > 5:
                break

    @robot_command
    def grip(self, range_open):
        """
        Sends command to open the RG6 gripper.
        :param range_open: number in [cm]
        :return: void
        """
        assert isinstance(range_open, float) or isinstance(range_open, int)
        command = rg6_cmd(range_open)
        self.socket_write.send(command)

    def get_data_from_ur3_package(self, msg, start_byte, stop_byte, num_chunks, chunk_size):
        values_bytes = msg[start_byte:stop_byte]
        values = list()
        for i in range(num_chunks):
            m = chunk_size * i

            # byte string containing 8-byte double number
            value = b''
            for k in range(chunk_size, 0, -1):
                idx = (k - 1) + m
                byte = values_bytes[idx]
                print(type(byte))
                value += byte

            values.append(unpack('d', value)[0])
        return values
