#!/usr/bin/env python
import math
import camera_projection as cp

def check_for_closeness(coord_dict, nest_list, threshold):
    return_list = []
    min_closeness = 1000
    for k in coord_dict:
        if lat_lon_closeness(coord_dict, k["pos"]) < min_closeness:
            min_closeness = lat_lon_closeness(coord_dict, k["pos"]) 
    return min_closeness 

def lat_lon_closeness(coord_1, coord_2):
    latdist = coord_1["lat"] - coord_2["lat"]
    londist = coord_1["lon"] - coord_2["lon"]

    x,y = convert_m_to_lat_lon(latdist, londist, coord_1["lat"])

    return math.sqrt(math.pow(x,2) + math.pow(y,2))
