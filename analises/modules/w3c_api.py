#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Functions for collecting data from W3C API
Copyright (C) 2024  Henrique S. Xavier
Contact: hsxavier@gmail.com

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import requests
import json
import pandas as pd
from glob import glob


def one_call_w3c_api(endpoint, api_root=''):
    """
    Make a request to W3C API. The endpoint may contain parameters,
    e.g.: 'https://api.w3.org/groups?page=2&items=100'

    Returns a JSON.
    """
    
    headers = {'accept': 'application/json'}
    response = requests.get(api_root + endpoint, headers=headers)
    #assert response.status_code == 200, 'Request failed for endpoint ' + endpoint 
    data = json.loads(response.text)
    
    return data


def get_all_data(endpoint):
    """
    Cycle through pages of the response and return all the data.
    Returns a list.
    """
    
    # Make the first API call:
    content = one_call_w3c_api(endpoint)
    dname = endpoint.split('/')[-1]

    # Avoid 404 errors:
    if '_links' in content:
        # Check if there is data associated to the entity:
        if dname in content['_links']:
            # Get first data:
            data = content['_links'][dname]
            # Call next pages:
            while 'next' in 'next' in content['_links']:
                # Concatenate data:
                content = one_call_w3c_api(content['_links']['next']['href'])
                data += content['_links'][dname]
        # If there is no data:
        else:
            data = []
        # Sanity check:
        assert len(data) == content['total']
    else:
        # Make sure the reason for error is the known one:
        assert content['status'] == 404
        data = []
        
    return data


def get_group_properties(group_endpoint, verbose=False):
    """
    Get characteristics of a W3C group given its API endpoint.
    Returns a dict.
    """
    if verbose == True:
        print(group_endpoint)
    group_properties = one_call_w3c_api(group_endpoint)
    group_properties['call'] = group_endpoint
    links = group_properties.pop('_links')
    urls  = {k:links[k]['href'] for k in ['homepage', 'users', 'participations', 'chairs'] if k in links}
    group_properties.update(urls)
    if verbose == True:
        print(group_properties['name'])
    
    return group_properties


def get_properties(endpoint, extra, verbose=False):
    """
    Get characteristics of a W3C entity (group, affiliation) given its 
    API endpoint. `extra` are links to incorporate in the data, that 
    are links under '_links' key.
    Returns a dict.
    """
    # Log activity if requested:
    if verbose == True:
        print(endpoint)

    # Get basic info:
    properties = one_call_w3c_api(endpoint)
    # Save info source:
    properties['call'] = endpoint
    
    # Get relevant links:
    if '_links' in properties:
        links = properties.pop('_links')
        urls  = {k:links[k]['href'] for k in extra if k in links}
        properties.update(urls)

    # Log activity if requested:
    if verbose == True and 'name' in properties:
        print(properties['name'])
    
    return properties


def get_user_affiliations(endpoint):
    """
    Request information about a W3C users' affiliations, put it
    in a DataFrame. Example of `endpoint`:
    https://api.w3.org/users/ciqasp9689444sg0c4k4k0gc44cg44c/affiliations
    """
    
    user_affiliations = get_all_data(endpoint)
    user_affiliations_df = pd.DataFrame(user_affiliations)
    user_affiliations_df['call'] = endpoint
    
    return user_affiliations_df


def unique_shortname(users_endpoint, prefix='https://api.w3.org/groups/', suffix='/users'):
    """
    Create an unique identifier for the group users endpoint.
    Get `users_endpoint` (string) as input and returns a string.
    """
    return users_endpoint.replace(prefix, '').replace(suffix, '').replace('/', '+')


def load_raw_api_data(file_pattern):
    """
    Load data saved in many CSV files (fulfilling the provided
    `file_pattern`) into a DataFrame.
    """
    
    filelist = glob(file_pattern)
    df = pd.concat([pd.read_csv(f) for f in filelist], ignore_index=True)
    
    return df


# If running this code as a script:
if __name__ == '__main__':
    pass
