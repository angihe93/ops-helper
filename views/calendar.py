from flask import Blueprint, render_template
from datetime import datetime
import os
import psycopg2
from models.ops_calendar import OpsCalendar
from models.users import Users
from models.items import Items
from operator import attrgetter
from flask_login import login_required

calendar = Blueprint('calendar', __name__)

host = os.environ.get('DB_HOST')
database = os.environ.get('DB_DB')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PW')


def get_db_connection():
    conn = psycopg2.connect(
        host=host,
        database=database,
        user=user,
        password=password)
    return conn

@calendar.route('/calendar')
@login_required
def show_calendar():
    # get current month, start showing from there
    # show historical calendar if requested
    current_month = datetime.now().strftime('%m') # returns string eg. '11' for november, '02' for feb
    month_dict = {'01': ['Jan', 31], '02': ['Feb', 28], '03': ['Mar', 31], '04': ['Apr', 30], '05': ['May', 31], '06': ['Jun', 30],
                  '07': ['Jul', 31], '08': ['Aug', 31], '09': ['Sep', 30], '10': ['Oct', 31], '11': ['Nov', 30], '12': ['Dec', 31]}
    current_year = datetime.now().strftime('%Y')
    leap_year = 1 if int(current_year) % 4 == 0 and not int(current_year) % 100 == 0 else 0
    if leap_year==1:
        month_dict['02'] = ['Feb', 29]

    html = f"""
        <a href='upcoming-tasks'>Upcoming Tasks</a>&nbsp;&nbsp;
        <a href='main-site-ops'>Main Site Ops</a>
        <h2>Calendar</h2>
        <a href='past-tasks'>Past Tasks</a>
        <table>
          <tr>
            <th>{month_dict[current_month][0]} {current_year}</th>
            <th> </th>
            <th> </th>
            <th> </th>
            <th> </th>
            <th> </th>
            <th> </th>
          </tr>
        </table>
    """

    return html


