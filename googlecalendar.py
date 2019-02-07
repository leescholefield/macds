#!usr/bin/python
# A Script that gets this weeks schedule from peoplestuff and adds them to google calendar
# In order for this to work you will need the client_secret file.
# You can find this here: https://developers.google.com/calendar/quickstart/go

import macds as mac
import config
import os
import httplib2
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


def add_shift_to_calendar(shift):
    """
    Adds the given shift to the calendar.

    :param shift: tuple containing datetimes for the start and end of the shift.
    """
    
    event = {
        'summary': 'Shift'
        }

    start = shift[0].isoformat('T') + 'Z'
    st = {'dateTime': start, 'timezone': 'GMT'}
    event['start'] = st

    end = shift[1].isoformat('T') + 'Z'
    en = {'dateTime': end, 'timezone': 'GMT'}
    event['end'] = en

    add_to_calendar(event)


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

 
if __name__ == '__main__':
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    global service  # global variable so the addToCalendar function can access it. Doesn't authenticate without it
    service = discovery.build('calendar', 'v3', http=http)

    # get schedule for this week
    schedule = mac.get_schedule(config.username, config.password)
    # add the shifts to google calendar
    for val in schedule.days_working:
        add_shift_to_calendar(val)
