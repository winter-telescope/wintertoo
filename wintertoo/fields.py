"""
Module for handling field-related functions
"""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from matplotlib.axes import Axes

from wintertoo.data import (
    SUMMER_BASE_WIDTH,
    WINTER_BASE_WIDTH,
    summer_fields,
    winter_fields,
)

logger = logging.getLogger(__name__)


def get_fields(summer: bool = False) -> pd.DataFrame:
    """
    Get field table for either summer or winter
    :param summer: boolean whether to use summer grid
    :return: field dataframe
    """
    if summer:
        field_df = summer_fields
    else:
        field_df = winter_fields
    return field_df


def get_base_width(summer: bool = False) -> float:
    """
    Get base width of field
    :param summer: boolean whether to use summer (or winter)
    :return: width in deg
    """
    return SUMMER_BASE_WIDTH if summer else WINTER_BASE_WIDTH


def get_field_info(field_id: int, summer: bool = False) -> pd.Series:
    """
    Get info from field table for a particular field ID
    :param field_id: ID of field
    :param summer: boolean whether to use summer field table
    :return: Series for matching field
    """

    field_df = get_fields(summer=summer)

    field_mask = field_df["ID"].to_numpy(dtype=int) == field_id
    if np.sum(field_mask) == 0:
        err = f"Could not find field {field_id}"
        logger.error(err)
        raise KeyError(err)

    assert np.sum(field_mask) == 1

    return field_df.copy()[field_mask]


def get_fields_in_box(
    ra_lim: tuple, dec_lim: tuple, summer: bool = False
) -> pd.DataFrame:
    """
    Return all fields within a particular rectangle
    :param ra_lim: tuple of lower, upper RA values
    :param dec_lim: tuple of lower, upper dec values
    :param summer: boolean to use SUMMER grid rather than WINTER
    :return: dataframe of fields within the rectangle
    """

    field_df = get_fields(summer=summer)
    base_width = 0.5 * get_base_width(summer=summer)

    res = field_df.query(
        f"(RA > {ra_lim[0] - base_width}) and (RA < {ra_lim[1] + base_width}) "
        f"and (Dec > {dec_lim[0] - base_width}) and (Dec < {dec_lim[1] + base_width})"
    )
    return res


def get_overlapping_fields(
    ra_deg: float, dec_deg: float, summer: bool = False
) -> pd.DataFrame:
    """
    Get all fields overlapping a particular RA/dec
    :param ra_deg: Ra
    :param dec_deg: dec
    :param summer: boolean whether to use summer field grid
    :return: dataframe of overlapping fields
    """

    width = get_base_width(summer=summer) / np.cos(np.radians(dec_deg))

    field_df = get_fields(summer=summer)

    res = field_df.query(
        f"(RA > {ra_deg - 0.5 * width}) and "
        f"(RA < {ra_deg + 0.5 * width}) and "
        f"(Dec > {dec_deg - 0.5 * width}) and "
        f"(Dec < {dec_deg + 0.5 * width})"
    )

    logger.info(f"Found {len(res)} overlapping fields.")

    return res


def plot_field_rectangles(
    ax: Axes, field_df: pd.DataFrame, color: str = "k", summer: bool = False
):
    """
    Function to plot field contours
    :param ax: axis
    :param field_df: dataframe of fields
    :param color: color for the field edge color
    :param summer: Boolean whether to use summer field grid
    :return: None
    """

    base_width = get_base_width(summer=summer)

    for _, row in field_df.iterrows():
        width_deg = base_width / np.cos(np.radians(row["Dec"]))
        rectangle = plt.Rectangle(
            (row["RA"] - 0.5 * width_deg, row["Dec"] - 0.5 * width_deg),
            width_deg,
            width_deg,
            fc="none",
            ec=color,
        )
        ax.add_patch(rectangle)


def plot_overlapping_fields(
    field_df: pd.DataFrame,
    ra_deg: float,
    dec_deg: float,
    summer: bool = False,
    closest: pd.DataFrame = None,
) -> Axes:
    """
    Plot summer fields overlapping a given ra/dex
    :param field_df: field dataframe
    :param ra_deg: ra
    :param dec_deg: dec
    :param summer: boolean whether to use summer field grid
    :param closest: the closest field
    :return: ax
    """
    ax = plt.subplot(111)
    plt.scatter(ra_deg, dec_deg, marker="*")

    plot_field_rectangles(ax, field_df, summer=summer)

    if closest is not None:
        plot_field_rectangles(ax, closest, color="r")

    return ax


def get_best_field(
    ra_deg, dec_deg, summer: bool = False, make_plot: bool = False
) -> pd.Series:
    """
    Get the 'best' summer field for a given ra/dec,
    where best is defined as the field with a center closest to the value
    :param ra_deg: ra
    :param dec_deg: dec
    :param summer: boolean whether to use summer field grid
    :param make_plot: make a plot of the overlap
    :return: best field
    """
    res = get_overlapping_fields(ra_deg, dec_deg, summer=summer)

    sky_pos = SkyCoord(ra_deg, dec_deg, unit="deg")

    dists = np.array(
        [
            sky_pos.separation(SkyCoord(x["RA"], x["Dec"], unit="deg")).value
            for _, x in res.iterrows()
        ]
    )

    closest_mask = dists == np.min(dists)

    closest = res[closest_mask]

    logger.info(f"Best is field {int(closest.iloc[0]['ID'])}")

    if make_plot:
        plot_overlapping_fields(res, ra_deg, dec_deg, summer=summer, closest=closest)

    return closest.iloc[0]


def plot_fields(
    field_df: pd.DataFrame, ra_lim: tuple, dec_lim: tuple, summer: bool = False
) -> Axes:
    """
    Plot fields within a rectangle
    :param field_df: dataframe of fields
    :param ra_lim: tuple of lower, upper ra values
    :param dec_lim: tuple of lower, upper dec values
    :return: Matplotlib ax
    """
    ax = plt.subplot(111)
    plt.scatter(field_df["RA"], field_df["Dec"], marker="+")

    rectangle = plt.Rectangle(
        (ra_lim[0], dec_lim[0]),
        (ra_lim[1] - ra_lim[0]),
        (dec_lim[1] - dec_lim[0]),
        fc="red",
        alpha=0.2,
    )
    ax.add_patch(rectangle)

    plot_field_rectangles(ax, field_df, summer=summer)

    return ax
