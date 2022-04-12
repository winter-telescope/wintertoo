import pandas as pd
import os

data_dir = os.path.dirname(__file__)

summer_fields_path = os.path.join(data_dir, "summer_fields.txt")
summer_fields = pd.read_csv(summer_fields_path, sep='\s+')

summer_filters = ["u", "g", "r", "i"]

too_schedule_config = os.path.join(data_dir, "scheduleconfig.json")
