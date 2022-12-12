from datetime import date, datetime, time, timedelta
import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
from geopy.geocoders import Nominatim
from pyzipcode import ZipCodeDatabase
import numpy as np
from django.core.exceptions import ObjectDoesNotExist

from carpool.models import Routes, CA_Zip, Candidates, Carpools

import mydatabase # custom module to interact with SQLite3 database

# A custom module to create carpools

# Initialize objects
geolocator = Nominatim(user_agent="carpool")
zcdb = ZipCodeDatabase() 

# Retrieve the drive network graph within the limits of the bounding box
#graph_path = 'carpool/static/carpool/box.graphml'
graph_path = 'media/box.graphml'

# Load the graph
box_graph = ox.load_graphml(graph_path)


# HELPER METHODS to create the carpool
# Methods to check user's role
def check_driver(stud):
    ''' Check student's role for driver or either. 
    Return: true or false '''

    if (stud['role'] == 'D' or stud['role'] == 'E') :
        return True
    else: # Student is a passenger
        return False
    
def check_passenger(stud):
    ''' Check student's role for passenger or either. 
    Return: true or false '''

    if (stud['role'] == 'P' or stud['role'] == 'E') :
        return True
    else : # Student is a driver
        return False

# Methods to check schedule constraint
# MODIF: check driver schedule 
def check_driver_schedule(stud):
    '''Check which days of the week the driver goes to campus'''

    schedule = ''
    # student goes to school if arrival and departure are not the same
    if stud['M_arr'] != stud['M_dep']: schedule += 'M'
    if stud['T_arr'] != stud['T_dep']: schedule += 'T'
    if stud['W_arr'] != stud['W_dep']: schedule += 'W'
    if stud['R_arr'] != stud['R_dep']: schedule += 'R'
    if stud['F_arr'] != stud['F_dep']: schedule += 'F'
    if stud['S_arr'] != stud['S_dep']: schedule += 'S'
    
    return schedule
        
         

