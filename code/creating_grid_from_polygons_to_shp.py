#!/usr/bin/env python
# coding: utf-8

# In[2]:


import osmnx as ox, matplotlib.pyplot as plt, pandas as pd, geopandas as gpd
from descartes import PolygonPatch
from shapely.geometry import Point, Polygon, MultiPolygon
#get_ipython().run_line_magic('matplotlib', 'inline')
import cartoframes
from cartoframes import QueryLayer, Layer, styling, Credentials, CartoContext
import pandas as pd
import geopandas as gpd
from shapely import *
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.ops import cascaded_union
from shapely.ops import unary_union
import time
from IPython.display import clear_output
import sys
import math
import numpy as np
from shapely.wkt import loads
import os

# Enter your username and api key below
cc = cartoframes.CartoContext(base_url='https://{username}.carto.com/'.format(username='celtiberian'), api_key='f311b3de86d1ecc95e5a702615b630ef3947187d')


# In[30]:


INPUT_TABLE_NAME = 'ecu_adm0'
BIG_GRID_SIDE = 25000 #METERS
OUTPUT_TABLE_NAME = f'{INPUT_TABLE_NAME}_big_grid_{BIG_GRID_SIDE}_meters'

FOLDER_PATH = '../Resources'
FOLDER_NAME = 'ecuador_grid_shp'
FILE_PREFIX = 'ecuador_250_part'

if not os.path.exists(f'{FOLDER_PATH}/{FOLDER_NAME}'):
    os.makedirs(f'{FOLDER_PATH}/{FOLDER_NAME}')
    

# ### Create a table of big grid 50km x 50km with this query
# WITH grid as (
#   SELECT
#     row_number() over () as cartodb_id,
#     CDB_RectangleGrid(
#       ST_Buffer(the_geom_webmercator, 1000000),
#       __Big_Grid_side_length_in_meters__,
#       __Big_Grid_side_length_in_meters__
#     ) AS the_geom_webmercator
#   FROM
#     __TABLE_NAME__)
# 
# SELECT
#   grid.the_geom_webmercator,
#   row_number() over() as cartodb_id
# FROM
#   grid, __TABLE_NAME__ a
# WHERE
#   ST_Intersects(grid.the_geom_webmercator, a.the_geom_webmercator)
#   
# __Example:__
# 
# WITH grid as (
#   SELECT
#     row_number() over () as cartodb_id,
#     CDB_RectangleGrid(
#       ST_Buffer(the_geom_webmercator, 1000000),
#       50000,
#       50000
#     ) AS the_geom_webmercator
#   FROM
#     chl_adm0)
# 
# SELECT
#   grid.the_geom_webmercator,
#   row_number() over() as cartodb_id
# FROM
#   grid, chl_adm0 a
# WHERE
#   ST_Intersects(grid.the_geom_webmercator, a.the_geom_webmercator)
# 

# In[25]:


start = time.time()
query =    f'''
    CREATE TABLE IF NOT EXISTS {OUTPUT_TABLE_NAME} AS (
        WITH grid as (
          SELECT
            row_number() over () as cartodb_id,
            CDB_RectangleGrid(
              ST_Buffer(the_geom_webmercator, 1000000),
              {BIG_GRID_SIDE},
              {BIG_GRID_SIDE}
            ) AS the_geom_webmercator
          FROM
            {INPUT_TABLE_NAME})

        SELECT
          grid.the_geom_webmercator,
          row_number() over() as cartodb_id
        FROM
          grid, {INPUT_TABLE_NAME} a
        WHERE
          ST_Intersects(grid.the_geom_webmercator, a.the_geom_webmercator)
    );
    select cdb_cartodbfytable('{OUTPUT_TABLE_NAME}');
    '''
grid_gdf = cc.query(query, decode_geom=True)
end = time.time()
print('Read italy shape from carto time:', end - start)


# In[27]:


start = time.time()
grid_gdf = cc.read(OUTPUT_TABLE_NAME, decode_geom=True)
end = time.time()
print('Read italy shape from carto time:', end - start)


# In[28]:


print('Number of big grid: ', grid_gdf.shape[0])


# In[6]:


grid_bounds = grid_gdf.iloc[0].geometry.bounds
[xmin, ymin, xmax, ymax] = grid_bounds


