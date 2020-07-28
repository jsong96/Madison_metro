

# Author: Jiwon Song

from zipfile import ZipFile
import pandas as pd
from datetime import datetime
from math import sin, cos, asin, sqrt, pi
import copy

class Node:
    '''
    Node Class
    list of components:
    
        stops = list of stops
        val = split point
        split_type = x or y (vertical or horizontal)
    '''
    def __init__(self, stops, val,split_type):
        self.left = None
        self.right = None
        
        # x or y coordinate that was splited into half
        self.val = val
        
        # to identify x or y
        self.type = split_type
        
        # list of Stops
        self.stops = stops
        
class Tree:
    
    '''
    Tree Class for binary tree
    dump method is for debugging
    '''
    def __init__(self, stops):
        
        self.root = Node(stops,stops[len(stops)//2].location.x,None)
        self.size = 0
               
    
    def build_tree(self,root, stops, level, split_type):
        
        # until level 6
        if level > 0:
            
            # horizontal
            if split_type == 'x' or split_type == None:
                # sort the list by x val of location
                stops.sort(key=lambda p : p.location.x)

                root.left = Node(stops[:len(stops)//2], stops[len(stops)//2].location.x, 'x')
                root.right = Node(stops[len(stops)//2:], stops[len(stops)-1].location.x, 'x') 
                self.size += 2
                
                return self.build_tree(root.left,stops[:len(stops)//2], level-1, 'y') + self.build_tree(root.right, stops[len(stops)//2:], level-1, 'y')

            # vertical
            if split_type == 'y':
                # sort the list by y val of location
                stops.sort(key=lambda p : p.location.y)
                
                root.left = Node(stops[:len(stops)//2], stops[len(stops)//2].location.y, 'y')
                root.right = Node(stops[len(stops)//2:], stops[len(stops)-1].location.y, 'y')
                self.size += 2

                return self.build_tree(root.left, stops[:len(stops)//2], level-1, 'x') + self.build_tree(root.right, stops[len(stops)//2:], level-1, 'x')
        else:
            return 0
            
        
    def dump(self):
        if self.root is not None:
            self._dump(self.root)
        
    def _dump(self, node):
        if node is not None:
            self._dump(node.left)
            
            print(node.val)
            self._dump(node.right)


class BusDay:
    def __init__(self,date):
        
        # lists to store elements
        self.service_ids = []
        self.trip_list = []
        self.stop_list = []
        
        # index of df is fixed
        date_idx = 2 + date.weekday()
    
        # open files and create dataframes
        with ZipFile('mmt_gtfs.zip') as zf:
            with zf.open("calendar.txt") as f:
                df = pd.read_csv(f)
            with zf.open("trips.txt") as f:
                trips = pd.read_csv(f)
            with zf.open('stops.txt') as f:
                stops = pd.read_csv(f)
            with zf.open('stop_times.txt') as f:
                stop_times = pd.read_csv(f)
        
        # creating service id list O(N)
        for i in range(len(df)):
             
            s_tmp = str(df.loc[i].start_date)
            start = datetime(int(s_tmp[:4]),int(s_tmp[4:6]),int(s_tmp[6:]))
            e_tmp = str(df.loc[i].end_date)
            end = datetime(int(e_tmp[:4]),int(e_tmp[4:6]),int(e_tmp[6:]))
            if start <= date and date <= end:
                if df.loc[i][date_idx] == 1:
                    self.service_ids += [df.loc[i].service_id]
        # sort the list by its element's service ID        
        self.service_ids = sorted(self.service_ids)
        
        
        # creating trip_list O(N)        
        filtered_trip = trips[trips['service_id'].isin(self.service_ids)]
        for row in filtered_trip.iterrows():
            data = row[1]
            self.trip_list += [Trip( data.trip_id ,data.route_short_name  , bool(data.bikes_allowed))]
            
        # sort the list by its element's trip ID
        self.trip_list.sort(key= lambda x : x.trip_id)
        
        
        # taking out trip ids
        trip_ids = []
        for element in self.trip_list:
            trip_ids += [element.trip_id]
        trip_ids = list(set(trip_ids))
        
        # filter stop times dataframe
        filtered_stop_times = stop_times[stop_times['trip_id'].isin(trip_ids)]
        # create stop df according to the corresponding stop times
        filtered_stop = stops[stops['stop_id'].isin(filtered_stop_times['stop_id'])]
        
        # creating stop_list O(N)
        for row in filtered_stop.iterrows():
            data = row[1]
            loc = Location(latlon = (data.stop_lat, data.stop_lon))
            
            self.stop_list += [Stop(data.stop_id, loc, bool(data.wheelchair_boarding))]
        
        
        # sort the list by its element's stop ID
        self.stop_list.sort(key = lambda x : x.stop_id)
        
        self.tmp_stops = copy.deepcopy(self.stop_list)
        
        # creating a binary tree
        self.tree = Tree(self.tmp_stops)
        self.tree.build_tree(self.tree.root,self.tmp_stops,6,'x')
        
        # lists to hold certain Stop instances
        no_wheel = []
        wheels = []
        
        for stop in self.stop_list:
            if stop.w_brding == True:
                wheels += [stop]
                
            else:
                no_wheel += [stop]
                
        # convert the lists into dataframe for scatter plot
        self.wheels = pd.DataFrame.from_records(s.to_dict() for s in wheels)
        self.no_wheels = pd.DataFrame.from_records(s.to_dict() for s in no_wheel)
        
        # make a copy of its stop_list for draw_tree
        self.stop_cpy = copy.deepcopy(self.stop_list) 
                
                
        
    def get_stops(self):
        return self.stop_list
    
    def get_trips(self,route_id = None):
        filtered = []
        if route_id is not None:
            for trips in self.trip_list:
                if trips.route_id == route_id:
                    filtered += [trips]
            return filtered
        
        else:
             return self.trip_list
        
    
    def get_stops_rect(self,xcord,ycord):
        # call its helper method and return the result
        return self._get_stops_rect(self.tree.root, xcord, ycord)

    
    def _get_stops_rect(self,node, x, y):
        '''
        helper method for get_stops_rect()
        
        '''
        # if it is a leaf node
        if node.left is None and node.right is None:
            fit = []
            for stop in node.stops:
                # take Stops that are in the area of rectangle
                if stop.location.x >= x[0] and stop.location.x <= x[1] and stop.location.y >= y[0] and stop.location.y <= y[1]:
                    fit += [stop]
                    
                    
            return fit
        
        else:
            return self._get_stops_rect(node.left,x,y) + self._get_stops_rect(node.right,x,y)
            
            
    
    def get_stops_circ(self,xy,radius):
        
        x1 = xy[0]-radius
        x2 = xy[0]+radius
        
        y1 = xy[1]-radius
        y2= xy[1]+radius
        
        # first take Stops that are in the rectangle area
        rect = self.get_stops_rect((x1,x2),(y1,y2))
        
        # filter those that are in the circle area
        circle = self._get_stops_circ(rect, xy, radius)
        
        return circle
    
    def _get_stops_circ(self, rect, xy, radius):
        
        # find Stops that are in the range (center of circle(x,y) ~ radius)
        circle = []
        for point in rect:
            if (point.location.x - xy[0]) * (point.location.x - xy[0]) + (point.location.y - xy[1]) * (point.location.y - xy[1]) <= (radius * radius):
                circle += [point]
        
        return circle
    
    
    def scatter_stops(self,ax):
        # scatter plot red for with wheel chairs and grey for no wheel chairss
        self.wheels.plot.scatter(x= 'location_x', y= 'location_y', ax= ax, s= 1.5, color = 'red')
        self.no_wheels.plot.scatter(x= 'location_x', y='location_y', ax=ax, s= 1.5, color = '0.7')
        
        
        
        
    
    def draw_tree(self,ax):
        # set a starting level 
        level = 1
        # set line width to plot line
        lw = 6
        # call helper method to plot lines
        self.split_helper(self.stop_cpy,level,lw,None,ax)

    def split_helper(self, stops, level, lw, way, ax):
        '''
        helper method for draw_tree
        '''
        # check each level and draw lines
        if level == 1:
            stops.sort(key=lambda p : p.location.x)
            
            x = stops[len(stops)//2].location.x
            ax.plot((x,x), ax.get_ylim(), lw=lw, zorder = -10, color = 'goldenrod')
            
            self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
            self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
        
        if level == 2:
            
            
            x1 = stops[-1].location.x
            x2 = stops[0].location.x
            
            stops.sort(key=lambda p : p.location.y)
            y = stops[len(stops)//2].location.y
            
            if way == 'l':
                ax.plot((ax.get_xlim()[0], x1), (y,y),lw=lw, zorder = -10, color = 'goldenrod' )
                
                self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
                self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
            if way == 'r':

                ax.plot((x2  ,ax.get_xlim()[1]), (y,y),lw=lw, zorder = -10, color = 'goldenrod' )
                
                self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
                self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
        
        if level == 3:
                  
            y1 = stops[-1].location.y
            y2 = stops[0].location.y
            
            stops.sort(key=lambda p : p.location.x)
            x = stops[len(stops)//2].location.x
            
            if way == 'l':
                ax.plot((x, x), (ax.get_ylim()[0], y1),lw=lw, zorder = -10, color = 'goldenrod' )
                
                self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
                self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
            if way == 'r':

                ax.plot((x, x), (y2,ax.get_ylim()[1]),lw=lw, zorder = -10, color = 'goldenrod' )
                
                self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
                self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
        
        if level == 4:
            
            x1 = stops[0].location.x
            x2 = stops[-1].location.x
            
            stops.sort(key=lambda p : p.location.y)
            y = stops[len(stops)//2].location.y
            
            if way == 'l':
                ax.plot((x1, x2), (y,y),lw=lw, zorder = -10, color = 'goldenrod' )
                
                self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
                self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
            if way == 'r':
               
                ax.plot((x1, x2), (y,y),lw=lw, zorder = -10, color = 'goldenrod' )
                
                self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
                self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
        
        if level == 5:
            
            y1 = stops[0].location.y
            y2 = stops[-1].location.y
            
            stops.sort(key=lambda p : p.location.x)
            x = stops[len(stops)//2].location.x
            
            if way == 'l':
                
                ax.plot((x, x), (y1,y2),lw=lw, zorder = -10, color = 'goldenrod' )
                
                self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
                self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
                
            if way == 'r':

                ax.plot((x, x), (y1,y2),lw=lw, zorder = -10, color = 'goldenrod' )
                
                self.split_helper(stops[:len(stops)//2], level + 1, lw-1, 'l',ax)
                self.split_helper(stops[len(stops)//2:], level + 1, lw-1, 'r',ax)
                
        if level ==6:
            
            x1 = stops[0].location.x
            x2 = stops[-1].location.x
            
            stops.sort(key=lambda p : p.location.y)
            y = stops[len(stops)//2].location.y
    
            if way == 'l':
                ax.plot((x1, x2), (y,y),lw=lw, zorder = -10, color = 'goldenrod' )
                
                
            if way == 'r':
               
                ax.plot((x1, x2), (y,y),lw=lw, zorder = -10, color = 'goldenrod' )
                  
                    
class Trip:
    def __init__(self,trip_id,route_short_name,bikes_allowed):
        self.trip_id = trip_id
        self.route_id = route_short_name
        self.bikes_allowed = bikes_allowed
    
    def __repr__(self):
        return ('Trip(%s, %s, %r)'% (self.trip_id,self.route_id,self.bikes_allowed))

class Stop:
    def __init__(self,stop_id, loc, wheelchair_boarding):
        self.stop_id = stop_id
        self.location = loc
        self.w_brding = wheelchair_boarding
    def __repr__(self):
        return ('Stop(%s, %s, %r)' % (self.stop_id, self.location, self.w_brding))
    def to_dict(self):
        return {
            'stop_id': self.stop_id,
            'location_x': self.location.x,
            'location_y': self.location.y,
            'wheelchair': self.w_brding
            
        }
    
    

def haversine_miles(lat1, lon1, lat2, lon2):
    """Calculates the distance between two points on earth using the
    harversine distance (distance between points on a sphere)
    See: https://en.wikipedia.org/wiki/Haversine_formula

    :param lat1: latitude of point 1
    :param lon1: longitude of point 1
    :param lat2: latitude of point 2
    :param lon2: longitude of point 2
    :return: distance in miles between points
    """
    lat1, lon1, lat2, lon2 = (a/180*pi for a in [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon/2) ** 2
    c = 2 * asin(min(1, sqrt(a)))
    d = 3956 * c
    return d


class Location:
    """Location class to convert lat/lon pairs to
    flat earth projection centered around capitol
    """
    capital_lat = 43.074683
    capital_lon = -89.384261

    def __init__(self, latlon=None, xy=None):
        if xy is not None:
            self.x, self.y = xy
        else:
            # If no latitude/longitude pair is given, use the capitol's
            if latlon is None:
                latlon = (Location.capital_lat, Location.capital_lon)

            # Calculate the x and y distance from the capital
            self.x = haversine_miles(Location.capital_lat, Location.capital_lon,
                                     Location.capital_lat, latlon[1])
            self.y = haversine_miles(Location.capital_lat, Location.capital_lon,
                                     latlon[0], Location.capital_lon)

            # Flip the sign of the x/y coordinates based on location
            if latlon[1] < Location.capital_lon:
                self.x *= -1

            if latlon[0] < Location.capital_lat:
                self.y *= -1

    def dist(self, other):
        """Calculate straight line distance between self and other"""
        return sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def __repr__(self):
        return "Location(xy=(%0.2f, %0.2f))" % (self.x, self.y)
