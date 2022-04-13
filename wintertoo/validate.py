import logging
import numpy as np
from jsonschema import validate, ValidationError
from wintertoo.data import too_schedule_config

logger = logging.getLogger(__name__)


def validate_schedule_json(
    data: dict
):
    try:
        validate(data, schema=too_schedule_config)
        logger.info("Successfully validated schema")
    except ValidationError as e:
        logger.error(e)
        raise


def validate_pi(
        program_name: str,
        pi: str
):
    return True


def validate_program_dates(start_time, stop_time, program_details):
    program_start_date = program_details[3]
    program_end_date = program_details[4]
    valid = 0
    if np.logical_or((start_time < program_start_date), (stop_time > program_end_date)):
        valid = -99

    return valid