# Arrival and Departure Schedule for all weekdays, group days, and individual weekdays
def check_schedule(stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for all weekdays are the same. 
    Return: true or false '''
   
    if check_schedule_M(stud_A, stud_B) and  check_schedule_T(stud_A, stud_B) and check_schedule_W(stud_A, stud_B) and check_schedule_R(stud_A, stud_B) and check_schedule_F(stud_A, stud_B) and check_schedule_S(stud_A, stud_B): 
        return True
    else : 
        return False


def check_schedule_MWF(stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for Mondays, Wednesdays, 
    and Fridays are the same. 
    Return: true or false '''
   
    if check_schedule_M(stud_A, stud_B) and check_schedule_W(stud_A, stud_B) and  check_schedule_F(stud_A, stud_B): 
        return True
    else : 
        return False


def check_schedule_TR (stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for Tuesdays 
    and Thursdays are the same. 
    Return: true or false '''

    if check_schedule_T(stud_A, stud_B) and check_schedule_R(stud_A, stud_B):
        return True
    else : 
        return False

def time_plus(time, timedelta):
    '''Add a time delta to time object. Do not cross midnight!'''
    # source: https://stackoverflow.com/questions/12448592/how-to-add-delta-to-python-datetime-time
    start = datetime( 2000, 1, 1,
        hour=time.hour, minute=time.minute, second=time.second)
    end = start + timedelta
    return end.time()

def check_arr_dep_delta(arrival_time_A, departure_time_A, arrival_time_B, departure_time_B, max_delta):
    '''Check arrival and departure within max_delta range. Assume student A is the driver, and student B is the rider. 
    Allows to find matches for candidates that needs to arrive in school after driver,
    and that finishes classes before driver. Driver never waits, only passenger.'''

    arrival = False
    departure = False

    #range(start, stop, step)
    max_delta += 5 # because stop is not included in range
    delta_lst = list(range(0,max_delta, 5))

    for d in delta_lst:
        delta = timedelta(minutes=d)
        arr = time_plus(arrival_time_A, delta) 
        dep = time_plus(departure_time_B, delta)
        # print('arrival' , arr, 'departure', dep)

        if arr ==  arrival_time_B: 
            # print('arr found')
            arrival = True 
        if departure_time_A == dep:
            # print('dep found')
            departure = True 
    
    # print('check_arr_dep_delta function')
    return arrival, departure


def check_schedule_S (stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for Saturday are the same. 
    Return: true or false '''

    arrival, departure = check_arr_dep_delta(stud_A['S_arr'],stud_A['S_dep'], stud_B['S_arr'], stud_B['S_dep'], 30)

    if (arrival) and (departure):
        # print('saturday match')
    # if (stud_A['S_arr'] == stud_B['S_arr'] and stud_A['S_dep'] == stud_B['S_dep'] ) :
        return True
    else : 
        return False


def check_schedule_M (stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for Monday are the same. 
    Return: true or false '''

    arrival, departure = check_arr_dep_delta(stud_A['M_arr'],stud_A['M_dep'], stud_B['M_arr'], stud_B['M_dep'], 30)

    if (arrival) and (departure):
        # print('monday match')
    # if (stud_A['M_arr'] == stud_B['M_arr'] and stud_A['M_dep'] == stud_B['M_dep'] ) :
        return True
    else : 
        return False


def check_schedule_T (stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for Tuesday are the same. 
    Return: true or false '''

    arrival, departure = check_arr_dep_delta(stud_A['T_arr'],stud_A['T_dep'], stud_B['T_arr'], stud_B['T_dep'], 30)

    if (arrival) and (departure):
        # print('tuesday match')
    # if (stud_A['T_arr'] == stud_B['T_arr'] and stud_A['T_dep'] == stud_B['T_dep'] ) :
        return True
    else : 
        return False


def check_schedule_W (stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for Wednesday are the same. 
    Return: true or false '''

    arrival, departure = check_arr_dep_delta(stud_A['W_arr'],stud_A['W_dep'], stud_B['W_arr'], stud_B['W_dep'], 30)


    if (arrival) and (departure):
        # print('wednesday match')
    # if (stud_A['W_arr'] == stud_B['W_arr'] and stud_A['W_dep'] == stud_B['W_dep'] ) :
        return True
    else : 
        return False


def check_schedule_R (stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for Thursday are the same. 
    Return: true or false '''

    arrival, departure = check_arr_dep_delta(stud_A['R_arr'],stud_A['R_dep'], stud_B['R_arr'], stud_B['R_dep'], 30)

    if (arrival) and (departure):
        # print('thrusday match')
    # if (stud_A['R_arr'] == stud_B['R_arr'] and stud_A['R_dep'] == stud_B['R_dep'] ) :
        return True
    else : 
        return False


def check_schedule_F (stud_A, stud_B):
    ''' Check if stud_A and stud_B arrival and departure time for Friday are the same. 
    Return: true or false '''

    arrival, departure = check_arr_dep_delta(stud_A['F_arr'],stud_A['F_dep'], stud_B['F_arr'], stud_B['F_dep'], 30)

    if (arrival) and (departure):
        # print('friday match')
    # if (stud_A['F_arr'] == stud_B['F_arr'] and stud_A['F_dep'] == stud_B['F_dep'] ) :
        return True
    else : 
        return False
    
# Methods to check compatibility
def check_same_gender (stud_A, stud_B):
    ''' Check if student A and student B are of the same gender. 
    Return: true or false '''

    if (stud_A['gender'] == stud_B['gender'] ):
        return True
    else : 
        return False


def check_same_college (stud_A, stud_B):
    ''' Check if student A and student B are of the same college. 
    Return: true or false '''

    if (stud_A['college'] == stud_B['college'] ):
        return True
    else : 
        return False


def check_same_age_group(stud_A, stud_B):
    ''' Check if student A and student B are of the same age group. 
    Return: true or false '''

    if (stud_A['under_25'] == stud_B['under_25'] ):
        return True
    else : 
        return False


def check_same_level (stud_A, stud_B) :
    ''' Check if student A and student B are of the same level.
    Undergrad == True if ['Senior', 'Junior','Sophomore','Freshman']
    Undergrad == False if ['Graduate', 'Post-Bacc']
    Return: true or false '''

    if (stud_A['undergrad'] == stud_B['undergrad'] ):
        return True
    else : 
        return False  


def check_smoker (stud_A, stud_B):
    ''' Check if student A and student B are of both smokers or both non_smokers. 
    Return: true or false '''

    if stud_A['smoker'] == stud_B['smoker'] :
        return True
    else : 
        return False        
    
# Method to compute compatibility score
def comp_score(stud_A, stud_B, factor=2):
    ''' Compute the compatibility score between two ride-mates
    Parameters: stud_A and stud_B = potential ride-mates, 
                factor = weight for preferences (default value is 2)
        Base value:    1     for feature with same characteristic
                       0     for feature with different characteristic but not choosen as preference
                      -1     for feature with different characteristics and choosen as preference
        Factor:        1     for no preference
                'factor'  weight for selected feature preference   
    Return score: the sum of the base value of each feature multiplied by students' preference factor 
    '''

    # factor must be between 2 and 5
    if factor <= 1: factor = 2     # Score range = [-17, 17]
    if factor > 5: factor = 5      # Score range = [-101, 101]
    
    # Default base values, assume no characteristic matches
    base_age = base_gender = base_level = base_smoker = base_college = 0
    # Default factor values, assume student A has no preferences
    factor_age_A = factor_gender_A = factor_level_A = factor_nonsmoker_A = 1
    # Default factor values, assume student B has no preferences
    factor_age_B = factor_gender_B = factor_level_B = factor_nonsmoker_B = 1
 
    # If any feature is selected as prefence by any student, update base value for -1 
    # Update factor value for stud_A preferences
    if (stud_A['pref_age']): 
        base_age = -1
        factor_age_A = factor
    if (stud_A['pref_gender']): 
        base_gender = -1
        factor_gender_A = factor
    if (stud_A['pref_status']): 
        base_level = -1
        factor_level_A = factor
    if (stud_A['pref_nonsmoker']): 
        base_smoker = -1   
        factor_nonsmoker_A = factor

    # Update factor value for stud_B preferences
    if (stud_B['pref_age']): 
        base_age = -1
        factor_age_B = factor
    if (stud_B['pref_gender']): 
        base_gender = -1
        factor_gender_B = factor
    if (stud_B['pref_status']): 
        base_level = -1
        factor_level_B = factor
    if (stud_B['pref_nonsmoker']): 
        base_smoker = -1
        factor_nonsmoker_B = factor

    # Update base values when feature matches to 1
    if (check_same_age_group(stud_A, stud_B)) : base_age = 1
    if (check_same_gender(stud_A, stud_B))    : base_gender = 1
    if (check_same_level(stud_A, stud_B))     : base_level = 1 
    if (check_smoker(stud_A, stud_B))         : base_smoker = 1
    if (check_same_college(stud_A, stud_B))   : base_college = 1

    # Compute weighted values
    w_age = (factor_age_A * factor_age_B * base_age)
    w_gender = (factor_gender_A * factor_gender_B *base_gender)
    w_status = (factor_level_A * factor_level_B * base_level)
    w_NSmoker= (factor_nonsmoker_A * factor_nonsmoker_B * base_smoker)

    # final score = sum(weighted values) + base_college
    final_score = w_age + w_gender + w_status + w_NSmoker + base_college
    
    return final_score

# Method to find route from location to campus when it's not saved in the database
def shortest_route_to_csusm(graph, origin_lat, origin_lng):
    ''' Get a list with intermediary nodes of a route from origin to CSUSM
    Parameters: origin_lat: the y(latitude) coordinate
                origin_lng: the x(longitude) coordinate
                graph: the base network to find the route
    Return: a list of the shortest route by distance 
            a list of the shortest route by time
            travel time as a string
            total distance of the route in miles
    '''
    # destination's X_longitude, Y_latitude 
    csusm = {'x': -117.1587, 'y': 33.1298}   
    # In the graph, get the nodes closest to the points
    destination_node = ox.distance.nearest_nodes(graph, X= csusm.get('x'), Y= csusm.get('y'))

    x = origin_lng # x(longitude)
    y = origin_lat # y(latitude)
    # In the graph, get the nodes closest to the points
    origin_node = ox.distance.nearest_nodes(graph, X= x, Y= y,)
    
    # Get the shortest route by distance and by time from origin to destination
    shortest_route_by_distance = ox.shortest_path(graph, origin_node, destination_node, weight='length')
    shortest_route_by_travel_time = ox.shortest_path(graph, origin_node, destination_node, weight='travel_time')

    # Get the travel time, in seconds
    # use "nx" (networkx), not "ox" (osmnx)
    try:
        travel_time_in_seconds = nx.shortest_path_length(graph, origin_node, destination_node, weight='travel_time')       
        # The travel time in "HOURS:MINUTES:SECONDS" format
        travel_time_str = str(timedelta(seconds=travel_time_in_seconds))
    except nx.NetworkXNoPath:
        travel_time_str= '00:00:00'
        pass
        
    # Get the distance in meters
    try:
        distance_in_meters = nx.shortest_path_length(graph, origin_node, destination_node, weight='length')
        # Distance in kilometers and miles
        distance_in_kilometers = distance_in_meters / 1000
        distance_in_miles = distance_in_kilometers * 0.62137
    except nx.NetworkXNoPath:
        distance_in_miles = 0
        pass

    return shortest_route_by_distance, shortest_route_by_travel_time, travel_time_str, distance_in_miles

# convert string into list (helper function for the next function)
def convert_to_list(string):
    ''' Receives a list in a string format and converts it back to a list'''
    lst = list(string.split(","))
    first = lst[0]
    last = lst[-1]

    if (first[0] == '['): 
        first = first[1:]
        lst[0] = first
    if (last[-1] == ']'): 
        last = last[:-1] 
        lst[-1] = last

    return lst


def find_zips_on_route(graph, route):
    ''' Retrieve coordinates from nodes on the route, then find zip codes for each coord
        Return: set of zip codes on the route
    '''
    route_lst=[]
    if (type(route) == str):
        route_lst = convert_to_list(route) #convert from str to list
    else:
        route_lst = route

    path_coordinates = []

    for node in route_lst:
        node = int(node) #make sure the node is a number

        # get node attributes in the Graph using
        lat = graph.nodes[node]['y']
        lng = graph.nodes[node]['x']        
        path_coordinates.append((lat,lng))

    # create a list zip codes on the route (whe need to preserve the order)
    path_zip_codes = []

    for coord in path_coordinates:
        try:
            location = geolocator.reverse(coord)
            path_zip_codes.append(location.raw['address']['postcode'])
        except:
            pass

    # keep only unique values into the list
    path_zip_codes = list(dict.fromkeys(path_zip_codes)) 

    return path_zip_codes


# Methods to CREATE the carpool
def select_driver(df):
    ''' Select a driver from the pool df
    Return: driver's index and driver dict'''

    d_ind = None
    driver = None

    while True:
        d_ind = df.sample(1).index
        driver = df.loc[d_ind].to_dict(orient='index')
        
        d_ind = list(driver.keys()) 
        d_ind = d_ind[0]

        if check_driver(driver[d_ind]): 
            break

    #d_ind = list(driver.keys())
    #d_ind = d_ind[0]

    # print('Select_driver:', type(driver), driver[d_ind])

    return d_ind, driver[d_ind]


def remove_from_pool(remove_lst, df):
    ''' Remove students from pool
    Parameters: remove_lst: list of indices of students to be removed from df
                df: pool of students dataframe '''
    for cand in remove_lst:
        try:
            df.drop(index= [cand], axis=0, inplace=True)
        except KeyError:
            pass


def create_carpool_dict(driver, carpool_id):
    ''' Create a carpool dict based on driver's information 
        Return: carpool dict with values for driver ID, and vacant seats, waiting for candidates' information'''
    
    # MODIF: added driver schedule into dict
    # carpool = {'driver': driver['id'], 'vacant_seats': driver['seats'], 'candidates': {} }
    carpool = {'carpool_id': carpool_id, 'driver': driver['id'], 'driver_schedule': check_driver_schedule(driver) , 'vacant_seats': driver['seats'], 'candidates': {} } 
    
    return carpool



def get_route(origin):
    ''' Get driver's route from the origin zip code 
        Return a list with the zip codes that the route crosses '''
    
    route_lst = []
    try:
        # Get route from origin in the database
        route_lst = Routes.objects.values_list('zips_on_route', flat=True).get(pk=origin)

        # if len(route_lst) == 1:
        #     #only one element in list
        #     route_lst = route_lst[0]

        if type(route_lst) == str:
           #list is a sring
            zip = ''      #empty string
            zip_lst = []  # empty list 

            for char in route_lst:
                if (char.isdigit()):
                    zip += char
                if len(zip) == 5:
                    zip_lst.append(zip)
                    zip = ''       
            route_lst = zip_lst
    except  ObjectDoesNotExist:
        if len(route_lst) == 0:
            # Find the shortest path to campus
            print('Route from', origin, 'not found on database, please wait...')
            start_time = datetime.now() # store the execution start time

            # Get zip code's coordinates in CA zip code dataset
            zip_coord = CA_Zip.objects.only('latitude','longitude').get(zip_code=origin)
            # print('zip_coord', type(zip_coord), zip_coord)
            lat = zip_coord.latitude
            lng = zip_coord.longitude

            # compute shortest routes by length/time and travel time/dist
            short_route_by_dist, short_route_by_time, travel_time, travel_dist = shortest_route_to_csusm(box_graph, lat, lng)

            # Fix string format for travel_time
            if len(travel_time) ==7 or len(travel_time) > 8 :
                travel_time = travel_time[:7].zfill(8)

            # find all zip codes on the shortest route by time
            zips_on_route = find_zips_on_route(box_graph, short_route_by_time)

            # save new route into the database
            new_route = {'origin_id': origin,
                            's_route_dist': short_route_by_dist,
                            's_route_time': short_route_by_time,
                            'travel_time': travel_time,
                            'travel_distance': travel_dist,
                            'zips_on_route':  zips_on_route
                            }
            Routes.objects.create(**new_route) 

            # save values into df
            #routes_df.at[index,'zips_route'] = zips_on_route

            end_time = datetime.now() # store execution end time
            elapsed_time = end_time - start_time 
            print("Route created in %.3f seconds" % elapsed_time.seconds)
            
            route_lst = zips_on_route
        # end of new route

    return route_lst



def find_zips_around(location, radius=5):
    ''' Using pyzipcode to search in its ZipCodeDatabase, 
    find all zip codes around this location within this radius
    Return: a list of zip codes'''
    zips_in_radius = []
    try:
        zips_in_radius = [z.zip for z in zcdb.get_zipcodes_around_radius(location, radius)] # ('ZIP', radius in miles)
        #radius_utf = [x.encode('UTF-8') for x in zips_in_radius] # unicode list to utf list
    
    except:
        zips_in_radius = [location]
    
    return zips_in_radius
    # source: https://stackoverflow.com/questions/35047031/could-i-use-python-to-retrieve-a-number-of-zip-code-within-a-radius


def find_candidates(df, zips_in_radius):
    ''' Look for candidates in the pool with zip code within a radius
    Return: candidates dictionary'''

    df['zip_code'] = df['zip_code'].apply(str) # make sure zip code is string

    # Find all students within this radius
    candidates = df[df["zip_code"].isin(zips_in_radius)] #.to_dict(orient='index')
    candidates= candidates.to_dict(orient='index')
    
    #remove candidates that are only drivers
    remove = []
    if (len(candidates) > 0):      
        for key, value in candidates.items():
            if (value['role'] == 'D'):
                remove.append(key)
        
    if len(remove) > 0: 
        for key in remove:
            try:
                del candidates[key]
            except KeyError:
                print('Cannot delete ', key)

    # print("find_candidates:", type(candidates), len(candidates))

    return candidates


    
def compare_schedules(candidates, driver):
    ''' Compare candidate's and driver's schedule
    Return: a dict with lists with the indices of candidates for all weekdays round-trip carpool, 
    MWF round-trip carpool, TR round-trip carpool, and a list for 
    each individual weekday round-trip carpool'''

    cand_week =[]
    cand_MWF = []
    cand_TR = []
    cand_M = []
    cand_T = []
    cand_W = []
    cand_R = []
    cand_F = []
    cand_S = []
    remove_lst =[]

    driver_schedule = check_driver_schedule(driver)

    if len(candidates) > 0:
        for cand in candidates.keys():
            # every weekday round trip
            if ( check_schedule(driver, candidates[cand]) ):
                cand_week.append(cand) # add to week list

            # MWF round trip
            elif ('M' and 'W' and 'F' in driver_schedule) and ( check_schedule_MWF(driver, candidates[cand]) ):
                cand_MWF.append(cand)

            # TR round trip
            elif ('T' and 'R' in driver_schedule) and  ( check_schedule_TR(driver, candidates[cand]) ):
                cand_TR.append(cand)
            
            # M round trip
            elif ('M' in driver_schedule) and ( check_schedule_M(driver, candidates[cand]) ):
                cand_M.append(cand)

            # T round trip
            elif ('T' in driver_schedule) and ( check_schedule_T(driver, candidates[cand]) ):
                cand_T.append(cand) 

            # W round trip
            elif ('W' in driver_schedule) and ( check_schedule_W(driver, candidates[cand]) ):
                cand_W.append(cand)        

            # R round trip
            elif  ('R' in driver_schedule) and ( check_schedule_R(driver, candidates[cand]) ):
                cand_R.append(cand)

            # F round trip
            elif ('F' in driver_schedule) and ( check_schedule_F(driver, candidates[cand]) ):
                cand_F.append(cand)

            # S round trip
            elif ('S' in driver_schedule) and ( check_schedule_S(driver, candidates[cand]) ):
                cand_S.append(cand)
            
            else: 
                # remove all remaining candidates
                remove_lst.append(cand)

    # remove candidates which schedule does not match
    for cand in remove_lst:
        del candidates[cand]

    # create a dict to hold all candidates found per day
    cand_dict = {'week': cand_week,
                'MWF': cand_MWF,
                'TR': cand_TR,
                'M': cand_M,
                'T': cand_T,
                'W': cand_W, 
                'R': cand_R, 
                'F': cand_F,
                'S': cand_S
                }
    return cand_dict



def compute_comp_score(driver, candidates, cand_lst):
    ''' Call comp_score with driver and each candidate from the list
    Return: list of candidates sorted from highest to lowest score for 
    the schedules all weekdays, MWF, and TR'''

    candidates_dict = dict()

    for cand in cand_lst:
        cs = comp_score(driver, candidates[cand])
        candidates[cand]['score'] = cs
        candidates_dict[cand]= candidates[cand].copy() 

    # Sort candidates by highest score
    cand_lst = sorted(candidates_dict, key = lambda x: candidates_dict[x]['score'], reverse=True)

    return cand_lst


def add_candidate_to(carpool, cand_lst, cand_dict, schedule, location):
    ''' Add candidates to carpool with ID, score, and meeting point for specified schedule
    Return: a list with indices of candidates that got a seat and should be removed from the pool''' 
    remove_lst = []
    cand_keys_lst = list(dict.fromkeys(cand_dict))

    # remove candidates that are already in the carpool
    remove_cand_lst = []
    for cand in cand_lst:
        if cand in carpool['candidates'].keys():
            remove_cand_lst.append(cand)

            # try:
            #     cand_lst.remove(cand)
            # except:
            #     pass
    for cand in remove_cand_lst:
        cand_lst.remove(cand)

    for cand in cand_lst:
        if (carpool['vacant_seats'] <= 0): 
            break  

        candidate = {'id': cand_dict[cand]['id'], 
                    'score':cand_dict[cand]['score'], 
                    'schedule': schedule, 
                    'meeting_point': location
                    }
        carpool['candidates'][cand] = candidate
        remove_lst.append(cand)
        carpool['vacant_seats'] = carpool['vacant_seats'] - 1

    return remove_lst



def save_carpool_to_df(df, carpool_dict):
    ''' Save the carpool dict into the carpool dataframe'''

    index = len(df.index)
    df.at[index, 'carpool_id'] = carpool_dict['carpool_id']
    df.at[index, 'driver_id'] = carpool_dict['driver']
    df.at[index, 'driver_schedule'] = carpool_dict['driver_schedule'] # MODIF: add driver schedule to df
    df.at[index, 'direction'] = 'RT'
    df.at[index, 'create_date'] = datetime.now()
    n = 0
    for cand in carpool_dict['candidates'].values():
        n += 1
        col = 'passenger_' + str(n)
        df.at[index, col] = cand['id']
        col = 'score_' + str(n)
        df.at[index, col] = cand['score']
        col = 'schedule_' + str(n)
        df.at[index, col] = cand['schedule']

    return



def create_carpools():
    '''Create carpools using all carpool_candidates from the database. 
    Save results into database at carpool_carpools table'''
    
    print("Creating carpools, please wait...")
    start_time = datetime.now() # store the execution start time

    # Get candidates from database
    queryset = Candidates.objects.all().values()
    pool_df = pd.DataFrame(queryset)

    # print('Candidates before adding new column', pool_df.shape)
    # print(pool_df.sample(1))
    # print(pool_df.info())

    #MODIF: add new column with carpool empty list to the dataframe to save which carpools a passenger belongs to
    pool_df["carpools_lst"] =  np.empty((len(pool_df), 0)).tolist()
    # print(stud_pool_df.columns)
    
    # print('Candidates after adding new column', pool_df.shape)
    # print(pool_df.sample(1))
    # print(pool_df.info())


    # Create a carpool dataframe to save the carpools

    df_columns = ['carpool_id', 'driver_id', 'driver_schedule',     # MODIF: add driver schedule 
                'passenger_1', 'score_1', 'schedule_1', 
                'passenger_2', 'score_2', 'schedule_2', 
                'passenger_3', 'score_3', 'schedule_3', 
                'direction', 'create_date'
                ]
    carpool_df = pd.DataFrame(columns= df_columns)

    # Create carpools while there are available drivers or until the pool is empty
    total_students = pool_df.shape[0]
    total_drivers = len(pool_df[pool_df['role']=='D']) + len(pool_df[pool_df['role']=='E']) 

    carpool_id = 0
    # MODIF: do NOT check len(pool_df) to allow all passengers to have a chance with other drivers
    while (total_drivers > 0): # and (len(pool_df.index)) > 0:
        carpool_id += 1

        #Select driver
        d_ind, driver = select_driver(pool_df)
        # print("Driver schedule:", check_driver_schedule(driver))

        # Remove driver from pool
        remove_from_pool([d_ind], pool_df) 

        # MODIF: do not use remove_lst to remove passengers from the pool
        remove_lst = [] # passengers won't be removed from pool

        # Create a carpool with this driver
        carpool_dict = create_carpool_dict(driver, carpool_id)

        # Get driver's route to school
        route_lst = get_route(driver['zip_code'])
        if (route_lst):
            #check if origin is in the list
            if driver['zip_code'] != route_lst[0]:
                route_lst.insert(0,driver['zip_code'])   

        # Find candidates for carpools
        stop = 0
        while carpool_dict['vacant_seats'] > 0 and len(route_lst) > 0:
            # Get driver's location
            location = route_lst.pop(0)

            if location == None:
                if len(route_lst) > 0 : 
                    # get another location on this route
                    location = route_lst.pop(0)
                else:
                    # start over
                    continue
            stop += 1

            # Broaden the search to a radius around this location
            zips_around = find_zips_around(location,5)

            # Find candidates around these locations 
            candidates = find_candidates(pool_df, zips_around)
        
            # Compare schedules and find possible matches for the whole week, MWF, and TR
            candidates_dict = compare_schedules(candidates, driver)

            # Check if any candidate is present in more than one list
            # result = [item for item in list2 if item in list1]
            # all week vs MWF
            repeated = [ cand for cand in candidates_dict['MWF'] if cand in candidates_dict['week']]
            for cand in repeated:  
                # del candidates_dict['MWF'][cand]
                candidates_dict['MWF'].remove(cand)   
            # All week vs TR
            repeated = [ cand for cand in candidates_dict['TR'] if cand in candidates_dict['week']]
            for cand in repeated:  
                # del candidates_dict['TR'][cand]
                candidates_dict['TR'].remove(cand)
            # All week vs M or MWF vs M
            repeated = [ cand for cand in candidates_dict['M'] if (cand in candidates_dict['week'] or cand in candidates_dict['MWF'])]
            for cand in repeated:  
                # del candidates_dict['M'][cand]
                candidates_dict['M'].remove(cand)
            # All week vs W or MWF vs W
            repeated = [ cand for cand in candidates_dict['W'] if (cand in candidates_dict['week'] or cand in candidates_dict['MWF'])]
            for cand in repeated:  
                # del candidates_dict['W'][cand]
                candidates_dict['W'].remove(cand)
            # All week vs F or MWF vs F
            repeated = [ cand for cand in candidates_dict['F'] if (cand in candidates_dict['week'] or cand in candidates_dict['MWF'])]
            for cand in repeated:  
                # del candidates_dict['F'][cand]
                candidates_dict['F'].remove(cand)
            # All week vs T or TR vs T
            repeated = [ cand for cand in candidates_dict['T'] if (cand in candidates_dict['week'] or cand in candidates_dict['TR'])]
            for cand in repeated:  
                # del candidates_dict['T'][cand]
                candidates_dict['T'].remove(cand)
            # All week vs R or TR vs R
            repeated = [ cand for cand in candidates_dict['R'] if (cand in candidates_dict['week'] or cand in candidates_dict['TR'])]
            for cand in repeated:  
                # del candidates_dict['R'][cand]
                candidates_dict['R'].remove(cand)
            # All week vs S
            repeated = [ cand for cand in candidates_dict['S'] if cand in candidates_dict['week'] ]
            for cand in repeated:  
                # del candidates_dict['S'][cand]
                candidates_dict['S'].remove(cand)


            # Compute compatibility scores and get a sorted list from highest to lowest score for each schedule
            schedules = ['week', 'MWF', 'TR', 'M', 'T', 'W', 'R', 'F', 'S']
            for schedule in schedules:
                candidates_dict[schedule] = compute_comp_score(driver, candidates, candidates_dict[schedule])

            # Add candidates into carpool from most matching days if carpool still has vancant seats
            for schedule in schedules:
                if (len(candidates_dict[schedule]) > 0) and carpool_dict['vacant_seats'] > 0: 
                    remove = add_candidate_to(carpool_dict,candidates_dict[schedule],candidates,schedule,location)
                    for cand in remove:
                        remove_lst.append(cand)


        # Remove riders from the pool
        # remove_from_pool(remove_lst, pool_df) # MODIF: do NOT remove candidates from pool_df

        # MODIF: use remove_lst to update pool_df adding this carpool to carpool_lst to all passengers
        # print('who are in the remove_lst?', remove_lst)
        for cand in remove_lst:
            # print(type(cand), cand)
            pool_df.at[cand, 'carpools_lst'].append(carpool_id)

        # Save carpool into dataframe
        save_carpool_to_df(carpool_df, carpool_dict)
        # print(carpool_dict) 

        # update total drivers counting all 'E' and 'D' that are remaining
        total_drivers = len(pool_df[pool_df['role']=='D']) + len(pool_df[pool_df['role']=='E']) 

    # How long did it take to process the whole dataset? 
    end_time = datetime.now() # store execution end time
    elapsed_time = end_time - start_time 

    # Count students
    alone_drivers = carpool_df['passenger_1'].isnull().sum()
    # MODIF: all passengers are still in the pool_Df, so shape[0] still has all passengers in it
    # unmatched = pool_df.shape[0]
    # MODIF: sum empty cells (with empty list) of new column to check how many passengers did not find a ride
    unmatched_passengers = 0
    for index, row in pool_df.iterrows():
        if len(row['carpools_lst']) == 0:
            # it means this person did not find any carpool after checking against all drivers
            unmatched_passengers += 1 
    unmatched = unmatched_passengers + alone_drivers
    total_carpools = carpool_df.shape[0] - alone_drivers 
    riders_drivers = total_students - unmatched

    # Drop new column before saving df into db
    carpool_df.drop(columns=['driver_schedule'], inplace= True)

    # Save carpool_df into the database
    mydatabase.save_carpool_df_into_db(carpool_df) # MODIF: columns df and databse do not match, so don't save it yet

    print("%d carpools created in %.2f seconds" % (carpool_df.shape[0], elapsed_time.seconds))
    print("Total students in the pool:", total_students)
    print('Alone drivers:', alone_drivers)
    print('Remaining passengers in the pool:', pool_df.shape[0] )
    print('Unmatched passengers + drivers: %d (%.1f %%)' % (unmatched, (unmatched/total_students)*100))
    print('Matched passengers + drivers: %d (%.1f %%)' % (riders_drivers, (riders_drivers/total_students)*100))
    print('Carpools with at least one passenger: %d'% total_carpools)


