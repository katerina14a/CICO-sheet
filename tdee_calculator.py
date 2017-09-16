import re
import requests
from bs4 import BeautifulSoup


def parse_tdee_website(age, gender, pounds, height, activity_level, body_fat_percentage):
    if pounds is None or body_fat_percentage is None:
        return None

    endpoint = 'https://tdeecalculator.net/result.php?s=imperial&age={}&g={}&lbs={}&in={}&act={}&bf={}&f=1'.format(
        age, gender, pounds, height, activity_level, body_fat_percentage
    )
    print "Calling TDEE endpoint: {}".format(endpoint)
    r = requests.get(endpoint)
    soup = BeautifulSoup(r.text, 'html.parser')
    for i, e in enumerate(soup.find(id="tdee-cals").descendants):
        if i == 4 and len(e) == 5 and e[1] == ',':
            calories_in = int(re.sub('[,]', '', e))
            return calories_in
    return None
