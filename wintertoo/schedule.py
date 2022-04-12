import pandas as pd
import os
from astropy.time import Time
from astropy import units as u
import logging
from nuwinter.paths import winter_schedule_dir
from nuwinter.data import base_prog_id, summer_filters, too_schedule_config
from wintertoo.make_request import make_too_request_from_file


logger = logging.getLogger(__name__)


def to_date_string(
        time: Time
):
    return time.isot.split("T")[0]


def build_schedule(
        schedule_name,
        ra_degs: list,
        dec_degs: list,
        prog_id: str,
        pi: str,
        filters: list = None,
        texp: float = 300,
        nexp: int = 1,
        dither_bool: bool = True,
        dither_distance="",
        maximum_airmass: float = 1.5,
        maximum_seeing: float = 3.0,
        nights: list = None,
        t_0: Time = None,
        save: bool = True
):

    if nights is None:
        nights = list([1, 2, 3])
    if filters is None:
        filters = summer_filters
    if t_0 is None:
        t_0 = Time.now()

    schedule = pd.DataFrame()

    for night in nights:
        start_date = to_date_string(t_0 + (night-1)*u.day)
        end_date = to_date_string(t_0 + (night*u.day))

        for i, ra_deg in enumerate(ra_degs):
            dec_deg = dec_degs[i]

            for f in filters:
                schedule = schedule.append({
                    "RA_deg": ra_deg,
                    "Dec_deg": dec_deg,
                    "Filter": f,
                    "Texp": texp,
                    "Nexp": nexp,
                    "Dither?": ["n", "y"][dither_bool],
                    "Dither distance": dither_distance,
                    "PI": pi,
                    "propID": prog_id,
                    "Earliest UT Date": start_date,
                    "UT Start Time": "00:00:00.02",
                    "Latest UT Date": end_date,
                    "UT Finish Time": "00:00:00.01",
                    "Maximum Airmass": maximum_airmass,
                    "Maximum Seeing": maximum_seeing
                }, ignore_index=True)

    schedule = schedule.astype({"Nexp": int})

    out_path = os.path.join(
        winter_schedule_dir,
        f"{schedule_name}.csv"
    )

    if save:
        logger.info(f"Saving schedule to {out_path}")
        schedule.to_csv(out_path, index=False)
    return schedule


def make_schedule(
        schedule_name,
        ra_degs: list,
        dec_degs: list,
        prog_id: str = base_prog_id,
        pi: str = "Somebody",
        filters: list = None,
        texp: float = 300,
        nexp: int = 1,
        dither_bool: bool = True,
        dither_distance="",
        maximum_airmass: float = 1.5,
        maximum_seeing: float = 3.0,
        nights: list = None,
        t_0: Time = None,
        save: bool = True,
        submit: bool = False
):
    schedule = build_schedule(
        schedule_name=schedule_name,
        ra_degs=ra_degs,
        dec_degs=dec_degs,
        prog_id=prog_id,
        pi=pi,
        filters=filters,
        texp=texp,
        nexp=nexp,
        dither_bool=dither_bool,
        dither_distance=dither_distance,
        maximum_seeing=maximum_seeing,
        maximum_airmass=maximum_airmass,
        nights=nights,
        t_0=t_0,
        save=save
    )

    if submit:

        make_too_request_from_file(
            too_file_path=csv_path,
            save_path=csv_path.replace(".csv", ".db"),
            config_path=too_schedule_config
        )

    return schedule

def schedule_ra_dec(
        schedule_name: str,
        ra_deg: float,
        dec_deg: float,
        pi: str,
        prog_id: str,
        filters: list = summer_filters,
        texp: float = 300.,
        nexp: int = 1,
        dither_bool: bool = True,
        dither_distance="",
        nights=[1],
        t_0=None,
        summer: bool = True,
        use_field: bool = True,
        submit: bool = False
):
    if use_field:
        best_field = get_best_field(res["candidate"]["ra"], res["candidate"]["dec"])
        ra_deg = best_field["RA"]
        dec_deg = best_field["Dec"]

    schedule = make_schedule(
        schedule_name=schedule_name,
        ra_degs=[ra_deg],
        dec_degs=[dec_deg],
        filters=filters,
        texp=texp,
        nexp=nexp,
        dither_bool=dither_bool,
        dither_distance=dither_distance,
        nights=nights,
        t_0=t_0,
        pi=pi,
        prog_id=prog_id,
        submit=submit
    )