# In[7]:


def haversine(lon1, lat1, lon2, lat2):
    R = 6372800  # Earth radius in meters
    
    phi1, phi2 = math.radians(lat1), math.radians(lat2) 
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 +         math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1 - a))


# In[ ]:





# In[8]:


horizontal_len = haversine(xmin, ymin, xmin, ymax)
vertical_len = haversine(xmin, ymin, xmax, ymin)
print (f'Horizontal len: {horizontal_len}, Vertical len: {vertical_len}')


# In[9]:


final_grid_size = 250 #meters

rows = math.ceil(round(horizontal_len) / final_grid_size)
cols = math.ceil(round(vertical_len)  / final_grid_size)
print (f'Rows: {rows}, cols: {cols}')


# In[10]:


init_start = time.time()
length = len(grid_gdf.geometry)
intersects_grid_list = [gpd.GeoDataFrame] * (length + 1)
print(length)
for index in grid_gdf.index:
    start_for = time.time() 
    xmin,ymin,xmax,ymax =  grid_gdf.geometry[index].bounds
    start = time.time()
    width = abs(xmax - xmin) / rows
    height = abs(ymax - ymin) / cols
    XleftOrigin = xmin
    XrightOrigin = xmin + width
    YtopOrigin = ymax
    YbottomOrigin = ymax- height
    polygons = []
    for i in range(rows):
        Ytop = YtopOrigin
        Ybottom =YbottomOrigin
        for j in range(cols):
            polygons.append(Polygon([(XleftOrigin, Ytop), (XrightOrigin, Ytop), (XrightOrigin, Ybottom), (XleftOrigin, Ybottom)])) 
            Ytop = Ytop - height
            Ybottom = Ybottom - height
        XleftOrigin = XleftOrigin + width
        XrightOrigin = XrightOrigin + width
    grid = gpd.GeoDataFrame({'geometry':polygons})
    intersects_grid = grid
    intersects_grid_list[index] = intersects_grid
    end_for = time.time() 
    clear_output(wait=True)
    print('Current progress:', index, '/', length, f'Loop {index} time: ', end_for - init_start)


final_end = time.time()
print(f'Total time: ', final_end - init_start)


# In[11]:


intersects_grid_list[2].head()


# In[12]:


start = time.time()
intersects_grid_all = gpd.GeoDataFrame()
sum_grid = 0
for index, value in enumerate(intersects_grid_list):
    try:
        if (intersects_grid_list[index] == gpd.geodataframe.GeoDataFrame):
            continue
    except:
        if (len(intersects_grid_list[index].shape) == 2):
            if intersects_grid_all.empty:
                intersects_grid_all = intersects_grid_list[index]
            else:
                intersects_grid_all = intersects_grid_all.append(intersects_grid_list[index])
            sum_grid += intersects_grid_list[index].shape[0]
            clear_output(wait=True)
            print (f'index: {index}, sum: ', sum_grid)
end = time.time()
print(f'Total time: ', end - start)


# In[15]:


print('Total number of grids: ', intersects_grid_all.shape[0])


# In[16]:


intersects_grid_all.head()


# In[17]:


intersects_grid_all = intersects_grid_all.reset_index()


# In[19]:


intersects_grid_all['poly_id'] = intersects_grid_all.index


# In[20]:


intersects_grid_all.head()


# In[24]:

start = time.time()
number_small_grid = cols * rows
number_of_file = round(intersects_grid_all.shape[0]/number_small_grid)
start_file_number = 0
for i in range(start_file_number,number_of_file):
    #print(i)
    print(f'File name: ecuador_250_part{i + 1}.csv from {number_small_grid * i} to {number_small_grid * (i + 1)}')
    tmp = intersects_grid_all.iloc[number_small_grid * i :number_small_grid * (i + 1)]
    #print(tmp.columns)
    intersects_grid_all.iloc[number_small_grid * i :number_small_grid * (i + 1)][['poly_id', 'geometry']].to_file(f'{FOLDER_PATH}/{FOLDER_NAME}/{FILE_PREFIX}{i + 1}.shp')
end = time.time()
print(f'Total time: ', end - start)


# In[ ]:




