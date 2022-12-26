# https://github.com/hubbub-tech/rent-server/blob/e86cafc43caf56458b4f2998650a224439c2fc55/src/models/logistics/timeslots.py
from blubber_orm import Models
# from ._conn import Blubber
from blubber_orm.models._conn import Blubber


class OpsCalendar(Models):

    def __init__(self, attrs):
        self.task_type = attrs["task_type"]
        self.logistics_id = attrs["logistics_id"]
        self.order_id = [attrs["order_id"]]
        self.date = attrs["date"]
        self.dt_range_start = [attrs["dt_range_start"]] # can be none if type 1
        self.dt_range_end = [attrs["dt_range_end"]] # can be none if type 1
        self.dt_sched_eta = attrs["dt_sched_eta"] # can be none if type 1 or 2
        self.notes = attrs["notes"] # can be none if type 1
        self.item_id = [attrs["item_id"]]
        self.renter_id = attrs["renter_id"]
        self.address_lat = attrs["address_lat"] # address for type 1 is based on users table, may not be up to date
        self.address_lng = attrs["address_lng"]
        self.address_formatted = attrs["address_formatted"]

    def get_name(self):
        return self._unformatted_name.replace("+", " ")

    @classmethod
    def get_upcoming_dropoffs_1(cls, month, day, year): # get type 1 dropoffs to display in ops calendar: type 1 meaning user placed order but has not filled out dropoff logistics form
        ### this query assumes user has not filled out the pickup form first, bc if so it will be in order_logistics and this will fail to collect the dropoff
        SQL = f"""
            select 'type 1 dropoff' as task_type, null as logistics_id, order_id, date(res_dt_start) as date, null as dt_range_start, null as dt_range_end, null as dt_sched_eta, null as notes, item_id, orders_users_.users_id as renter_id, address_lat, address_lng, formatted as address_formatted
            from
                (select 'type 1 dropoff', orders_.id as order_id, res_dt_start, item_id, users.id as users_id, address_lat, address_lng
                    from
                    (select 'type 1 dropoff', id, res_dt_start, renter_id, item_id
                    FROM orders
                    WHERE DATE(res_dt_start) >= '{year+'-'+month+'-'+day}' and is_canceled='FALSE' and id not in
                        (select order_id
                        from order_logistics)  ) as orders_
                left JOIN users
                on users.id=orders_.renter_id ) as orders_users_
            left join addresses
            on addresses.lat= orders_users_.address_lat and addresses.lng=orders_users_.address_lng
        """
        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL) #, data)
            results = cursor.fetchall()
            # print(value)
            _instances = []
            for result in results:
                _instance_dict = Blubber.format_to_dict(cursor, result)
                _instance = cls(_instance_dict)
                _instances.append(_instance)
        # print(_instances)
        return _instances
            # return value

    @classmethod
    def get_upcoming_dropoffs_2(cls, month, day, year):
        SQL = f"""
            select distinct 'type 2 dropoff' as task_type, timeslots.logistics_id, order_id, date(res_dt_start) as date, dt_range_start, dt_range_end, null as dt_sched_eta, notes, item_id, renter_id, to_addr_lat as address_lat, to_addr_lng as address_lng, formatted as address_formatted
            from
                (
                select order_id, res_dt_start, item_id, renter_id, logistics_id, notes, to_addr_lat, to_addr_lng, formatted
                from
                    (select order_id, res_dt_start, item_id, renter_id, logistics_id, notes, to_addr_lat, to_addr_lng
                    from
                        (select id as order_id, res_dt_start, item_id, renter_id, logistics_id
                        from orders
                        inner join order_logistics
                        on orders.id = order_logistics.order_id
                        where DATE(res_dt_start) >= '{year+'-'+month+'-'+day}' and is_canceled='FALSE') as order_logistics_
                    left join logistics
                    on logistics.id = order_logistics_.logistics_id and logistics.receiver_id = order_logistics_.renter_id) as order_logistics__
                left join addresses
                on order_logistics__.to_addr_lat = addresses.lat and order_logistics__.to_addr_lng = addresses.lng
                ) as order_logistics_addresses
                left join timeslots
                on timeslots.logistics_id = order_logistics_addresses.logistics_id
            where dt_sched_eta is null
        """
        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL) #, data)
            results = cursor.fetchall()
            # print(value)
            _instances = []
            for result in results:
                _instance_dict = Blubber.format_to_dict(cursor, result)
                _instance = cls(_instance_dict)
                _instances.append(_instance)
        # print(_instances)
        return _instances


    @classmethod
    def get_upcoming_dropoffs_3(cls, month, day, year): # get type 1 dropoffs to display in ops calendar: type 1 meaning user placed order but has not filled out dropoff logistics form
    ### make sure the logistics item is for dropoff only, not pickups too
        SQL = f"""
            select distinct 'type 3 dropoff' as task_type, timeslots.logistics_id, order_id, date(res_dt_start) as date, null as dt_range_start, null as dt_range_end, notes, dt_sched_eta, item_id, renter_id, to_addr_lat as address_lat, to_addr_lng as address_lng, formatted as address_formatted
            from
                (
                select order_id, res_dt_start, item_id, renter_id, logistics_id, notes, to_addr_lat, to_addr_lng, formatted
                from
                    (select order_id, res_dt_start, item_id, renter_id, logistics_id, notes, to_addr_lat, to_addr_lng
                    from
                        (select id as order_id, res_dt_start, item_id, renter_id, logistics_id
                        from orders
                        inner join order_logistics
                        on orders.id = order_logistics.order_id
                        where DATE(res_dt_start) >= '{year+'-'+month+'-'+day}' and is_canceled='FALSE') as order_logistics_
                    left join logistics
                    on logistics.id = order_logistics_.logistics_id and logistics.receiver_id = order_logistics_.renter_id) as order_logistics__
                left join addresses
                on order_logistics__.to_addr_lat = addresses.lat and order_logistics__.to_addr_lng = addresses.lng
                ) as order_logistics_addresses
                left join timeslots
                on timeslots.logistics_id = order_logistics_addresses.logistics_id
            where dt_sched_eta is not null
        """
        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL) #, data)
            results = cursor.fetchall()
            # print(value)
            _instances = []
            for result in results:
                _instance_dict = Blubber.format_to_dict(cursor, result)
                _instance = cls(_instance_dict)
                _instances.append(_instance)
        # print(_instances)
        return _instances


    @classmethod
    def get_upcoming_pickups_1(cls, month, day, year): # get type 1 dropoffs to display in ops calendar: type 1 meaning user placed order but has not filled out dropoff logistics form
        SQL = f"""
            select 'type 1 pickup' as task_type, null as logistics_id, id as order_id, date, null as dt_range_start, null as dt_range_end, null as dt_sched_eta, null as notes, item_id, orders_users_.renter_id, address_lat, address_lng, formatted as address_formatted
            from
                (select orders_.id, date, renter_id, item_id, address_lat, address_lng
                from
                    (select id, coalesce(ext_date,date(orders.res_dt_end)) as date, renter_id, item_id
                    from orders
                    left join
                        (select order_id, date(max(res_dt_end)) as ext_date
                        from extensions
                        group by order_id) as extensions_max
                    on orders.id = extensions_max.order_id
                    where  coalesce(ext_date,date(orders.res_dt_end)) >= '{year+'-'+month+'-'+day}' and is_canceled='FALSE' and (id in
                       (select order_id
                       from order_logistics
                       group by order_id
                       having count(distinct(logistics_id))<=1) or
                       id not in (select order_id from order_logistics))
                    order by date) as orders_
                left join users
                on users.id=orders_.renter_id ) as orders_users_
            left join addresses
            on addresses.lat=orders_users_.address_lat and addresses.lng=orders_users_.address_lng
        """

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL) #, data)
            results = cursor.fetchall()
            # print("results from ops_calendar.get_upcoming_pickups_1",results)
            _instances = []
            for result in results:
                _instance_dict = Blubber.format_to_dict(cursor, result)
                _instance = cls(_instance_dict)
                _instances.append(_instance)
        # print(_instances)
        return _instances

    @classmethod
    def get_upcoming_pickups_2(cls, month, day, year): # get type 1 dropoffs to display in ops calendar: type 1 meaning user placed order but has not filled out dropoff logistics form
        SQL = f"""
            select distinct 'type 2 pickup' as task_type, timeslots.logistics_id, order_id, date, dt_range_start, dt_range_end, null as dt_sched_eta, notes, item_id, renter_id, from_addr_lat as address_lat, from_addr_lng as address_lng, formatted as address_formatted
            from
                (select order_id, date, item_id, renter_id, logistics_id, notes, from_addr_lat, from_addr_lng, formatted
                from
                    (select order_id, date, item_id, renter_id, logistics_id, notes, from_addr_lat, from_addr_lng
                    from
                        (select order_id, date, item_id, renter_id, logistics_id
                        from
                            (select id, coalesce(ext_date,date(orders.res_dt_end)) as date, renter_id, item_id
                            from orders
                            left join
                                (select order_id, date(max(res_dt_end)) as ext_date
                                from extensions
                                group by order_id) as extensions_max
                            on orders.id = extensions_max.order_id
                            where  coalesce(ext_date,date(orders.res_dt_end)) >= '{year+'-'+month+'-'+day}' and is_canceled='FALSE') as orders_ext
                        inner join order_logistics
                        on orders_ext.id = order_logistics.order_id) as order_logistics_
                    inner join logistics
                    on logistics.id = order_logistics_.logistics_id and logistics.sender_id = order_logistics_.renter_id) as order_logistics__
                left join addresses
                on order_logistics__.from_addr_lat = addresses.lat and order_logistics__.from_addr_lng = addresses.lng) as order_logistics_addresses
            left join timeslots
            on timeslots.logistics_id = order_logistics_addresses.logistics_id
            where dt_sched_eta is null
        """

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL) #, data)
            results = cursor.fetchall()
            # print("results from ops_calendar.get_upcoming_pickups_1",results)

            _instances = []
            for result in results:
                _instance_dict = Blubber.format_to_dict(cursor, result)
                _instance = cls(_instance_dict)
                _instances.append(_instance)
        # print(_instances)
        return _instances


    @classmethod
    def get_upcoming_pickups_3(cls, month, day, year): # get type 1 dropoffs to display in ops calendar: type 1 meaning user placed order but has not filled out dropoff logistics form
        SQL = f"""
                select distinct 'type 3 pickup' as task_type, timeslots.logistics_id, order_id, date, null as dt_range_start, null as dt_range_end, dt_sched_eta, notes, item_id, renter_id, from_addr_lat as address_lat, from_addr_lng as address_lng, formatted as address_formatted
                from
                    (select order_id, date, item_id, renter_id, logistics_id, notes, from_addr_lat, from_addr_lng, formatted
                    from
                        (select order_id, date, item_id, renter_id, logistics_id, notes, from_addr_lat, from_addr_lng
                        from
                            (select order_id, date, item_id, renter_id, logistics_id
                            from
                                (select id, coalesce(ext_date,date(orders.res_dt_end)) as date, renter_id, item_id
                                from orders
                                left join
                                    (select order_id, date(max(res_dt_end)) as ext_date
                                    from extensions
                                    group by order_id) as extensions_max
                                on orders.id = extensions_max.order_id
                                where  coalesce(ext_date,date(orders.res_dt_end)) >= '{year+'-'+month+'-'+day}' and is_canceled='FALSE') as orders_ext
                            inner join order_logistics
                            on orders_ext.id = order_logistics.order_id) as order_logistics_
                        inner join logistics
                        on logistics.id = order_logistics_.logistics_id and logistics.sender_id = order_logistics_.renter_id) as order_logistics__
                    left join addresses
                    on order_logistics__.from_addr_lat = addresses.lat and order_logistics__.from_addr_lng = addresses.lng) as order_logistics_addresses
                left join timeslots
                on timeslots.logistics_id = order_logistics_addresses.logistics_id
                where dt_sched_eta is not null
        """

        with Models.db.conn.cursor() as cursor:
            cursor.execute(SQL) #, data)
            results = cursor.fetchall()
            # print("results from ops_calendar.get_upcoming_pickups_1",results)

            _instances = []
            for result in results:
                _instance_dict = Blubber.format_to_dict(cursor, result)
                _instance = cls(_instance_dict)
                _instances.append(_instance)
        # print(_instances)
        return _instances
