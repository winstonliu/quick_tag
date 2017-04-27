#!/usr/bin/env python
import numpy
import math

from transformations import euler_matrix

# y is North-South, x is East-West
# Using right handed axis facing east

# Parameters

max_x = 4096
max_y = 3072

# Units in pixels
Ox = 2048
Oy = 1536

# Pixel ratio (px/m)
px_size = 6e-6
mxy = 1 / px_size
# Focal length (m)
f = 35e-3

# Camera matrix K (3x4)
K = numpy.matrix(
       [[ f*mxy, 0    , Ox , 0],
        [ 0    , f*mxy, Oy , 0],
        [ 0    , 0    , 1  , 0]])

def dead_simple_offset(camera_x, camera_y, yaw, alt):
    x_m, y_m = calculate_pixel_offset(camera_x, camera_y, alt)
    print x_m, y_m

    # Sketchy frame switching
    point_mat = numpy.matrix([[x_m, y_m, 0, 0]])

    rotation_mat = euler_matrix(0,0,yaw)

    return point_mat * camera_to_world_tf() * rotation_mat


def calculate_pixel_offset(x, y, altitude):
    width_x = 2 * altitude * Ox * px_size / f
    width_y = 2 * altitude * Oy * px_size / f
    
    x_m = x / float(max_x) * width_x
    y_m = y / float(max_y) * width_y

    return (x_m, y_m)

DIST_AT_EQUATOR =  111321
def convert_lat_lon_to_m(d_lat, d_lon, original_lat):
    # Convert lon to m, assuming lat lon in deg, alt in m
    # Using small angle theorem (assume a flat earth)
    y = d_lat * DIST_AT_EQUATOR
    x = d_lon * math.cos(original_lat) * DIST_AT_EQUATOR

    return (x, y)

def convert_m_to_lat_lon(x,y, original_lon, original_lat):
    lat = y / DIST_AT_EQUATOR + original_lat
    lon = x / (DIST_AT_EQUATOR * math.cos(lat)) + original_lon

    return (lon, lat)

def construct_rotation_matrix(x, y, z, yaw, pitch, roll):
    """
        Yaw from x
        Translation, then rotation
        Using fixed axis
    """
    # set x,y,z
    translation_mat = numpy.eye(4)
    translation_mat[0][3] = x
    translation_mat[1][3] = y
    translation_mat[2][3] = z

    rotation_mat = euler_matrix(roll, pitch, yaw, "sxyz")

    # Translation first, then rotation. Other way makes it a lot more confusing
    return numpy.asmatrix(translation_mat) * numpy.asmatrix(rotation_mat)

def pixel_to_camera(pixel_x, pixel_y, CAMERA_DIR):
    """ 
        camera_dir is one of "top" or "bottom"
    """

    camera_x = 0
    camera_y = 0

    if CAMERA_DIR == "bottom":
        camera_x = pixel_x - Ox
        camera_y = pixel_y - Oy
    elif CAMERA_DIR == "top":
        camera_x = Ox - pixel_x 
        camera_y = Oy - pixel_y

    return (camera_x, camera_y)

def world_to_camera_frame():
    """ Assuming y-axis in camera frame is towards the bottom of the image and pointing in the
        direction of travel.
        
    """

    roll = math.radians(180)
    yaw = math.radians(-90)

    # Apply rotation with rotating axis in order yaw, pitch, roll
    return numpy.asmatrix(euler_matrix(roll, 0, yaw, 'rzyx'))


def camera_to_world_tf():
    """ Assuming y-axis in camera frame is towards the bottom of the image and pointing in the
            direction of travel.
        
    """

    roll = math.radians(-180)
    yaw = math.radians(90)

    # Apply rotation with rotating axis in order roll, pitch, yaw
    return numpy.asmatrix(euler_matrix(roll, 0, yaw, 'rxyz'))


def world_coordinate_calculation(xy, R_inv):
    """  
        xy is in camera frame

        Q = K*R
        
        Where K is the 3x4 camera intrinsic matrix, and R is the 4x4 rotation matrix

        Forward projection is:

            [u,v,1]^T = K x R x P = Q x P

        So we should be able to do:

            Q' x [u,v,1]^T = P
    """
    return R_inv * K.I * xy
