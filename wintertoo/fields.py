"""
Module for handling field-related functions
"""
import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from matplotlib.axes import Axes

from wintertoo.data import summer_fields

logger = logging.getLogger(__name__)

BASE_SUMMER_WIDTH_DEG = 0.25


def get_summer_fields_in_box(ra_lim: tuple, dec_lim: tuple) -> pd.DataFrame:
    """
    Return all SUMMER fields within a particular rectangle

    :param ra_lim: tuple of lower, upper RA values
    :param dec_lim: tuple of lower, upper dec values
    :return: dataframe of fields within the rectangle
    """
    res = summer_fields.query(
        f"(RA > {ra_lim[0]}) and (RA < {ra_lim[1]}) "
        f"and (Dec > {dec_lim[0]}) and (Dec < {dec_lim[1]})"
    )
    return res


def get_overlapping_summer_fields(ra_deg: float, dec_deg: float) -> pd.DataFrame:
    """
    Get all SUMMER fields overlapping a particular RA/dec

    :param ra_deg: Ra
    :param dec_deg: dec
    :return: dataframe of overlaping fields
    """
    summer_width = BASE_SUMMER_WIDTH_DEG / np.cos(np.radians(dec_deg))

    res = summer_fields.query(
        f"(RA > {ra_deg - 0.5 * summer_width}) and "
        f"(RA < {ra_deg + 0.5 * summer_width}) and "
        f"(Dec > {dec_deg - 0.5 * summer_width}) and "
        f"(Dec < {dec_deg + 0.5 * summer_width})"
    )

    logger.info(f"Found {len(res)} overlapping fields.")

    return res


def get_best_summer_field(ra_deg, dec_deg, make_plot: bool = False) -> pd.Series:
    """
    Get the 'best' summer field for a given ra/dec,
    where best is defined as the field with a center closest to the value

    :param ra_deg: ra
    :param dec_deg: dec
    :param make_plot: make a plot of the overlap
    :return: best field
    """
    res = get_overlapping_summer_fields(ra_deg, dec_deg)

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
        plot_overlapping_summer_fields(res, ra_deg, dec_deg, closest)

    return closest.iloc[0]


def plot_field_rectangles(ax: Axes, field_df: pd.DataFrame, color: str = "k"):
    """
    Function to plot field contours

    :param ax: axis
    :param field_df: dataframe of fields
    :param color: color for the field edge color
    :return: None
    """

    for _, row in field_df.iterrows():
        summer_width_deg = BASE_SUMMER_WIDTH_DEG / np.cos(np.radians(row["Dec"]))
        rectangle = plt.Rectangle(
            (row["RA"] - 0.5 * summer_width_deg, row["Dec"] - 0.5 * summer_width_deg),
            summer_width_deg,
            summer_width_deg,
            fc="none",
            ec=color,
        )
        ax.add_patch(rectangle)


def plot_summer_fields(field_df: pd.DataFrame, ra_lim: tuple, dec_lim: tuple) -> Axes:
    """
    Plot summer fields within a rectangle

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

    plot_field_rectangles(ax, field_df)

    return ax


def plot_overlapping_summer_fields(
    field_df: pd.DataFrame,
    ra_deg: float,
    dec_deg: float,
    closest: pd.DataFrame = None,
) -> Axes:
    """
    Plot summer fields overlapping a given ra/dex

    :param field_df: field dataframe
    :param ra_deg: ra
    :param dec_deg: dec
    :param closest: closest field
    :return:
    """
    ax = plt.subplot(111)
    plt.scatter(ra_deg, dec_deg, marker="*")

    plot_field_rectangles(ax, field_df)

    if closest is not None:
        plot_field_rectangles(ax, closest, color="r")

    return ax
