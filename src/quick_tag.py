#!/usr/bin/env python
"""!

Using formulas from http://www.epixea.com/research/multi-view-coding-thesisse8.html

"""

import sys, json
import csv

from read_logs import *
from camera_projection import *

# Which way forward is in the image
CAMERA_DIR = "bottom"

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

    output_list = []
    # Convert relevant parts of the reference reading
    for key in ["lat", "lon"]:
        mavlink_ref[key] = float(mavlink_ref[key]) / 1e7
    mavlink_ref["relative_alt"] = float(mavlink_ref["relative_alt"])

    with open("output.csv", "ab") as writecsv:
        mywriter = csv.writer(writecsv, delimiter=",")
        for i in range(len(mavlink_data["mavlink_global_position_int_t"])):
            image = annotated_img[i]['filename']
            # Latitude is degrees * 1e7
            lat = float(gps_data[i]["lat"])
            lon = float(gps_data[i]["lon"])
            alt = float(mavlink_data["mavlink_global_position_int_t"][i]["relative_alt"])

            z = (alt - mavlink_ref["relative_alt"]) / 1e3

            print "Alt = ", z

            roll = float(mavlink_data["mavlink_attitude_t"][i]["roll"])
            pitch = float(mavlink_data["mavlink_attitude_t"][i]["pitch"])
            yaw = float(mavlink_data["mavlink_attitude_t"][i]["yaw"])

            # Construct pixel information

            for px in annotated_img[i]['annotations']:
                goosespecies = px['class']

                u = float(px["x"])
                v = float(px["y"])

                px_x, px_y = pixel_to_camera(u,v, CAMERA_DIR)
                offset = numpy.squeeze(numpy.asarray(dead_simple_offset(px_x, px_y, yaw, z)))
                geolon, geolat = convert_m_to_lat_lon(offset[0], offset[1], lat, lon)

                print image, geolon, geolat
                mywriter.writerow([image, geolon, geolat, int(px["x"]), int(px["y"])])
