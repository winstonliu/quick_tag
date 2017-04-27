#!/usr/bin/env python
"""!

Using formulas from http://www.epixea.com/research/multi-view-coding-thesisse8.html

"""

import sys, json

from read_logs import *
from camera_projection import *

# Which way forward is in the image
CAMERA_DIR = "bottom"

# 130 in Alma
ALTITUDE_CORRECTION = 172

def get_interesting_images(sloth_data):
    # List of annotated image
    return [d for d in sloth_data if d['annotations'] != []]

if __name__=="__main__":
    if len(sys.argv) != 4:
        sys.exit("ERROR: input must be in the form [CAMERA GPS LOG] [TLOG CSV FILE] [SLOTH JSON FILE]")

    sloth_data = json.loads(read_as_string(sys.argv[3]))

    # The only images we are interested in are the annotated ones
    annotated_img = get_interesting_images(sloth_data)
    # Use the filenames as a filter for reading GPS logs
    filter_list = [k['filename'] for k in annotated_img]
    gps_data = read_gps_log(sys.argv[1], filter_list)

    # Filter for interesting mavlink messages
    mavlink_filter = [k['time'] for k in gps_data]
    mavlink_datatypes = ["mavlink_global_position_int_t", "mavlink_attitude_t"]
    mavlink_data, mavlink_ref = read_mavlink(sys.argv[2], mavlink_filter, mavlink_datatypes)

    print mavlink_filter
    for k in mavlink_data["mavlink_global_position_int_t"]:
        print k["time"]

    output_list = []
    # Convert relevant parts of the reference reading
    for key in ["lat", "lon"]:
        mavlink_ref[key] = float(mavlink_ref[key]) / 1e7
    mavlink_ref["relative_alt"] = float(mavlink_ref["relative_alt"])

    for i in range(len(mavlink_data["mavlink_global_position_int_t"])):
        image = annotated_img[i]['filename']
        # Latitude is degrees * 1e7
        lat = float(mavlink_data["mavlink_global_position_int_t"][i]["lat"]) / 1e7
        lon = float(mavlink_data["mavlink_global_position_int_t"][i]["lon"]) / 1e7
        alt = float(mavlink_data["mavlink_global_position_int_t"][i]["relative_alt"])

        print "Lat Lon Alt = ", lat, lon, alt
        print gps_data[i]["time"]
        print mavlink_data["mavlink_global_position_int_t"][i]["time"]

        d_lat = lat - mavlink_ref["lat"]
        d_lon = lon - mavlink_ref["lon"]
        z = (alt - mavlink_ref["relative_alt"]) / 1e3

        x, y = convert_lat_lon_to_m(d_lat, d_lon, lat)

        roll = float(mavlink_data["mavlink_attitude_t"][i]["roll"])
        pitch = float(mavlink_data["mavlink_attitude_t"][i]["pitch"])
        yaw = float(mavlink_data["mavlink_attitude_t"][i]["yaw"])

        C_plane = numpy.array([x,y,z])

        print "X Y Z = ", x, y, z

        # Taking the back propogation path (world to camera)
        # Global frame xyz = East North Up ie facing east
        T_world_to_position = construct_rotation_matrix(x,y,z, 0, 0, 0)
        # Local reference frame is xyz = North West Up
        R_position_to_local = construct_rotation_matrix(0, 0, 0, math.radians(-90), 0, 0)
        R_local_to_plane = construct_rotation_matrix(0, 0, 0, yaw, pitch, roll)
        R_plane_to_camera = world_to_camera_frame()

        # From world to camera, it's already inverted, don't need to invert anymore
        R_inv = T_world_to_position * R_position_to_local * R_local_to_plane * R_plane_to_camera

        # Construct pixel information

        for px in annotated_img[i]['annotations']:
            goosespecies = px['class']

            u = float(px["x"])
            v = float(px["y"])

            px_x, px_y = pixel_to_camera(u,v, CAMERA_DIR)
            xy = numpy.matrix([[px_x],[px_y],[1]])

            raw_result = numpy.squeeze(numpy.asarray(world_coordinate_calculation(xy, R_inv)))
            # Calculate scaling factor (lambda = (Z - Cz) / p3 on pg 6
            scaling_factor = -1 * C_plane[2] / raw_result[2]

            geox = x + scaling_factor * raw_result[0]
            geoy = y + scaling_factor * raw_result[1]
            geoz = z + scaling_factor * raw_result[2]

            geolon, geolat = convert_m_to_lat_lon(geox, geoy, lat, lon)

            print image, geolon, geolat
