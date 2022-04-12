#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 11:15:41 2022

@author: frostig
"""

import json
import numpy as np
from sqlalchemy import create_engine
from datetime import datetime
import astropy.units as u
import pandas as pd
from astropy.time import Time
from wintertoo.utils import get_alt_az, get_field_ids, get_start_stop_times, \
    get_program_details, validate_program_dates, get_tonight, up_tonight
import re


def save_df_to_sqlitedb(df, save_path):
    date = datetime.now().strftime('%m_%d_%Y_%H_%s')
    engine = create_engine(save_path + 'timed_requests_' + date + '_' + '.db?check_same_thread=False',
                           echo=True)
    sqlite_connection = engine.connect()
    sqlite_table = "Summary"

    # save
    df.to_sql(sqlite_table, sqlite_connection, if_exists='replace', index=False)
    sqlite_connection.close()
    return 0


def make_too_request_from_file(too_file_path, save_path, config_path):
    try:
        too_table = pd.read_csv(too_file_path, comment='#')
    except ValueError:
        return [-66]

    print(too_table)

    too_table['ra'] = too_table['RA_deg']
    too_table['dec'] = too_table['Dec_deg']
    too_table['filt'] = too_table['Filter']
    too_table['n_exps'] = too_table['Nexp']
    too_table['dither'] = too_table['Dither?']
    too_table['start_time'] = Time(
        np.array(too_table['Earliest UT Date'] + ' ' + too_table['UT Start Time'], dtype=str), format='iso').mjd
    too_table['stop_time'] = Time(np.array(too_table['Latest UT Date'] + ' ' + too_table['UT Finish Time'], dtype=str),
                                  format='iso').mjd
    too_table['program_name'] = too_table['propID']
    too_table['exptime'] = too_table['Texp']
    too_table['time_units'] = 'mjd'
    too_table['target_priority'] = 0

    status = []

    too_df = pd.DataFrame()
    base_index = 0
    for index, data in too_table.iterrows():
        # ret = make_too_request(data, save_path, config_path,index=index)
        ret, new_df = make_too_dataframe(data, config_path, base_index=base_index)
        too_df = pd.concat([too_df, new_df])
        status.append(ret)
        base_index = len(too_df)

    status = np.array(status)
    print(status)

    save_df_to_sqlitedb(too_df, save_path)
    return status


# def validate_program_pi(
#         program_name: str
# ):


def make_too_dataframe(data, config_path, base_index=0):
    # get header keys
    with open(config_path, "r") as jsonfile:
        config_data = json.load(jsonfile)

    start_time, stop_time = get_start_stop_times(data)
    n_exp = data['n_exps']
    ra, dec = data['ra'], data['dec']
    ra_rad, dec_rad = data['ra'] * u.deg.to(u.rad), data['dec'] * u.deg.to(u.rad)
    exptime = data['exptime']
    filt = data['filt']
    dither = data['dither']
    program_name = data['program_name']
    target_priority = data['target_priority']
    exposures_array = np.linspace(start_time.mjd, stop_time.mjd, n_exp)
    keys = config_data['Summary'].keys()
    key_array = []

    tonight = get_tonight(data)
    is_up, str_up = up_tonight(tonight, ra * u.deg, dec * u.deg)
    if not is_up:
        return -99, pd.DataFrame()

    programs_query_results = get_program_details(program_name)
    if len(programs_query_results) == 0:
        return -10, pd.DataFrame()

    program_details = programs_query_results[0]
    dates_valid = validate_program_dates(start_time.mjd, stop_time.mjd, program_details)

    if dates_valid < 0:
        return -20, pd.DataFrame()

    program_db_id = programs_query_results[0][0]
    program_pi_name = programs_query_results[0][2]
    program_base_priority = programs_query_results[0][6]

    target_final_priority = program_base_priority + target_priority

    for key in keys:
        key_array.append(key)
        # get alt and az from coordinates and time

    alt, az = get_alt_az(exposures_array, ra * u.deg, dec * u.deg)

    # make dataframe structure
    n_lines = n_exp
    ind = range(n_lines)
    df_data = np.zeros((n_lines, len(key_array)))
    df_data[:] = np.NaN
    save_df = pd.DataFrame(data=df_data, index=ind,
                           columns=key_array)

    # add values
    save_df["obsHistID"] = ind
    save_df["obsHistID"] = save_df["obsHistID"] + base_index
    save_df["requestID"] = ind
    save_df["requestID"] = save_df["requestID"] + base_index
    save_df["propID"] = program_db_id
    save_df["fieldRA"] = ra_rad
    save_df["fieldDec"] = dec_rad
    save_df["visitTime"] = exptime
    save_df["visitExpTime"] = exptime
    save_df["expDate"] = np.floor(start_time.mjd)
    save_df["validStart"] = start_time.mjd
    save_df["validStop"] = stop_time.mjd
    save_df["expMJD"] = exposures_array
    save_df["visitTime"] = exptime
    save_df["visitExpTime"] = exptime
    save_df["filter"] = filt
    save_df["dither"] = dither
    save_df["azimuth"] = az
    save_df["altitude"] = alt
    save_df["Priority"] = target_final_priority
    save_df["fieldID"] = 999999999  # protected id for guest obs
    save_df["metricValue"] = target_final_priority
    save_df["observed"] = 0

    return 0, save_df


def make_too_request(data, save_path, config_path, index=0):

    # get header keys
    with open(config_path, "r") as jsonfile:
        config_data = json.load(jsonfile)

    start_time, stop_time = get_start_stop_times(data)
    n_exp = data['n_exps']
    ra, dec = data['ra'], data['dec']
    ra_rad, dec_rad = data['ra'] * u.deg.to(u.rad), data['dec'] * u.deg.to(u.rad)
    exptime = data['exptime']
    filt = data['filt']
    dither = data['dither']
    program_name = data['program_name']
    target_priority = data['target_priority']
    exposures_array = np.linspace(start_time.mjd, stop_time.mjd, n_exp)
    keys = config_data['Summary'].keys()
    key_array = []

    tonight = get_tonight(data)
    is_up, str_up = up_tonight(tonight, ra * u.deg, dec * u.deg)
    if not is_up:
        return -99

    programs_query_results = get_program_details(program_name)
    if len(programs_query_results) == 0:
        return -10

    program_details = programs_query_results[0]
    dates_valid = validate_program_dates(start_time.mjd, stop_time.mjd, program_details)

    if dates_valid < 0:
        return -20

    program_db_id = programs_query_results[0][0]
    program_pi_name = programs_query_results[0][2]
    program_base_priority = programs_query_results[0][6]

    target_final_priority = program_base_priority + target_priority

    for key in keys:
        key_array.append(key)
        # get alt and az from coordinates and time

    alt, az = get_alt_az(exposures_array, ra * u.deg, dec * u.deg)

    # make dataframe structure
    n_lines = n_exp
    ind = range(n_lines)
    df_data = np.zeros((n_lines, len(key_array)))
    df_data[:] = np.NaN
    save_df = pd.DataFrame(data=df_data, index=ind,
                           columns=key_array)

    # add values
    save_df["obsHistID"] = ind
    save_df["requestID"] = ind
    save_df["propID"] = program_db_id
    save_df["fieldRA"] = ra_rad
    save_df["fieldDec"] = dec_rad
    save_df["visitTime"] = exptime
    save_df["visitExpTime"] = exptime
    save_df["expDate"] = np.floor(start_time.mjd)
    save_df["validStart"] = start_time.mjd
    save_df["validStop"] = stop_time.mjd
    save_df["expMJD"] = exposures_array
    save_df["visitTime"] = exptime
    save_df["visitExpTime"] = exptime
    save_df["filter"] = filt
    save_df["dither"] = dither
    save_df["azimuth"] = az
    save_df["altitude"] = alt
    save_df["Priority"] = target_final_priority
    save_df["fieldID"] = 999999999  # protected id for guest obs
    save_df["metricValue"] = target_final_priority

    # save_df.reset_index(drop=True, inplace=True)


    # make sqlite database
    date = datetime.now().strftime('%m_%d_%Y_%H_%s')
    engine = create_engine(save_path + 'timed_requests_' + date + '_' + str(index) + '.db?check_same_thread=False',
                           echo=True)
    sqlite_connection = engine.connect()
    sqlite_table = "Summary"

    # save
    save_df.to_sql(sqlite_table, sqlite_connection, if_exists='replace', index=False)
    sqlite_connection.close()
    return 0


def make_timed_request(save_path, config_path, ra, dec, exptime, n_exp, start, stop, exp_arr, filt, dither):
    # make sqlite database
    date = datetime.now().strftime('%m_%d_%Y_%H_%s')
    engine = create_engine(save_path + 'timed_requests_' + date + '.db?check_same_thread=False', echo=True)
    sqlite_connection = engine.connect()

    # get header keys
    with open(config_path, "r") as jsonfile:
        data = json.load(jsonfile)

    keys = data['Summary'].keys()
    key_array = []
    for key in keys:
        key_array.append(key)
        # print(key)

    # get alt and az from coordinates and time
    alt, az = get_alt_az(exp_arr, ra, dec)

    # make dataframe structure
    n_lines = n_exp
    ind = range(n_lines)
    df_data = np.zeros((n_lines, len(key_array)))
    df_data[:] = np.NaN
    save_df = pd.DataFrame(data=df_data, index=ind,
                           columns=key_array)

    # add values
    save_df["obsHistID"] = ind
    save_df["requestID"] = ind
    save_df["propID"] = 4
    save_df["fieldRA"] = ra
    save_df["fieldDec"] = dec
    save_df["visitTime"] = exptime
    save_df["visitExpTime"] = exptime
    save_df["expDate"] = np.floor(start)
    save_df["validStart"] = start
    save_df["validStop"] = stop
    save_df["expMJD"] = exp_arr
    save_df["visitTime"] = exptime
    save_df["visitExpTime"] = exptime
    save_df["filter"] = filt
    save_df["dither"] = dither
    save_df["azimuth"] = az
    save_df["altitude"] = alt
    save_df["fieldID"] = 999999999  # protected id for guest obs

    # save_df.reset_index(drop=True, inplace=True)

    # save
    sqlite_table = "Summary"

    save_df.to_sql(sqlite_table, sqlite_connection, if_exists='replace', index=False)
    sqlite_connection.close()
    return 0


def make_untimed_request(write_path, camera, data, field_opts, filters):
    date = datetime.now().strftime('%m_%d_%Y_%H_%s')

    if camera == 'WINTER':
        write_path = write_path + 'winter_untimed_request' + date + '.json'
    else:
        write_path = write_path + 'summer_untimed_request' + date + '.json'

    # parse priority (get string before : )
    nightly_priority = str(data['priority'])[:str(data['priority']).index(":")]

    # parse field selections

    # sort by field ids
    if data['field_selection'] == field_opts[0]:
        field_selection = "field_ids"
        # check if ra and dec are empty
        if len(data['ra']) == 0 or len(data['dec']) == 0:
            return 0
        else:
            # pasre ra dec
            ra = re.split(r',|\[|\]', data['ra'])
            ra = [i for i in ra if i]
            dec = re.split(r',|\[|\]', data['dec'])
            dec = [i for i in dec if i]
            field_cut = get_field_ids(camera, ra, dec, units="degrees")

    # sort by ra and dec cuts
    elif data['field_selection'] == field_opts[1]:
        # check if cuts are empty
        if len(data['ra_cut']) == 0 or len(data['dec_cut']) == 0:
            return 0
        else:
            field_selection = "field_selections"
            if len(data['ra_cut']) != 0 and len(data['dec_cut']) != 0:
                ra_cut = re.split(r',|\[|\]', data['ra_cut'])
                ra_cut = [float(i) for i in ra_cut if i]
                dec_cut = re.split(r',|\[|\]', data['dec_cut'])
                dec_cut = [float(i) for i in dec_cut if i]
                field_cut = {"ra_range": ra_cut,
                             "dec_range": dec_cut}
            elif len(data['ra_cut']) != 0 and len(data['dec_cut']) == 0:
                ra_cut = re.split(r',|\[|\]', data['ra_cut'])
                ra_cut = [float(i) for i in ra_cut if i]
                field_cut = {"ra_range": ra_cut}
            else:
                dec_cut = re.split(r',|\[|\]', data['dec_cut'])
                dec_cut = [float(i) for i in dec_cut if i]
                field_cut = {"dec_range": dec_cut}

    # sort by galactic longitude and latitude cuts
    elif data['field_selection'] == field_opts[2]:
        if len(data['ra_cut']) == 0 or len(data['dec_cut']) == 0:
            return 0
        else:
            field_selection = "field_selections"
            if len(data['ra_cut']) != 0 and len(data['dec_cut']) != 0:
                ra_cut = re.split(r',|\[|\]', data['ra_cut'])
                ra_cut = [float(i) for i in ra_cut if i]
                dec_cut = re.split(r',|\[|\]', data['dec_cut'])
                dec_cut = [float(i) for i in dec_cut if i]
                field_cut = {"l_range": ra_cut,
                             "b_range": dec_cut}
            elif len(data['ra_cut']) != 0 and len(data['dec_cut']) == 0:
                ra_cut = re.split(r',|\[|\]', data['ra_cut'])
                ra_cut = [float(i) for i in ra_cut if i]
                field_cut = {"l_range": ra_cut}
            else:
                dec_cut = re.split(r',|\[|\]', data['dec_cut'])
                dec_cut = [float(i) for i in dec_cut if i]
                field_cut = {"b_range": dec_cut}

    # parse filter selections
    filter_choice = str(data['filter_choice'])[:str(data['filter_choice']).index(":")]

    # convert filter names to id numbers
    filter_ids = []
    for filt in data['filters']:
        filter_ids.append(filters.index(filt) + 1)

    program_data = {"program_name": "collaboration",
                    "subprogram_name": str(data['prog_name']),
                    "program_pi": str(data['name']),
                    "program_observing_fraction": 0.0,  # to be calculated later
                    "subprogram_fraction": 0.0,  # to be calculated later
                    field_selection: field_cut,
                    "filter_choice": filter_choice,
                    "filter_ids": filter_ids,
                    "internight_gap_days": int(data['internight_gap_days']),
                    "n_visits_per_night": int(data['n_visits_per_night']),
                    "nightly_priority": nightly_priority,
                    "exposure_time": float(data['exp']),
                    "active_months": "all"
                    }

    # add optional arguments
    if data['intranight_gap_min'] != None:
        program_data['intranight_gap_min'] = int(data['intranight_gap_min'])

    if data['intranight_half_width_min'] != None:
        program_data['intranight_half_width_min'] = int(data['intranight_half_width_min'])

    json_data = json.dumps(program_data)

    with open(write_path, "w") as jsonfile:
        jsonfile.write(json_data)
        print("Write successful")

    return 1

# make_untimed_request("test_prog", "my_name")
