#!/usr/bin/env python
"""!

Using formulas from http://www.epixea.com/research/multi-view-coding-thesisse8.html

"""

import sys, json
import csv
from nest_check import lat_lon_closeness

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
        mavlink_ref[key] = long(mavlink_ref[key]) / 1e7
    mavlink_ref["relative_alt"] = float(mavlink_ref["relative_alt"])

    coordinate_dict = {}
    with open("output.csv", "wb") as writecsv:
        mywriter = csv.writer(writecsv, delimiter=",")

        coordinate_dict = {}
        duplicates_dict = {}

        for i in range(len(mavlink_data["mavlink_global_position_int_t"])):
            image = annotated_img[i]['filename']
            # Latitude is degrees * 1e7
            lat = float(gps_data[i]["lat"])
            lon = float(gps_data[i]["lon"])
            #lat = mavlink_data["mavlink_global_position_int_t][i]["lat"] / 1e7
            #lon = mavlink_data["mavlink_global_position_int_t][i]["lon"] / 1e7
            
            alt = float(mavlink_data["mavlink_global_position_int_t"][i]["relative_alt"])
            z = (alt - mavlink_ref["relative_alt"]) / 1e3

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

                d_lat = geolat - mavlink_ref["lat"]
                d_lon = geolon - mavlink_ref["lon"]

                dxy = convert_lat_lon_to_m(d_lat, d_lon, lat)

                current_point = {'img': image, 'lon': geolon, 'lat': geolat, 'dxy': dxy}
                if not goosespecies in coordinate_dict:
                    coordinate_dict[goosespecies] = [current_point]
                else:
                    close_to_another_point = False
                    for k in coordinate_dict[goosespecies]:
                        if lat_lon_closeness(current_point, k):
                            close_to_another_point = True
                            if goosespecies not in duplicates_dict:
                                duplicates_dict[goosespecies] = [current_point]
                            else:
                                duplicates_dict[goosespecies].append(current_point)
                            break

                    if close_to_another_point == False:
                        coordinate_dict[goosespecies].append(current_point)
                    else:
                        # Skip
                        continue

                mywriter.writerow([goosespecies, image, geolon, geolat, dxy[0], dxy[1]])
        
        # Process duplicates
        for species in duplicates_dict:
            if species == "Nest" or species == "Group":
                continue

            for duplicate_point in duplicates_dict[species]:
                keep_point= False
                if "Nest" in coordinate_dict:
                    for k in coordinate_dict["Nest"]:
                        if lat_lon_closeness(k, duplicate_point):
                            keep_point = True
                            break
                if "Group" in coordinate_dict and keep_point == False:
                    for k in coordinate_dict["Group"]:
                        if lat_lon_closeness(k, duplicate_point):
                            keep_point = True
                            break

                if keep_point == True:
                    mywriter.writerow([species, duplicate_point["img"], duplicate_point["lon"], duplicate_point["lat"], duplicate_point["dxy"][0], duplicate_point["dxy"][1]])
