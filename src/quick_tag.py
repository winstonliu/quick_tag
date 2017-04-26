#!/usr/bin/env python
import sys, json

from read_logs import *

# Where forward is in the image
CAMERA_FWD = "bottom"

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

    print mavlink_ref
