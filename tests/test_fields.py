"""
Module for testing submission of a schedule
"""

import logging
import unittest

from wintertoo.fields import get_best_field, get_field_info, get_fields_in_box

logger = logging.getLogger(__name__)


class TestField(unittest.TestCase):
    """
    Class for schedule testing
    """

    def test_get_fields_in_box(self):
        """
        Test getting fields in box

        :return: None
        """
        logger.info("Testing getting fields in box")

        ra_deg = 210.910674637
        dec_deg = 54.3116510708

        width = 0.7

        ra_lim = (ra_deg - width, ra_deg + width)
        dec_lim = (dec_deg - width, dec_deg + width)

        fields = get_fields_in_box(ra_lim, dec_lim, summer=True)

        assert len(fields) == 28, f"Wrong number of fields ({len(fields)})"
        assert fields["ID"].iloc[0] == 54494, f"Wrong field {fields['ID'].iloc[0]}"

        fields = get_fields_in_box(ra_lim, dec_lim, summer=False)

        assert len(fields) == 3, f"Wrong number of fields ({len(fields)})"
        assert fields["ID"].iloc[0] == 3735, f"Wrong field {fields['ID'].iloc[0]}"

    def test_get_field_info(self):
        """
        Test getting field info

        :return: None
        """
        get_field_info(55286, summer=True)
        get_field_info(3735, summer=False)

    def test_get_best_field(self):
        """
        Test getting best field

        :return: None
        """
        get_best_field(210.910674637, 54.3116510708, summer=True, make_plot=True)
