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
        self.calories_in, self.fitbit_calories_out = get_calorie_data()
        self.weight, self.body_fat_percentage = get_weight_data()
        print self.calories_in, self.fitbit_calories_out
        print self.weight, self.body_fat_percentage

    def get_tdee(self):
        self.new_tdee = parse_tdee_website(self.AGE, self.GENDER, self.weight, self.HEIGHT_IN_INCHES,
                                           self.ACTIVITY_LEVEL, self.body_fat_percentage)
        print self.new_tdee

    def add_to_google_sheet(self):
        if self.new_tdee is None or self.calories_in is None or self.fitbit_calories_out is None or self.weight is None:
            raise Exception('One or more API calls failed.')
        write_to_sheet(self.calories_in, self.fitbit_calories_out, self.weight, self.new_tdee)


if __name__ == '__main__':
    summary = CalorieSummary()
    summary.get_fitbit_data()
    summary.get_tdee()
    summary.add_to_google_sheet()
