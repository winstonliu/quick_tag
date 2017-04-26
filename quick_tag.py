#!/usr/bin/env python
import sys, csv, json
import numpy
import time

class MyGPS:
    def __init__(self, img_tag, lat, lon, alt, heading, time):
        self.img = img_tag
        self.pos = numpy.array([lat, lon])
        self.alt = alt
        self.heading = heading
        self.time = time
        
class MyMavPos:
    def __init__(self, clk_time, pos, attitude, alt, relative_alt, hdg):
        self.time = clk_time
        self.pos = numpy.array([lat, lon])
        self.alt = alt
        self.heading = hdg
        self.attitude = attitude

def read_gps_log(filename, filter_list):
    output_list = list()
    idx = 0
    with open(filename, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",")
        for row in csvreader:
            # Take advantage of the fact that filter_list is ordered
            if row[0] == filter_list[idx]:
                output_list.append(MyGPS(*row))
                idx += 1
            if idx == len(filter_list):
                break
    return output_list                

def convert_mav_time_to_epoch(mav_time):
    pattern = "%Y-%m-%dT%H:%M:%S.%f"
    return time.mktime(time.strptime(mav_time, pattern))

def get_interesting_images(sloth_data):
    # List of annotated image
    return [d for d in sloth_data if d['annotations'] != []]

def read_mavlink(filename, filter_items=[]):
    """! Read in CSV files and return list of contents. """
    output_list = list()
    with open(filename, 'rb') as csvfile:
        cr = csv.reader(csvfile, delimiter=",")
        for r in cr:
            if r[9] in filter_items:
                pattern = "%Y-%m-%dT%H:%M:%S.%f"
                r.append(time.mktime(time.strptime(r[0], pattern)))
                output_list.append(r)
    return output_list

def read_as_list(filename):
    """! Read in CSV files and return list of contents. """
    output_list = list()
    with open(filename, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",")

        for row in csvreader:
            output_list.append(row)

    return output_list

def read_as_string(filename):
    """! Output file contents as string """

    data = ""
    with open(filename, 'r') as strfile:
        data = strfile.read().replace('\n', '')

    return data

if __name__=="__main__":
    if len(sys.argv) != 4:
        sys.exit("ERROR: input must be in the form [CAMERA GPS LOG] [TLOG CSV FILE] [SLOTH JSON FILE]")

    sloth_data = json.loads(read_as_string(sys.argv[3]))

    # The only images we are interested in are the annotated ones
    annotated_img = get_interesting_images(sloth_data)
    filter_list = [k['filename'] for k in annotated_img]
    gps_data = read_gps_log(sys.argv[1], filter_list)
    mavlink_filter = [k.time for k in gps_data]
    mavlink_datatypes = ["mavlink_global_position_int_t", "mavlink_attitude_t"]

    print mavlink_data[0]

