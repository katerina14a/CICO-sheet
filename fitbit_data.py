import base64
import urllib2
import urllib
import sys
import json
import os

import datetime

from fitbit_client_constants import CLIENT_ID, CLIENT_SECRET

# This is the Fitbit URL to use for the API call
fitbit_url = "https://api.fitbit.com/1/user/-/profile.json"

# Use this URL to refresh the access token
token_url = "https://api.fitbit.com/oauth2/token"

# Get and write the tokens from here
token_file = os.path.dirname(os.path.realpath(__file__)) + "/tokens.txt"

# Some constants defining API error handling responses
TOKEN_REFRESHED_OK = "Token refreshed OK"
ERROR_IN_API = "Error when making API call that I couldn't handle"


# Get the config from the config file.  This is the access and refresh tokens
def get_config():
    print "Reading from the config file"

    # Open the file
    file_obj = open(token_file, 'r')

    # Read first two lines - first is the access token, second is the refresh token
    access = file_obj.readline()
    refresh = file_obj.readline()

    # Close the file
    file_obj.close()

    # See if the strings have newline characters on the end.  If so, strip them
    if access.find("\n") > 0:
        access = access[:-1]
    if refresh.find("\n") > 0:
        refresh = refresh[:-1]

    # Return values
    return access, refresh


def write_config(access, refresh):
    print "Writing new token to the config file"
    print "Writing this: " + access + " and " + refresh

    # Delete the old config file
    os.remove(token_file)

    # Open and write to the file
    file_obj = open(token_file, 'w')
    file_obj.write(access + "\n")
    file_obj.write(refresh + "\n")
    file_obj.close()


# Make a HTTP POST to get a new access token
def get_new_access_token(refresh):
    print "Getting a new access token"

    # Form the data payload
    body_text = {'grant_type': 'refresh_token', 'refresh_token': refresh}
    # URL Encode it
    body_url_encoded = urllib.urlencode(body_text)
    print "Using this as the body when getting access token >>" + body_url_encoded

    # Start the request
    token_request = urllib2.Request(token_url, body_url_encoded)

    # Add the headers, first we base64 encode the client id and client secret with a : in between and create the
    # authorization header
    token_request.add_header('Authorization', 'Basic ' + base64.b64encode(CLIENT_ID + ":" + CLIENT_SECRET))
    token_request.add_header('Content-Type', 'application/x-www-form-urlencoded')

    # Fire off the request
    try:
        token_response = urllib2.urlopen(token_request)

        # See what we got back.  If it's this part of  the code it was OK
        full_response = token_response.read()

        # Need to pick out the access token and write it to the config file.  Use a JSON manipulation module
        response_json = json.loads(full_response)

        # Read the access token as a string
        new_access_token = str(response_json['access_token'])
        new_refresh_token = str(response_json['refresh_token'])
        # Write the access token to the ini file
        write_config(new_access_token, new_refresh_token)

        print "New access token output >>> " + full_response
    except urllib2.URLError as e:
        # Getting to this part of the code means we got an error
        print "An error was raised when getting the access token.  Need to stop here"
        print e.code
        print e.read()
        sys.exit()


# This makes an API call.  It also catches errors and tries to deal with them
def make_api_call(fitbit_endpoint, access, refresh):
    # Start the request
    req = urllib2.Request(fitbit_endpoint)

    # Add the access token in the header
    req.add_header('Authorization', 'Bearer ' + access)
    req.add_header('Accept-Language', 'en_US')

    # Fire off the request
    try:
        # Do the request
        response = urllib2.urlopen(req)
        # Read the response
        full_response = response.read()

        # Return values
        return True, full_response
    # Catch errors, e.g. A 401 error that signifies the need for a new access token
    except urllib2.URLError as e:
        print "Got this HTTP error: " + str(e.code)
        http_error_message = e.read()
        print "This was in the HTTP error message: " + http_error_message
        # See what the error was
        if e.code == 401 and http_error_message.find("Access token expired") > 0:
            get_new_access_token(refresh)
            return False, TOKEN_REFRESHED_OK
        # Return that this didn't work, allowing the calling function to handle it
        return False, ERROR_IN_API


def make_request(endpoint):
    # Get the config
    access_token, refresh_token = get_config()

    # Make the API call
    request_successful, response_data = make_api_call(endpoint, access_token, refresh_token)

    if request_successful:
        return json.loads(response_data)
    else:
        if response_data == TOKEN_REFRESHED_OK:
            return make_request(endpoint)
        else:
            return None


def get_calorie_data():
    calories_in = None
    calories_out = None

    yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime('%Y-%m-%d')
    calories_in_data = make_request('https://api.fitbit.com/1/user/-/foods/log/date/{}.json'.format(yesterday))
    calories_out_data = make_request('https://api.fitbit.com/1/user/-/activities/date/{}.json'.format(yesterday))

    if calories_in_data:
        calories_in = calories_in_data["summary"]["calories"]
    if calories_out_data:
        calories_out = calories_out_data["summary"]["caloriesOut"]
    return calories_in, calories_out


def get_weight_data():
    weight = None
    fat = None
    today = datetime.date.today().strftime('%Y-%m-%d')
    weight_data = make_request('https://api.fitbit.com/1/user/-/body/log/weight/date/{}.json'.format(today))
    if weight_data:
        recent_weight = weight_data["weight"][-1]
        weight = recent_weight["weight"]
        fat = recent_weight["fat"]
    return weight, fat


if __name__ == '__main__':
    print "Fitbit API Test Code"

    # Get the config
    access_token, refresh_token = get_config()

    # Make the API call
    request_successful, response_data = make_api_call(fitbit_url, access_token, refresh_token)

    if request_successful:
        print response_data
    else:
        if response_data == TOKEN_REFRESHED_OK:
            print "Refreshed the access token. Can go again"
        else:
            print ERROR_IN_API
