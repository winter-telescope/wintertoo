"""
Module for testing submission of a schedule
"""
import logging
import os
import unittest
from datetime import date

import pandas as pd
from astropy.time import Time

from wintertoo.models import Program, SummerFieldToO, SummerRaDecToO
from wintertoo.schedule import concat_toos, schedule_field, schedule_ra_dec
from wintertoo.submit import export_schedule_to_sqlitedb
from wintertoo.validate import (
    validate_obshist,
    validate_schedule_df,
    validate_target_dates,
    validate_target_pi,
    validate_target_priority,
    validate_target_visibility,
)

logger = logging.getLogger(__name__)

test_data_dir = os.path.join(os.path.dirname(__file__), "testdata")
test_json_path = os.path.join(test_data_dir, "test_schedule.json")
test_df = pd.read_json(test_json_path)

program = Program(
    pi_name="Stein",
    progname="2021A000",
    prog_key="763244309190298696786072636901190268976229595667748695826878",
    maxpriority=100,
    startdate=date(2021, 1, 1),
    enddate=date(2023, 12, 31),
)


class TestSchedule(unittest.TestCase):
    """
    Class for schedule testing
    """

    def test_validate_json(self):
        """
        Test validation of json

        :return: None
        """
        logger.info("Testing the validation with a test json")
        validate_schedule_df(test_df)

    def test_generate_schedule(self):
        """
        Test generating a schedule

        :return: None
        """
        logger.info("Testing schedule generation")

        schedule = schedule_ra_dec(
            too=SummerRaDecToO(
                ra_deg=173.7056754,
                dec_deg=11.253441,
                start_time_mjd=62721.1894969287,
                end_time_mjd=62722.1894969452,
            ),
            program=program,
        )

        # Uncomment to generate a new test json
        # schedule.to_json(test_json_path)

        validate_target_visibility(schedule)

        comp = pd.read_json(schedule.to_json())  # pylint: disable=no-member
        self.assertEqual(test_df.to_json(), comp.to_json())  # pylint: disable=no-member

        schedule = schedule_ra_dec(
            too=SummerRaDecToO(
                ra_deg=173.7056754,
                dec_deg=11.253441,
            ),
            program=program,
        )

        validate_schedule_df(schedule)
        validate_obshist(schedule)

        validate_target_priority(schedule=schedule, max_priority=program.maxpriority)

        program_start_date = Time(str(program.startdate), format="isot")

        program_end_date = Time(str(program.enddate), format="isot")

        validate_target_dates(
            schedule,
            program_start_date=program_start_date,
            program_end_date=program_end_date,
        )
        validate_target_pi(schedule, prog_pi=program.pi_name)

        export_schedule_to_sqlitedb(schedule, "test_schedule.db")

    def test_schedule_utils(self):
        """
        Test generating a schedule

        :return: None
        """
        logger.info("Testing schedule util functions")

        field_too = SummerFieldToO(
            field_id=1,
        )

        schedule_field(
            field_too,
            program=program,
            csv_save_file="test_schedule.csv",
        )

        concat_toos(
            [field_too, SummerRaDecToO(ra_deg=173.7056754, dec_deg=11.253441)],
            program=program,
        )
