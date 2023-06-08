#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 25 13:51:59 2022
@author: frostig, belatedly edited by Robert Stein
"""
import logging
from typing import Union

import astropy.time
import numpy as np
import pandas as pd
from astropy.coordinates import AltAz, SkyCoord
from astropy.time import Time

from wintertoo.data import PALOMAR_LOC, palomar_observer
from wintertoo.models.too import Summer, Winter

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
    time = Time(time_mjd, format="mjd")
    sun_rise = palomar_observer.sun_rise_time(time, which="previous")
    sun_set = palomar_observer.sun_set_time(time, which="next")
    night = sun_set.jd - sun_rise.jd
    if night >= 1:
        # if next day, subtract a day
        time_array = np.linspace(sun_set.jd, sun_set.jd + (night - 1), 100)
    else:
        time_array = np.linspace(sun_set.jd, sun_set.jd + night, 100)

    altaz = loc.transform_to(
        AltAz(obstime=Time(time_array, format="jd"), location=PALOMAR_LOC)
    )
    df = pd.DataFrame(data={"time": time_array, "alt": altaz.alt})
    df = df[df["alt"] >= MINIMUM_ELEVATION]

    try:
        time_up = df["time"].iloc[-1] - df["time"].iloc[0]
    except KeyError:
        time_up = 0

    if time_up > 0:
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


def is_summer(too: Union[Winter, Summer]) -> bool:
    """
    Checks a ToO Request to ensure it is either a Summer or Winter request

    :param too: ToO request
    :return: boolean
    """
    if isinstance(too, Summer):
        return True
    if isinstance(too, Winter):
        return False

    err = f"Unrecognised ToO type {type(too)}"
    logger.error(err)
    raise TypeError(err)


def get_date(time: Time) -> int:
    """
    Get the date from a time object

    :param time: Time object
    :return: date as an integer
    """
    return int(str(time).split(" ", maxsplit=1)[0].replace("-", ""))
