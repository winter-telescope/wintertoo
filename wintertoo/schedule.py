import pandas as pd
import os
import numpy as np
from astropy.time import Time
from astropy import units as u
import logging
from wintertoo.data import summer_filters, too_db_schedule_config, get_default_value
from wintertoo.make_request import make_too_request_from_df
from wintertoo.fields import get_best_summer_field
from wintertoo.validate import validate_schedule_df, validate_target_priority, calculate_overall_priority

logger = logging.getLogger(__name__)


def to_date_string(
        time: Time
):
    return time.isot.split("T")[0]


def build_schedule(
        ra_degs: list,
        dec_degs: list,
        field_ids: list,
        program_name: str,
        pi: str,
        program_priority: float = 0.,
        filters: list = None,
        texp: float = get_default_value("visitExpTime"),
        nexp: int = 1,
        dither_bool: bool = get_default_value("dither"),
        dither_distance: float = get_default_value("ditherStepSize"),
        maximum_airmass: float = get_default_value("maxAirmass"),
        nights: list = None,
        target_priorities: list = None,
        t_0: Time = None,
        csv_save_file: str = None,
):

    if nights is None:
        nights = list([1, 2, 3])
    if filters is None:
        filters = summer_filters
    if t_0 is None:
        t_0 = Time.now()

    schedule = pd.DataFrame()

    for night in nights:
        start_date = t_0 + (night-1)*u.day
        end_date = t_0 + (night*u.day)

        for i, ra_deg in enumerate(ra_degs):
            dec_deg = dec_degs[i]
            field_id = field_ids[i]

            priority = calculate_overall_priority(
                target_priority=target_priorities[i],
                program_base_priority=program_priority
            )

            for f in filters:
                for _ in range(nexp):
                    schedule = schedule.append({
                        "fieldRA": np.radians(ra_deg),
                        "fieldDec": np.radians(dec_deg),
                        "fieldID": field_id,
                        "azimuth": -100,
                        "altitude": -100,
                        "filter": f,
                        "visitExpTime": texp,
                        "priority": priority,
                        "programPI": pi,
                        "progName": program_name,
                        "validStart": start_date.mjd,
                        "validStop": end_date.mjd,
                        "observed": False,
                        "maxAirmass": maximum_airmass,
                        "dither": dither_bool,
                        "ditherStepSize": dither_distance,
                    }, ignore_index=True)

    schedule = schedule.astype({
        "dither": bool,
        "observed": bool
    })

    schedule["obsHistID"] = range(len(schedule))
    schedule["requestID"] = range(len(schedule))

    validate_schedule_df(schedule)

    if csv_save_file is not None:
        logger.info(f"Saving schedule to {csv_save_file}")
        schedule.to_csv(csv_save_file, index=False)
    return schedule


def make_schedule(
        ra_degs: list,
        dec_degs: list,
        field_ids: list,
        target_priorities: list,
        program_name: str,
        pi: str,
        program_priority: float = 0.,
        filters: list = None,
        t_exp: float = get_default_value("visitExpTime"),
        n_exp: int = 1,
        dither_bool: bool = get_default_value("dither"),
        dither_distance: float = get_default_value("ditherStepSize"),
        maximum_airmass: float = get_default_value("maxAirmass"),
        nights: list = None,
        t_0: Time = None,
        csv_save_file: str = None,
):
    schedule = build_schedule(
        ra_degs=ra_degs,
        dec_degs=dec_degs,
        field_ids=field_ids,
        target_priorities=target_priorities,
        program_name=program_name,
        pi=pi,
        program_priority=program_priority,
        filters=filters,
        texp=t_exp,
        nexp=n_exp,
        dither_bool=dither_bool,
        dither_distance=dither_distance,
        maximum_airmass=maximum_airmass,
        nights=nights,
        t_0=t_0,
        csv_save_file=csv_save_file,
    )

    return schedule


def schedule_ra_dec(
        ra_deg: float,
        dec_deg: float,
        pi: str,
        program_name: str,
        target_priority: float = 1.,
        filters: list = None,
        t_exp: float = get_default_value("visitExpTime"),
        n_exp: int = 1,
        dither_bool: bool = get_default_value("dither"),
        dither_distance: float = get_default_value("ditherStepSize"),
        maximum_airmass: float = get_default_value("maxAirmass"),
        nights=[1],
        t_0=None,
        summer: bool = True,
        use_field: bool = True,
        csv_save_file: str = None,
):

    if summer:
        get_best_field = get_best_summer_field
    else:
        raise NotImplementedError

    # Take RA/Dec and select nearest-centered field

    if use_field:
        best_field = get_best_field(ra_deg, dec_deg)
        ra_deg = best_field["RA"]
        dec_deg = best_field["Dec"]
        field_id = best_field["#ID"]
    else:
        field_id = get_default_value("fieldID")

    schedule = make_schedule(
        ra_degs=[ra_deg],
        dec_degs=[dec_deg],
        field_ids=[field_id],
        target_priorities=[target_priority],
        filters=filters,
        t_exp=t_exp,
        n_exp=n_exp,
        dither_bool=dither_bool,
        dither_distance=dither_distance,
        nights=nights,
        t_0=t_0,
        pi=pi,
        program_name=program_name,
        csv_save_file=csv_save_file
    )

    return schedule

