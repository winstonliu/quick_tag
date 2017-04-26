#!/usr/bin/env python
import time
import csv
import numpy

def gps_to_dict(img_tag, lat, lon, alt, heading, time):
    return {
            'img': img_tag,
            'pos': numpy.array([lat, lon]),
            'alt': alt,
            'heading ': heading,
            'time': time
        } 

def mav_to_dict(rowinfo):
    data =  {'time': rowinfo[0]}

    keyname = None
    for elem in rowinfo[10:]:
        if keyname == None:
            keyname = elem else:
            data[keyname] = elem
            keyname = None

    return data


def read_as_string(filename):
    """! Output file contents as string """

    data = ""
    with open(filename, 'r') as strfile:
        data = strfile.read().replace('\n', '')

    return data


def read_gps_log(filename, filter_list):
    """! Read from GPS log """
    output_list = list()
    idx = 0
    with open(filename, 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=",")
        for row in csvreader:
            # Take advantage of the fact that filter_list is ordered
            if row[0] == filter_list[idx]:
                output_list.append(gps_to_dict(*row))
                idx += 1

                if idx == len(filter_list): break

    return output_list                

def read_mavlink(filename, filter_times=[], filter_types=[]):
    """! Read in CSV files and return list of contents. """
    output_list = {'mavlink_global_position_int_t' : [], 'mavlink_attitude_t' : [] }
    idx = 0
    with open(filename, 'rb') as csvfile:
        cr = csv.reader(csvfile, delimiter=",")

        # Do some initial checks to make sure the filtered times are ok

        for r in cr:
            # Item 10 is the mavlink type
            if not r[9] in filter_types:
                continue

            r[0] = convert_mav_time_to_epoch(r[0])

            if r[0] > filter_times[idx]:
                output_list[r[9]].append(mav_to_dict(r))
                idx += 1

                if idx == len(filter_times): break

    return output_list

def convert_mav_time_to_epoch(mav_time):
    pattern = "%Y-%m-%dT%H:%M:%S.%f"
    return time.mktime(time.strptime(mav_time, pattern))
