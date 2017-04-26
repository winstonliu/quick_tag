#!/usr/bin/env python
import numpy
import math

from transformations import euler_matrix

# x is North-South, y is East-West

# Parameters

max_x = 4096
max_y = 3072

# Units in pixels
Ox = 2048
Oy = 1536

# Pixel ratio (px/m)
mxy = 1 / 6e-6
# Focal length (m)
f = 35e-3

# Camera matrix K (3x4)
K = numpy.matrix(
       [[ f*mxy, 0    , Ox , 0],
        [ 0    , f*mxy, Oy , 0],
        [ 0    , 0    , 1  , 0]])

DIST_AT_EQUATOR =  111321
def convert_lat_lon_to_m(d_lat, d_lon, original_lat):
    # Convert lon to m, assuming lat lon in deg, alt in m
    # Using small angle theorem (assume a flat earth)
    x = d_lat * DIST_AT_EQUATOR
    y = d_lon * math.cos(original_lat) * DIST_AT_EQUATOR

    return (x, y)

def convert_m_to_lat_lon(x,y, original_lon, original_lat):
    lat = x / DIST_AT_EQUATOR + original_lat
    lon = y / (DIST_AT_EQUATOR * math.cos(lat)) + original_lon

    return (lat, lon)

def construct_rotation_matrix(x, y, z, yaw, pitch, roll):
    rotation_mat = euler_matrix(roll, pitch, yaw)
    # set x,y,z
    rotation_mat[0][3] = x
    rotation_mat[1][3] = y
    rotation_mat[2][3] = z

    return numpy.asmatrix(rotation_mat)

def pixel_to_camera_frame(pixel_x, pixel_y, CAMERA_DIR):
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

def world_coordinate_calculation(xy, R):
    """  
        xy is in camera frame

        Q = K*R
        
        Where K is the 3x4 camera intrinsic matrix, and R is the 4x4 rotation matrix

        Forward projection is:

            [u,v,1]^T = K x R x P = Q x P

        So we should be able to do:

            Q' x [u,v,1]^T = P
    """
    return R.I * K.I * xy
