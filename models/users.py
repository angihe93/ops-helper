import copy
from blubber_orm import Models
from blubber_orm.models._conn import Blubber

class Users(Models):
    """
    A class to define the use of the Users type from Hubbub Shop's relational database.
    Create, read, update, destroy have been implemented by the Models class.

    """

    table_name = "users"
    table_primaries = ["id"]
    sensitive_attributes = ["password", "session_key"]

    def __init__(self, attrs: dict):
        self.id = attrs["id"]

        self._unformatted_name = attrs["name"]
        self.name = self.get_name()
        # self.first_name = self.get_first_name()
        # self.last_name = self.get_last_name()

        self.phone = attrs["phone"]
        self.email = attrs["email"]
        # self.password = attrs["password"]
        # self.bio = attrs["bio"]
        # self.profile_pic = attrs["profile_pic"]
        # self.dt_joined = attrs["dt_joined"]
        # self.dt_last_active = attrs["dt_last_active"]
        # self.is_blocked = attrs["is_blocked"]
        # self.session_key = attrs["session_key"]

        # self.address_lat = attrs["address_lat"]
        # self.address_lng = attrs["address_lng"]

        # self._password = attrs.get("password")


    def get_name(self):
        return self._unformatted_name.replace("+", " ")


    def get_first_name(self):
        return self._unformatted_name.split("+")[0]


    def get_last_name(self):
        return self._unformatted_name.split("+")[1]


    @classmethod
    def get_valid_roles(cls):
        return ["payees", "payers", "couriers", "renters", "listers", "senders", "receivers"]


    @classmethod
    def get_all(cls, role=None):
        if role is None: return super().get_all()

        valid_roles = Users.get_valid_roles()
        assert role in valid_roles

        SQL = f"""
            SELECT *
            FROM {role};
            """

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL)
            user_tuples = cursor.fetchall()
            user_tuples = copy.deepcopy(user_ids)

            users = []
            for user_t in user_tuples:
                id, *_ = user_t
                user = cls.get({"id": id})
                users.append(user)
        return users


    def to_query_address(self):
        query_address = {
            "lat": self.address_lat,
            "lng": self.address_lng
        }

        return query_address


    def add_role(self, role: str):
        role = role.lower()
        valid_roles = Users.get_valid_roles()
        assert role in valid_roles, f"This is not a valid role. Try: [{', '.join(valid_roles)}]"

        role_id = f"{role[:-1]}_id"

        SQL = f"""
            INSERT
            INTO {role} ({role_id})
            VALUES (%s)
            ON CONFLICT ({role_id}) DO NOTHING;
            """

        data = (self.id,)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)

            Models.db.conn.commit()


    def check_role(self, role: str):
        role = role.lower()
        valid_roles = Users.get_valid_roles()
        assert role in valid_roles, f"This is not a valid role. Try: [{', '.join(valid_roles)}]"

        role_id = f"{role[:-1]}_id"

        SQL = f"""
            SELECT {role_id}
            FROM {role}
            WHERE {role_id} = %s;
            """

        data = (self.id,)

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL, data)
            result = cursor.fetchone()

            return result is not None

    @classmethod
    def get_renter_info(cls,ids):
        SQL = f"""SELECT id, name, email, phone FROM users WHERE id IN {tuple(ids)}"""
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
        #     _instance_dict = Blubber.format_to_dict(cursor, result)
        #     _instance = cls(_instance_dict)
        #     # print("_instance in get_renter_info",_instance,"id:",_instance.id,"name:",_instance.name)
        # return _instance