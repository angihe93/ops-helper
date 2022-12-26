from datetime import datetime
from blubber_orm import Models
from blubber_orm.models._conn import Blubber

class Items(Models):
    """
    A class to define the use of the Items type from Hubbub Shop's relational database.
    Create, read, update, destroy have been implemented by the Models class.

    """

    table_name = "items"
    table_primaries = ["id"]
    sensitive_attributes = []

    def __init__(self, attrs: dict):
        self.id = attrs["id"]
        self.name = attrs["name"]
        # self.retail_price = attrs["retail_price"]
        # self.is_visible = attrs["is_visible"]
        # self.is_transactable = attrs["is_transactable"]
        # self.is_featured = attrs["is_featured"]
        # self.dt_created = attrs["dt_created"]
        # self.is_locked = attrs["is_locked"]
        # self.locker_id = attrs["locker_id"]
        # self.description = attrs["description"]
        # self.weight = attrs["weight"]
        # self.weight_unit = attrs["weight_unit"]
        # self.dim_height = attrs["dim_height"]
        # self.dim_length = attrs["dim_length"]
        # self.dim_width = attrs["dim_width"]
        # self.dim_unit = attrs["dim_unit"]
        # self.lister_id = attrs["lister_id"]

        self.address_lat = attrs["address_lat"]
        self.address_lng = attrs["address_lng"]
        self.address_formatted = attrs["address_formatted"]


    def lock(self, user: Models):
        assert isinstance(user, Models), "user must be a child of Models"
        assert user.table_name == "users", "Model must be type Users."

        SQL = """
            UPDATE items
            SET is_locked = %s, locker_id = %s
            WHERE id = %s;
            """

        data = (True, user.id, self.id)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            Models.db.conn.commit()

        self.is_locked = True
        self.locker_id = user.id


    def unlock(self):
        SQL = """
            UPDATE items
            SET is_locked = %s, locker_id = %s
            WHERE id = %s;
            """

        data = (False, None, self.id)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            Models.db.conn.commit()

        self.is_locked = False
        self.locker_id = None


    def get_tags(self):
        SQL = """
            SELECT title
            FROM item_tags
            WHERE item_id = %s;
            """

        data = (self.id,)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            tags = cursor.fetchall()
            tags = [tag for tag_t in tags for tag in tag_t]

        return tags


    def add_tag(self, tag: Models):
        assert isinstance(tag, Models), "tag must be a child of Models"
        assert tag.table_name == "tags", "Model must be type Tags"

        tag_titles = self.get_tags()
        if tag.title in tag_titles: return

        SQL = """
            INSERT
            INTO item_tags (item_id, title)
            VALUES (%s, %s);
            """

        data = (self.id, tag.title)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            Models.db.conn.commit()


    def remove_tag(self, tag: Models):
        assert isinstance(tag, Models), "tag must be a child of Models"
        assert tag.table_name == "tags", "Model must be type Tags"

        tag_titles = self.get_tags()
        if tag.title not in tag_titles: return

        SQL = """
            DELETE
            FROM item_tags
            WHERE item_id = %s AND title = %s;
            """

        data = (self.id, tag.title)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            Models.db.conn.commit()


    @classmethod
    def get_by(cls, availability: dict=None):
        if availability:
            assert isinstance(availability, dict), "Availability must be a dictionary."
            if availability.get("dt_lbound") is None:
                availability["dt_lbound"] = datetime.min
            if availability.get("dt_ubound") is None:
                availability["dt_ubound"] = datetime.max

            if availability["dt_lbound"] == None or \
                availability["dt_ubound"] == None:

                return cls.filter({"is_visible": True, "is_transactable": True})

            if availability["dt_lbound"] == datetime.min and \
                availability["dt_ubound"] == datetime.max:

                return cls.filter({"is_visible": True, "is_transactable": True})

            assert availability["dt_lbound"] < availability["dt_ubound"], "Start date comes before end date."
            print("search by dates")
            SQL = """
                WITH unavail_items (id) AS (
                    SELECT r.item_id
                    FROM reservations r
                    INNER JOIN items i
                    ON i.id = r.item_id
                    WHERE r.is_calendared = TRUE AND NOT (r.dt_started > %s OR r.dt_ended < %s)
                ),
                all_items (id, is_transactable, is_visible) AS (
                    SELECT id, is_transactable, is_visible
                    FROM items
                )
                SELECT id FROM all_items
                WHERE is_transactable = TRUE AND is_visible = TRUE
                EXCEPT ALL
                SELECT id FROM unavail_items;
                """

            # IMPORTANT: Upper bound first, Lower bound second
            data = (availability["dt_ubound"], availability["dt_lbound"])

            with Models.db.conn.cursor() as cursor:
                cursor.execute(SQL, data)

                item_ids = cursor.fetchall()
                item_ids = [item_id for item_t in item_ids for item_id in item_t]

                items = []
                for item_id in item_ids:
                    item = cls.get({ "id": item_id })
                    items.append(item)
                return items
        else:
            return cls.filter({"is_visible": True, "is_transactable": True})






    def to_query_address(self):
        query_address = {
            "lat": self.address_lat,
            "lng": self.address_lng
        }

        return query_address


    @classmethod
    def get_item_info(cls,ids):
        SQL=f"""
        SELECT id, name, address_lat, address_lng, formatted as address_formatted
        FROM items 
        INNER JOIN addresses
        ON addresses.lat = address_lat AND addresses.lng = address_lng
        WHERE id in {tuple(ids)}"""
        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL) #, data)
            # result = cursor.fetchall()[0]
            results = cursor.fetchall()
            # print(results)
            _instances = []
            for result in results:
                _instance_dict = Blubber.format_to_dict(cursor, result)
                _instance = cls(_instance_dict)
                _instances.append(_instance)
        # print(_instances)
        return _instances