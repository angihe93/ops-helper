# https://github.com/hubbub-tech/rent-server/blob/e86cafc43caf56458b4f2998650a224439c2fc55/src/models/logistics/timeslots.py
from blubber_orm import Models


class Timeslots(Models):


    table_name = "timeslots"
    table_primaries = ["logistics_id", "dt_range_start", "dt_range_end"]
    sensitive_attributes = []


    def __init__(self, attrs):
        self.logistics_id = attrs["logistics_id"]
        self.dt_range_start = attrs["dt_range_start"]
        self.dt_range_end = attrs["dt_range_end"]
        self.is_sched = attrs["is_sched"]
        self.dt_sched_eta = attrs["dt_sched_eta"]

    @classmethod
    def get_is_sched(cls, id, res_date_start, res_date_end):
        SQL = """
            SELECT is_sched
            FROM timeslots
            WHERE logistics_id = %s AND DATE(dt_range_start) = %s AND DATE(dt_range_end) = %s;
        """

        data = (id, res_date_start, res_date_end)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            value = cursor.fetchall()
            print(value)
            return value
