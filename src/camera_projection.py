#!/usr/bin/env python
import numpy
import math

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

def convert_lat_lon_to_m(d_lat, d_lon):
    # Convert lon to m, assuming lat lon in deg, alt in m
    # Using small angle theorem (assume a flat earth)
    DIST_AT_EQ =  111321
    lon_m = d_lon * math.cos(lat) * DIST_AT_EQ
    lat_m = d_lat * DIST_AT_EQ

    return (lon_m, lat_m)

def construct_rotation_matrix(x, y, z, yaw, pitch, roll):
    pass

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

def world_coordinate_calculation(uv, R):
    """  
        Q = K*R
        
        Where K is the 3x4 camera intrinsic matrix, and R is the 4x4 rotation matrix

        Forward projection is:

            [u,v,1]^T = K x R x P = Q x P

        So we should be able to do:

            Q' x [u,v,1]^T = P
    """

    return (K*R).I * uv
