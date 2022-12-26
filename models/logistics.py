# https://github.com/hubbub-tech/rent-server/blob/e86cafc43caf56458b4f2998650a224439c2fc55/src/models/logistics/logistics.py
from blubber_orm import Models
from datetime import datetime


class Logistics(Models):

    table_name = "logistics"
    table_primaries = ["id"]
    sensitive_attributes = []

    def __init__(self, attrs):
        self.id = attrs["id"]
        self.notes = attrs["notes"]
        self.is_canceled = attrs["is_canceled"]
        self.dt_created = attrs["dt_created"]

        self.dt_sent = attrs["dt_sent"]
        self.dt_received = attrs["dt_received"]

        self.sender_id = attrs["sender_id"]
        self.receiver_id = attrs["receiver_id"]

        self.from_addr_lat = attrs["from_addr_lat"]
        self.from_addr_lng = attrs["from_addr_lng"]

        self.to_addr_lat = attrs["to_addr_lat"]
        self.to_addr_lng = attrs["to_addr_lng"]


    def to_query_address(self, direction):
        direction = direction.lower()
        assert direction in ["from", "to"], "Error: select a valid direction ['from', 'to']"

        if direction == "from":
            query_address = {
                "lat": self.from_addr_lat,
                "lng": self.from_addr_lng
            }
        elif direction == "to":
            query_address = {
                "lat": self.to_addr_lat,
                "lng": self.to_addr_lng
            }
        else: raise Exception("Error: Invalid logistics direction.")

        return query_address


    def get_order_ids(self):
        SQL = """
            SELECT order_id
            FROM order_logistics
            WHERE logistics_id = %s;
            """

        data = (self.id,)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            order_ids = cursor.fetchall()
            order_ids = [order_id for order_t in order_ids for order_id in order_t]

        return order_ids


    def get_courier_ids(self):
        SQL = """
            SELECT courier_id
            FROM logistics_couriers
            WHERE logistics_id = %s;
            """

        data = (self.id,)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            courier_ids = cursor.fetchall()
            courier_ids = [courier_id for courier_t in courier_ids for courier_id in courier_t]

        return courier_ids


    def confirm_sent(self):
        self.set({"id": self.id}, {
            "dt_sent": datetime.now()
        })


    def confirm_received(self):
        self.set({"id": self.id}, {
            "dt_received": datetime.now()
        })


    def get_timeslots(self):
        SQL = """
            SELECT dt_range_start, dt_range_end
            FROM timeslots
            WHERE logistics_id = %s;
            """

        data = (self.id,)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            return cursor.fetchall()


    def get_eta(self):
        SQL = """
            SELECT dt_range_start, dt_range_end
            FROM timeslots
            WHERE logistics_id = %s AND is_sched = %s;
            """

        data = (self.id, True)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            dt_eta = cursor.fetchone()

            if dt_eta: dt_eta = dt_eta[0]

        return dt_eta


    def add_order(self, order_id: int):
        order_ids = self.get_order_ids()
        if order_id in order_ids: return

        SQL = """
            INSERT
            INTO order_logistics (order_id, logistics_id)
            VALUES (%s, %s)
            """

        data = (order_id, self.id)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            Models.db.conn.commit()


    def remove_order(self, order_id: int):
        # We want both of these commands to succeed or fail together
        order_ids = self.get_order_ids()
        if order_id not in order_ids: return

        SQL = """
            DELETE
            FROM order_logistics
            WHERE order_id = %s AND logistics_id = %s;
            """
        data = (order_id, self.id)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            Models.db.conn.commit()


    def add_courier(self, courier_id: int):
        courier_ids = self.get_courier_ids()
        if courier_id in courier_ids: return

        SQL = """
            INSERT
            INTO logistics_couriers (logistics_id, courier_id)
            VALUES (%s, %s)
            """

        data = (self.id, courier_id)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            Models.db.conn.commit()


    def remove_courier(self, courier_id: int):
        # We want both of these commands to succeed or fail together
        courier_ids = self.get_courier_ids()
        if courier_id not in courier_ids: return

        SQL = """
            DELETE
            FROM logistics_couriers
            WHERE courier_id = %s AND logistics_id = %s;
            """
        data = (courier_id, self.id)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            Models.db.conn.commit()
