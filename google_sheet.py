import datetime
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SPREADSHEET_ID = '12IQrtvg-__WQTPhxP96TLXOI7nxIXF6Kcw_aVSAkjqQ'
SHEET_ID = 1425584630
SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Personal CICO recorder'
CALORIES_IN_COLUMN = 'E'
WEIGHT_COLUMN = 'B'
NEW_TDEE_COLUMN = 'F'
FITBIT_CALORIES_OUT_COLUMN = 'G'
NON_FUNCTION_COLUMN_INDICES = [0, 1, 4, 5, 6]


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'sheets.googleapis.com-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print 'Storing credentials to ' + credential_path
    return credentials


def format_to_range(column, row):
    cell = column + row
    cell += ':' + cell
    return cell


def add_today_row_if_missing(service, today_row, yesterday_row):
    today = datetime.date.today()
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='{0}:{0}'.format(today_row)).execute()

    # if set already, exit without doing anything else
    result_values = result.get('values', [])
    if len(result_values) > 0 and result_values[0][0]:
        return

    # get yesterday's row values for the formulas
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='{0}:{0}'.format(yesterday_row), valueRenderOption='FORMULA').execute()
    values = result.get('values', [])
    requests = []
    for i, value in enumerate(values[0]):
        # copying format of columns
        if i == 0 or i not in NON_FUNCTION_COLUMN_INDICES:
            start_source_row_index = int(yesterday_row) - 1
            end_destination_row_index = int(today_row) - 1
            requests.append({
                "copyPaste": {
                    "source": {
                        "sheetId": SHEET_ID,
                        "startRowIndex": start_source_row_index,
                        "endRowIndex": start_source_row_index + 1,
                        "startColumnIndex": i,
                        "endColumnIndex": i + 1
                    },
                    "destination": {
                        "sheetId": SHEET_ID,
                        "startRowIndex": end_destination_row_index,
                        "endRowIndex": end_destination_row_index + 1,
                        "startColumnIndex": i,
                        "endColumnIndex": i + 1
                    },
                    "pasteType": "PASTE_FORMAT",
                    "pasteOrientation": "NORMAL"
                }
            })

        # only copy over values from previous row if it's a function
        if i not in NON_FUNCTION_COLUMN_INDICES:
            start_row_index = int(yesterday_row) - 1
            end_row_index = int(today_row)
            requests.append({
                "repeatCell": {
                    "range": {
                        "sheetId": SHEET_ID,
                        "startRowIndex": start_row_index,
                        "endRowIndex": end_row_index,
                        "startColumnIndex": i,
                        "endColumnIndex": i + 1
                    },
                    "cell": {
                        "userEnteredValue": {
                            "formulaValue": value
                        }
                    },
                    "fields": "userEnteredValue"
                }
            })

    body = {
        'requests': requests
    }
    service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID,
                                       body=body).execute()
    # add today's date
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID, range='A{}'.format(today_row), valueInputOption='USER_ENTERED',
        body={'values': [[str(today)]]}).execute()


def write_to_sheet(calories_in, fitbit_calories_out, weight, new_tdee):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discovery_url = ('https://sheets.googleapis.com/$discovery/rest?'
                     'version=v4')
    service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discovery_url)

    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID, range='A:A').execute()
    values = result.get('values', [])

    yesterday = datetime.date.today() - datetime.timedelta(1)
    if not values:
        print 'No data found.'
    else:
        yesterday_row = None
        today_row = None
        for i, row in enumerate(values):
            if len(row) == 0:
                continue
            try:
                column_date = datetime.datetime.strptime(row[0], '%m/%d/%Y').date()
                if column_date == yesterday:
                    yesterday_row = str(i + 1)
                    today_row = str(i + 2)
                    add_today_row_if_missing(service, today_row, yesterday_row)
                    break
            except ValueError as e:
                # don't care if blank, move on to next one if it's a date
                continue
        if yesterday_row is None or today_row is None:
            # todo: if date row doesn't exist, add it
            # todo: copy formulas to new row
            pass

        calories_in_range = format_to_range(CALORIES_IN_COLUMN, yesterday_row)
        fitbit_tdee_range = format_to_range(FITBIT_CALORIES_OUT_COLUMN, yesterday_row)
        weight_range = format_to_range(WEIGHT_COLUMN, today_row)
        new_tdee_range = format_to_range(NEW_TDEE_COLUMN, today_row)

        print "New values added to cells: {}".format(
            ", ".join([calories_in_range, fitbit_tdee_range, weight_range, new_tdee_range]))

        data = [
            {
                'range': calories_in_range,
                'values': [[calories_in]]
            }, {
                'range': fitbit_tdee_range,
                'values': [[fitbit_calories_out]]
            }, {
                'range': weight_range,
                'values': [[weight]]
            }, {
                'range': new_tdee_range,
                'values': [[new_tdee]]
            }
        ]
        body = {
            'valueInputOption': 'RAW',
            'data': data
        }
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID, body=body).execute()

