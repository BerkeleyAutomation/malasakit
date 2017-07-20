#!/usr/bin/env python2

from __future__ import unicode_literals, print_function
import openpyxl
import json

workbook = openpyxl.load_workbook('PSGC Publication MAR2017.xlsx', read_only=True)
worksheet = workbook['PSGC']
location_data = {}

province, municipality_or_city, barangay = None, None, None

for index, row in enumerate(worksheet.rows):
    if index == 0:  # Skip the header
        continue
    row = [cell.value for cell in row]
    code, name, level, income, urban_or_rural, population = row
    if level == 'Prov':
        province = name
        location_data[province] = {}
        print('Processing province {0}'.format(name))
    elif level == 'City' or level == 'Mun':
        municipality_or_city = name
        location_data[province][municipality_or_city] = []
        print('  Processing municipality or city {0}'.format(name))
    elif level == 'Bgy':
        location_data[province][municipality_or_city].append(name)
    elif level is not None and level != 'Reg':
        pass

with open('pcari/static/data/location-data.json', 'w+') as json_file:
    json.dump(location_data, json_file)
