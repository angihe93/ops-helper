from flask import Blueprint, render_template, redirect, url_for, request
import flask
from datetime import datetime
import os
import psycopg2
from models.ops_calendar import OpsCalendar
from models.users import Users
from models.items import Items
from operator import attrgetter
from flask_login import login_required
from pytz import timezone
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import google.oauth2.credentials
from email.message import EmailMessage
from email.mime.text import MIMEText
import base64

calendar = Blueprint('calendar', __name__)

eastern = timezone('US/Eastern')

@calendar.route('/calendar')
@login_required
def show_calendar():
    # get current month, start showing from there
    # show historical calendar if requested
    current_month = datetime.now(eastern).strftime('%m') # returns string eg. '11' for november, '02' for feb
    month_dict = {'01': ['Jan', 31], '02': ['Feb', 28], '03': ['Mar', 31], '04': ['Apr', 30], '05': ['May', 31], '06': ['Jun', 30],
                  '07': ['Jul', 31], '08': ['Aug', 31], '09': ['Sep', 30], '10': ['Oct', 31], '11': ['Nov', 30], '12': ['Dec', 31]}
    current_year = datetime.now(eastern).strftime('%Y')
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
    month = datetime.now(eastern).strftime('%m')
    year = datetime.now(eastern).strftime('%Y')
    day = datetime.now(eastern).strftime('%d')
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
        renter_info = [r for r in renter_infos if r.id==i.renter_id][0]
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
            url_for_email = flask.url_for('calendar.email',recipient=renter_info.email,first_name=renter_info.name.split(' ')[0],etype=i.task_type.split(' ')[-1],year=year,month=month,day=day,items=item_info) 
            return_str+=f"""<li><a href={url_for_email} onclick="return confirm('Click OK to confirm sending email')">remind user to submit availability</a></li></ul>"""

        
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


@calendar.route('/oauth')
@login_required
def oauth():
    SCOPES = ['https://mail.google.com/']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json', scopes=SCOPES)
    # flow.redirect_uri = url_for('calendar.upcoming_tasks', _external=True)
    flow.redirect_uri = url_for('calendar.oauth2callback', _external=True)
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    
    # Store the state so the callback can verify the auth server response.
    flask.session['state'] = state
    
    return redirect(authorization_url)

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}

@calendar.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']
    SCOPES = ['https://mail.google.com/']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json', scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('calendar.oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

    # return flask.redirect(flask.url_for('calendar.email'))
    return flask.redirect(flask.url_for('calendar.upcoming_tasks'))


@calendar.route('/email')
@login_required
def email():
    try:
        credentials = google.oauth2.credentials.Credentials(**flask.session['credentials'])
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=credentials) 

    except: # error if not logged in to google oauth
        return flask.redirect(flask.url_for('oauth'))
    

    etype = request.args.get('etype')
    recipient = request.args.get('recipient')
    first_name = request.args.get('first_name')
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    items = request.args.getlist('items')
    # print('items:',items, type(items))

    dt = datetime(int(year),int(month),int(day))
    dt_to_weekday = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday',
                            3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
    weekday = dt_to_weekday[dt.weekday()]
    mdy = f'{month}/{day}/{year}'

    items_html = ""
    try:
        if any(isinstance(eval(i), list) for i in items): # if mutiple items
            for item in items:
                # print('item',item,type(item))
                item_li = eval(item)
                # print('item_li',item_li,type(item_li))
                items_html+= f"<a href=https://www.hubbub.shop/item/{item_li[0]}>{item_li[1]}</a>, " #name
            items_html= items_html[:-2]
    except:
        items_html+=f"<a href=https://www.hubbub.shop/item/{items[0]}>{items[1]}</a>, "

    if etype == 'dropoff':
        # print("if etype == 'dropoff'")
        if len(items)>1:
            subject = '[Hubbub] Schedule Drop-offs for Your Rentals'
        else:
            subject = '[Hubbub] Schedule Drop-off for Your Rental'
        body_html = f"""<p>Hi {first_name}, </p>
        <p> Hope you're doing well! We're reaching out regarding the upcoming start of your rental of {items_html} on <b>{weekday} {mdy}</b>. Please use <a href=https://www.hubbub.shop/accounts/u/orders>this link</a> to schedule your drop-off. Let us know if you have any questions. </p>
        <p>All the best,</p>
        <p>Team Hubbub</p>
        """

    elif etype =='pickup':
        # print("elif etype =='pickup'")
        subject = '[Hubbub] End of Rental Logistics'
        body_html = f"""<p>Hi {first_name}, </p>
            <p>Hope you're doing well and enjoying your rental! </p>
            <p>We're reaching out regarding the upcoming end of your rental of {items_html} on <b>{weekday} {mdy}</b>. Please schedule your pick-up at <a href=https://www.hubbub.shop/accounts/u/orders>this link</a>, or use the link to set up a rental extension. Let us know if you have any questions.</p>
            <p>All the best,</p>
            <p>Team Hubbub</p>
            """
        
    message = EmailMessage()
    # body = MIMEText(f"<p>hello from hubbub!</p>",'html')
    body = MIMEText(body_html,'html')
    message.set_content(body)
    # message['Subject'] = 'hubbub test'
    message['Subject'] = subject
    # message['To'] = 'ah3354@columbia.edu'
    message['To'] = recipient
    message['From'] = 'hello@hubbub.shop'
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    # for sending email:
    create_message = {
        'raw': encoded_message
    }
    service.users().messages().send(userId="me", body=create_message).execute()
    # for saving draft email
    # create_message = {
    #     'message': {
    #         'raw': encoded_message
    #     }
    # }
    # service.users().drafts().create(userId="me", body=create_message).execute()
    return f"<p>email sent.</p><p><a href={url_for('calendar.upcoming_tasks')}>back to upcoming tasks</a></p>"
