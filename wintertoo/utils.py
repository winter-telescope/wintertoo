#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 13:51:59 2022
@author: frostig, belatedly edited by Robert Stein, further belatedly edited by Sam Rose
"""
import logging

import astropy.time
import numpy as np
import pandas as pd
from astropy import units as u
from astropy.coordinates import AltAz, SkyCoord
from astropy.time import Time
from astropy.utils.masked import Masked

from wintertoo.data import PALOMAR_LOC, palomar_observer

logger = logging.getLogger(__name__)

MINIMUM_ELEVATION = 20.0


def get_alt_az(times_mjd: list, ra: float, dec: float) -> tuple:
    """
    Get alt and az for a target at various times in decimal degrees
    :param times_mjd: list of times
    :param ra: ra
    :param dec: dec
    :return: alt array, and az array
    """
    loc = SkyCoord(ra=ra, dec=dec, frame="icrs")
    time = Time(times_mjd, format="mjd")
    altaz = loc.transform_to(AltAz(obstime=time, location=PALOMAR_LOC))
    degs = SkyCoord(altaz.az, altaz.alt, frame="icrs")
    alt_array = degs.dec.degree
    az_array = degs.ra.degree
    return alt_array, az_array


def get_night_times(time_mjd: astropy.time.Time):
    """
    Get an array of times which cover the night of the date given.

    Parameters
    ----------
    time_mjd : astropy.time.Time
        date in MJD (median Julian Date), e.g. 59480 (Sept 23)

    Returns
    -------
    time_array : numpy array
        array of times during the night

    """
    time = Time(time_mjd, format="mjd")

    # Rise/fade can fail if target is close to a bin edge
    sun_rise_next = palomar_observer.sun_rise_time(time, which="next")
    sun_set_next = palomar_observer.sun_set_time(time, which="next")
    sun_set_prev = palomar_observer.sun_set_time(time, which="previous")

    if isinstance(sun_rise_next.value, Masked):
        sun_rise_next = palomar_observer.sun_rise_time(
            time - 0.05 * u.day, which="next"
        )

    if isinstance(sun_set_next.value, Masked):
        sun_set_next = palomar_observer.sun_set_time(time - 0.05 * u.day, which="next")

    if isinstance(sun_set_prev.value, Masked):
        sun_set_prev = palomar_observer.sun_set_time(
            time + 0.05 * u.day, which="previous"
        )

    until_next_sunset = sun_set_next.jd - time.jd
    until_next_sunrise = sun_rise_next.jd - time.jd

    if until_next_sunrise < until_next_sunset:
        # this is the case where time is during the night
        time_array = np.linspace(sun_set_prev.jd, sun_rise_next.jd, 100)
    else:
        # this is the case where time is during the day
        time_array = np.linspace(sun_set_next.jd, sun_rise_next.jd, 100)

    return time_array


def up_tonight(time_mjd: astropy.time.Time, ra: str, dec: str) -> tuple[bool, str]:
    """
    what is up (above altitude 20 deg) in a given night?
    date in MJD (median Julian Date), e.g. 59480 (Sept 23)
    ra (right ascension) in hours, minutes, seconds, e.g. '+19h50m41s'
    dec (declination) in hours, minutes, seconds, e.g. '+08d50m58s'
    :param time_mjd: time in mjd
    :param ra: ra of target
    :param dec: dec of target
    :return:
    """
    loc = SkyCoord(ra=ra, dec=dec, frame="icrs")
    time_array = get_night_times(time_mjd)
    time = Time(time_mjd, format="mjd")

    altaz = loc.transform_to(
        AltAz(obstime=Time(time_array, format="jd"), location=PALOMAR_LOC)
    )
    df = pd.DataFrame(data={"time": time_array, "alt": altaz.alt})
    df = df[df["alt"] >= MINIMUM_ELEVATION]

    time_up = 0
    if len(df) > 0:
        try:
            time_up = df["time"].iloc[-1] - df["time"].iloc[0]
        except KeyError:
            pass

    if time_up > 0:
        if time.jd > df["time"].iloc[-1]:
            is_available = (
                f"Object is up between UTC "
                f'{Time(df["time"].iloc[0]+1, format="jd").isot} '
                f'and {Time(df["time"].iloc[-1]+1, format="jd").isot}'
            )
            avail_bool = True

        else:
            is_available = (
                f"Object is up between UTC "
                f'{Time(df["time"].iloc[0], format="jd").isot} '
                f'and {Time(df["time"].iloc[-1], format="jd").isot}'
            )
            avail_bool = True
    else:
        is_available = "Object is not up"
        avail_bool = False

    return avail_bool, is_available


def get_date(time: Time) -> int:
    """
    Get the date from a time object

    :param time: Time object
    :return: date as an integer
    """
    return int(str(time).split(" ", maxsplit=1)[0].replace("-", ""))
