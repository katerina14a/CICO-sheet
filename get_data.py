import datetime

from fitbit_data import get_calorie_data, get_weight_data
from google_sheet import write_to_sheet
from tdee_calculator import parse_tdee_website


def calculate_age(born):
    today = datetime.date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


class CalorieSummary:
    def __init__(self):
        self.calories_in = 0
        self.fitbit_calories_out = 0
        self.weight = 0
        self.body_fat_percentage = 0
        self.new_tdee = 0

        # non changing values
        self.HEIGHT_IN_INCHES = 67
        self.AGE = calculate_age(datetime.date(1992, 5, 31))
        self.GENDER = 'female'
        self.ACTIVITY_LEVEL = '1.2'  # sedentary

    def get_fitbit_data(self):
        print "Getting calories in and calories out"
        self.calories_in, self.fitbit_calories_out = get_calorie_data()
        print self.calories_in, self.fitbit_calories_out
        print "Getting weight and body fat percentage"
        self.weight, self.body_fat_percentage = get_weight_data()
        print self.weight, self.body_fat_percentage

    def get_tdee(self):
        print "Parsing TDEE website to get new TDEE"
        self.new_tdee = parse_tdee_website(self.AGE, self.GENDER, self.weight, self.HEIGHT_IN_INCHES,
                                           self.ACTIVITY_LEVEL, self.body_fat_percentage)
        print self.new_tdee

    def add_to_google_sheet(self):
        self.check_for_none()
        print "Writing new values to Google Sheet"
        write_to_sheet(self.calories_in, self.fitbit_calories_out, self.weight, self.new_tdee)

    def check_for_none(self):
        none_values = []
        if self.new_tdee is None:
            none_values.append('new_tdee')
        if self.calories_in is None:
            none_values.append('calories_in')
        if self.fitbit_calories_out is None:
            none_values.append('fitbit_calories_out')
        if self.weight is None:
            none_values.append('weight')
        if len(none_values) > 0:
            raise Exception('One or more required fields are None: {}'.format(', '.join(none_values)))


if __name__ == '__main__':
    summary = CalorieSummary()
    summary.get_fitbit_data()
    summary.get_tdee()
    summary.add_to_google_sheet()
