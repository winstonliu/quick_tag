#!/usr/bin/env python
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
    mavlink_filter = [float(k['time']) for k in gps_data]
    mavlink_datatypes = ["mavlink_global_position_int_t", "mavlink_attitude_t"]
    mavlink_data, mavlink_ref = read_mavlink(sys.argv[2], mavlink_filter, mavlink_datatypes)

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

        d_lat = lat - mavlink_ref["lat"]
        d_lon = lon - mavlink_ref["lon"]
        z = (alt - mavlink_ref["relative_alt"]) / 1e3

        x, y = convert_lat_lon_to_m(d_lat, d_lon, lat)

        roll = float(mavlink_data["mavlink_attitude_t"][i]["roll"])
        pitch = float(mavlink_data["mavlink_attitude_t"][i]["pitch"])
        yaw = float(mavlink_data["mavlink_attitude_t"][i]["yaw"])

        R = construct_rotation_matrix(x, y, z, yaw, pitch, roll)

        # Construct pixel information

        for px in annotated_img[i]['annotations']:
            goosespecies = px['class']

            u = float(px["x"])
            v = float(px["y"])

            px_x, px_y = pixel_to_camera_frame(u,v, CAMERA_DIR)
            xy = numpy.matrix([[px_x],[px_y],[1]])

            raw_result = numpy.squeeze(numpy.asarray(world_coordinate_calculation(xy, R)))

            geox = x + raw_result[0]
            geoy = y + raw_result[1]

            geolat, geolon = convert_m_to_lat_lon(geox, geoy, lat, lon)

            print image, geolon, geolat