@calendar.route('/upcoming-tasks')
@login_required
def upcoming_tasks():
    # 3 types of tasks:
     # 1) user ordered and did not fill out logistics form,
     # 2) user filled out logistics form but ops has not confirmed,
     # 3) ops has confirmed time
    
    # display the ones with res_dt_start >= the current day
    # for each one, use order.ext_dt_end to get the true end date, keep the ones with ext_dt_end >= current month being displayed

    # upcoming dropoffs
    # type 1 dropoff
    month = datetime.now().strftime('%m')
    year = datetime.now().strftime('%Y')
    day = datetime.now().strftime('%d')
    dropoffs_1 = OpsCalendar.get_upcoming_dropoffs_1(month, day, year)
    dropoffs_2 = OpsCalendar.get_upcoming_dropoffs_2(month, day, year)
    dropoffs_3 = OpsCalendar.get_upcoming_dropoffs_3(month, day, year)
 
    # order the dropoffs_1 by renter_id, date ascending, then merge those with the same renter and date
    try:
        dropoffs_1_sorted = sorted(dropoffs_1,key=attrgetter('date','renter_id'))
        dropoffs_1_grouped = [dropoffs_1_sorted[0]]
        for i in range(1,len(dropoffs_1_sorted)):
            # print('dropoffs_1_sorted[i]',dropoffs_1_sorted[i].task_type,dropoffs_1_sorted[i].order_id,dropoffs_1_sorted[i].date,dropoffs_1_sorted[i].renter_id)
            # print('dropoffs_1_grouped[-1]',dropoffs_1_grouped[-1].task_type,dropoffs_1_grouped[-1].order_id,dropoffs_1_grouped[-1].date,dropoffs_1_grouped[-1].renter_id)
            if dropoffs_1_sorted[i].date == dropoffs_1_grouped[-1].date and dropoffs_1_sorted[i].renter_id == dropoffs_1_grouped[-1].renter_id:
                # print('if same date and renter as previous')
                dropoffs_1_grouped[-1].order_id.append(dropoffs_1_sorted[i].order_id[0])
                dropoffs_1_grouped[-1].item_id.append(dropoffs_1_sorted[i].item_id[0])
                # print('dropoffs_1_grouped after append item:',dropoffs_1_grouped)
            else:
                # print('else not same date and renter as previous')
                dropoffs_1_grouped.append(dropoffs_1_sorted[i])
                # print('dropoffs_1_grouped after append object:',dropoffs_1_grouped)
    except IndexError:
        dropoffs_1_grouped = []
 
    # print('dropoffs_1_grouped')
    # for i in dropoffs_1_grouped:
    #     print(i.task_type,i.order_id,i.date,i.renter_id,i.item_id)


    try:
        dropoffs_2_sorted = sorted(dropoffs_2,key=attrgetter('logistics_id'))
        dropoffs_2_grouped = [dropoffs_2_sorted[0]]
        for i in range(1,len(dropoffs_2_sorted)):
            # print('dropoffs_1_sorted[i]',dropoffs_1_sorted[i].task_type,dropoffs_1_sorted[i].order_id,dropoffs_1_sorted[i].date,dropoffs_1_sorted[i].renter_id)
            # print('dropoffs_1_grouped[-1]',dropoffs_1_grouped[-1].task_type,dropoffs_1_grouped[-1].order_id,dropoffs_1_grouped[-1].date,dropoffs_1_grouped[-1].renter_id)
            if dropoffs_2_sorted[i].logistics_id == dropoffs_2_grouped[-1].logistics_id:
                # print('if same date and renter as previous')
                # check if need to append item or time range
                if dropoffs_2_sorted[i].item_id[0] != dropoffs_2_grouped[-1].item_id[-1]:
                    dropoffs_2_grouped[-1].order_id.append(dropoffs_2_sorted[i].order_id[0])
                    dropoffs_2_grouped[-1].item_id.append(dropoffs_2_sorted[i].item_id[0])
                if dropoffs_2_sorted[i].dt_range_start[0] != dropoffs_2_grouped[-1].dt_range_start[-1]:
                    dropoffs_2_grouped[-1].dt_range_start.append(dropoffs_2_sorted[i].dt_range_start[0])
                if dropoffs_2_sorted[i].dt_range_end[0] != dropoffs_2_grouped[-1].dt_range_end[-1]:
                    dropoffs_2_grouped[-1].dt_range_end.append(dropoffs_2_sorted[i].dt_range_end[0])
                # print('dropoffs_1_grouped after append item:',dropoffs_1_grouped)
            else:
                # print('else not same date and renter as previous')
                dropoffs_2_grouped.append(dropoffs_2_sorted[i])
                # print('dropoffs_1_grouped after append object:',dropoffs_1_grouped)
    except IndexError:
        dropoffs_2_grouped = []
 
    # print('\ndropoffs_2_grouped')
    # for i in dropoffs_2_grouped:
    #     print(i.task_type,i.logistics_id,i.order_id,i.date,i.dt_range_start,i.dt_range_end,i.renter_id,i.item_id)


    try:
        dropoffs_3_sorted = sorted(dropoffs_3,key=attrgetter('logistics_id'))
        dropoffs_3_grouped = [dropoffs_3_sorted[0]]
        for i in range(1,len(dropoffs_3_sorted)):
            if dropoffs_3_sorted[i].logistics_id == dropoffs_3_grouped[-1].logistics_id:
                if dropoffs_3_sorted[i].item_id[0] != dropoffs_3_grouped[-1].item_id[-1]:
                    dropoffs_3_grouped[-1].order_id.append(dropoffs_3_sorted[i].order_id[0])
                    dropoffs_3_grouped[-1].item_id.append(dropoffs_3_sorted[i].item_id[0])
                else:
                    dropoffs_3_grouped.append(dropoffs_3_sorted[i])
            else:
                dropoffs_3_grouped.append(dropoffs_3_sorted[i])
    except IndexError:
        dropoffs_3_grouped = []

    # print('\ndropoffs_3_grouped')
    # for i in dropoffs_3_grouped:
    #     print(i.task_type,i.logistics_id,i.order_id,i.date,i.dt_sched_eta,i.renter_id,i.item_id)


    all_tasks = dropoffs_1_grouped
    all_tasks.extend(dropoffs_2_grouped)
    all_tasks.extend(dropoffs_3_grouped)
    # all_tasks.sort(key=attrgetter('date'))


    pickups_1 = OpsCalendar.get_upcoming_pickups_1(month,day,year) # group by date, user?
    pickups_2 = OpsCalendar.get_upcoming_pickups_2(month,day,year) # group by logistics id?
    pickups_3 = OpsCalendar.get_upcoming_pickups_3(month,day,year) # group by logistics id?

    try:
        pickups_1_sorted = sorted(pickups_1,key=attrgetter('date','renter_id'))
        pickups_1_grouped = [pickups_1_sorted[0]]
        for i in range(1,len(pickups_1_sorted)):
            # print('dropoffs_1_sorted[i]',dropoffs_1_sorted[i].task_type,dropoffs_1_sorted[i].order_id,dropoffs_1_sorted[i].date,dropoffs_1_sorted[i].renter_id)
            # print('dropoffs_1_grouped[-1]',dropoffs_1_grouped[-1].task_type,dropoffs_1_grouped[-1].order_id,dropoffs_1_grouped[-1].date,dropoffs_1_grouped[-1].renter_id)
            if pickups_1_sorted[i].date == pickups_1_grouped[-1].date and pickups_1_sorted[i].renter_id == pickups_1_grouped[-1].renter_id:
                # print('if same date and renter as previous')
                pickups_1_grouped[-1].order_id.append(pickups_1_sorted[i].order_id[0])
                pickups_1_grouped[-1].item_id.append(pickups_1_sorted[i].item_id[0])
                # print('dropoffs_1_grouped after append item:',dropoffs_1_grouped)
            else:
                # print('else not same date and renter as previous')
                pickups_1_grouped.append(pickups_1_sorted[i])
                # print('dropoffs_1_grouped after append object:',dropoffs_1_grouped)
    except IndexError:
        pickups_1_grouped = []

    # print('pickups_1_grouped')
    # for i in pickups_1_grouped:
    #     print(i.task_type,i.order_id,i.date,i.renter_id,i.item_id)


    try:
        pickups_2_sorted = sorted(pickups_2,key=attrgetter('logistics_id'))
        pickups_2_grouped = [pickups_2_sorted[0]]
        for i in range(1,len(pickups_2_sorted)):
            # print('dropoffs_1_sorted[i]',dropoffs_1_sorted[i].task_type,dropoffs_1_sorted[i].order_id,dropoffs_1_sorted[i].date,dropoffs_1_sorted[i].renter_id)
            # print('dropoffs_1_grouped[-1]',dropoffs_1_grouped[-1].task_type,dropoffs_1_grouped[-1].order_id,dropoffs_1_grouped[-1].date,dropoffs_1_grouped[-1].renter_id)
            if pickups_2_sorted[i].logistics_id == pickups_2_grouped[-1].logistics_id:
                # print('if same date and renter as previous')
                # check if need to append item or time range
                if pickups_2_sorted[i].item_id[0] != pickups_2_grouped[-1].item_id[-1]:
                    pickups_2_grouped[-1].order_id.append(pickups_2_sorted[i].order_id[0])
                    pickups_2_grouped[-1].item_id.append(pickups_2_sorted[i].item_id[0])
                if pickups_2_sorted[i].dt_range_start[0] != pickups_2_grouped[-1].dt_range_start[-1]:
                    pickups_2_grouped[-1].dt_range_start.append(pickups_2_sorted[i].dt_range_start[0])
                if pickups_2_sorted[i].dt_range_end[0] != pickups_2_grouped[-1].dt_range_end[-1]:
                    pickups_2_grouped[-1].dt_range_end.append(pickups_2_sorted[i].dt_range_end[0])
                # print('dropoffs_1_grouped after append item:',dropoffs_1_grouped)
            else:
                # print('else not same date and renter as previous')
                pickups_2_grouped.append(pickups_2_sorted[i])
                # print('dropoffs_1_grouped after append object:',dropoffs_1_grouped)
    except IndexError:
        pickups_2_grouped = []

    # print('\npickups_2_grouped')
    # for i in pickups_2_grouped:
    #     print(i.task_type,i.logistics_id,i.order_id,i.date,i.renter_id,i.item_id,i.dt_range_start,i.dt_range_end)


    try:
        pickups_3_sorted = sorted(pickups_3,key=attrgetter('logistics_id'))
        pickups_3_grouped = [pickups_3_sorted[0]]
        for i in range(1,len(pickups_3_sorted)):
            if pickups_3_sorted[i].logistics_id == pickups_3_grouped[-1].logistics_id:
                if pickups_3_sorted[i].item_id[0] != pickups_3_grouped[-1].item_id[-1]:
                    pickups_3_grouped[-1].order_id.append(pickups_3_sorted[i].order_id[0])
                    pickups_3_grouped[-1].item_id.append(pickups_3_sorted[i].item_id[0])
                else:
                    pickups_3_grouped.append(pickups_3_sorted[i])
            else:
                pickups_3_grouped.append(pickups_3_sorted[i])
    except IndexError:
        pickups_3_grouped = []

    all_tasks.extend(pickups_1_grouped)
    all_tasks.extend(pickups_2_grouped)
    all_tasks.extend(pickups_3_grouped)
    all_tasks.sort(key=attrgetter('date','dt_sched_eta'))

    renter_ids = [i.renter_id for i in all_tasks]
    renter_infos = Users.get_renter_info(renter_ids)

    item_ids = [i.item_id for i in all_tasks]
    item_ids = [item for sublist in item_ids for item in sublist] # flatten item_ids list
    item_infos = Items.get_item_info(item_ids)

    return_str = "<a href='calendar'>Calendar</a>&nbsp;&nbsp;<a href='main-site-ops'>Main Site Ops</a> <h2>Upcoming Tasks</h2> <p><ul>"
    
    for i in all_tasks:
        # print(i,i.task_type,i.logistics_id,type(str(i.logistics_id)),i.date)
        # display by default:
        return_str+="<li>"
        return_str+=f"date: {str(i.date)}&nbsp;&nbsp;&nbsp;type: {str(i.task_type.split(' ')[-1])}&nbsp;&nbsp;&nbsp;time scheduled: {str(i.dt_sched_eta)}&nbsp;&nbsp;&nbsp;address: {str(i.address_formatted)}"
        item_info = []
        for item_id in i.item_id: # for each item in the current task
            item = [item for item in item_infos if item_id==item.id][0]
            item_info.append([item.id,item.name,(item.address_lat,item.address_lng),item.address_formatted])
        # print('item_info:',item_info)
        return_str+=f"<ul><li>items: <ol>"
        for item in item_info:
            if 'dropoff' in i.task_type: # care about item location in dropoffs
                return_str+=f"<li>({item[0]}) {item[1]} (location: {item[3]})</li>"
            elif 'pickup' in i.task_type:
                return_str+=f"<li>({item[0]}) {item[1]}</li>"
        return_str+="</ol></li>"

        if i.task_type=="type 3 pickup" or i.task_type=="type 3 dropoff":
            return_str+="<li>delivery notes: "+str(i.notes)+"</li></ul>"
        elif i.task_type=="type 2 pickup" or i.task_type=="type 2 dropoff":
            dt_range_zip_sorted = sorted(list(zip(i.dt_range_start,i.dt_range_end)),key=lambda x: x[0])
            dt_range_zip_sorted = [[i[0],i[1]] for i in dt_range_zip_sorted]
            dt_ranges = [dt_range_zip_sorted[0]]
            for t in range(1,len(dt_range_zip_sorted[1:])):
                if dt_range_zip_sorted[t][0]==dt_range_zip_sorted[t-1][1]: # if current start is same as previous end
                    dt_ranges[-1][1]=dt_range_zip_sorted[t][1] # update previous end to current end
                else: # append new range
                    dt_ranges.append(dt_range_zip_sorted[t])
            return_str+="<li>available times: "
            for t in dt_ranges:
                return_str+=t[0].strftime("%H:%M")+"-"+t[1].strftime("%H:%M")+", "
            return_str=return_str[:-2] # remove last comma
            return_str+="</li>"
            return_str+="<li>delivery notes: "+str(i.notes)+"</li>"
            return_str+="</ul>"
        elif i.task_type=="type 1 pickup" or i.task_type=="type 1 dropoff":
            return_str+="<li>remind user to submit availability</li></ul>"

        renter_info = [r for r in renter_infos if r.id==i.renter_id][0]
        # print('renter_info:',renter_info.id, renter_info.name, renter_info.email, renter_info.phone)
        return_str += "<details><summary>more info</summary>"
        return_str+= f"order id(s): {i.order_id}, logistics id: {i.logistics_id}, renter info: [id: {renter_info.id}, name: {renter_info.name}, email: {renter_info.email}, phone: {renter_info.phone}, address lat/lng: ({i.address_lat},{i.address_lng})]"
        return_str += "</details>"

        return_str+='<li style="list-style:none;">&nbsp;</li>'
    
    return_str += "</ul></p>"

    return return_str



@calendar.route('/past-tasks')
@login_required
def past_tasks():
    return "<a href='calendar'>Main Calendar</a><p>This is Past Tasks</p>"
