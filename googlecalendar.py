#!usr/bin/python
# A Script that gets this weeks schedule from peoplestuff and adds them to google calendar

import macds as mac
import os
import httplib2
import datetime
import yaml
import argparse

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except SystemExit:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Macds writer'

service = None


# uses a yaml file to store the username and password
with open("config.yml", 'r') as yml_file:
    cfg = yaml.load(yml_file)
    password = cfg['password']
    username = cfg['username']


def get_credentials():
    """
    get_credentials creates an oauth credential file
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'macds-gcalendar.json')
    
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)

    return credentials


def add_shift_to_calendar(schedule):
    """
    addShiftToCalendar loops through the schedule and adds each shift to the calendar

    :param schedule: list of shifts
    :type schedule: list of shifts as tuples in the form of ("day, date", "start:end")
    """
    
    event = {
        'summary': 'Shift'
        }

    for val in schedule:
        dt_tup = __create_datetime(val)
        if dt_tup is not None:

            start = dt_tup[0].isoformat('T') + 'Z'
            st = {'dateTime': start, 'timezone': 'GMT'}
            event['start'] = st

            end = dt_tup[1].isoformat('T') + 'Z'
            en = {'dateTime': end, 'timezone': 'GMT'}
            event['end'] = en

            add_to_calendar(event)


def __create_datetime(shift):
    """
    createDateTime is a helper method for the addShiftToCalendar function. It creates and start and an end datetime
    and returns them as a tuple.

    The shift param will be a tuple in the format ('Thursday, 09/03/2017', '16:30-23:30').

    :param shift: shift time
    :type shift: tuple
    :return: a tuple containing a datetime object for the start and end of the shift. Will return None if there is
    no time in the shift string.
    """
    print(shift)

    time_format = "%d/%m/%Y %H:%M"
    # get the date string
    day, time = shift
    date = day.split(", ")[1]
    s = date + " "

    # split the time into shift start and end
    tm = time.split("-")

    # check if tm has both start and end time
    if len(tm) != 2:
        return

    start = s + tm[0]
    s_dt = datetime.datetime.strptime(start, time_format)
    end = s + tm[1]

    e_dt = datetime.datetime.strptime(end, time_format)
    
    tup = (s_dt, e_dt)
    
    return tup


def add_to_calendar(entry):
    """
    add_to_calendar adds the given entry to google calendar.
    Entries must be in the form:
    
    event = {
        'summary':'summary text',
        'start':{
            'dateTime': 'RFC339 format'
            'timezone': 'GMT'
        },
        'end':{
            'dateTime': 'RFC339 format'
            'timezone': 'GMT'
        },
    }
    
    """
    # check whether a shift has already been added for that day
    event_list = service.events().list(calendarId='primary', timeMin=entry['start']['dateTime'],
                                       timeMax=entry['end']['dateTime']).execute()
    for val in event_list['items']:
        # if the title of the found event is 'Shift' we can assume it has already been added
        if val['summary'] == 'Shift':
            print("Shift already added for %s" % entry['start']['dateTime'])
            return  # exit function

    entry = service.events().insert(calendarId='primary', body=entry).execute()
    print("Entry created: %s" % (entry.get('htmlLink')))


def main():
    
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    global service  # global variable so the addToCalendar function can access it
    service = discovery.build('calendar', 'v3', http=http)

    # get schedule for this week
    schedule = mac.get_shift(username, password)
    # add the shifts to google calendar
    for val in schedule.weeks:
        add_shift_to_calendar(val)
 
if __name__ == '__main__':
    main()
