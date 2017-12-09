"""
Compare lists of strings using Python's difflib and other strategies that may be more appropriate
Original intent: Comparing 2017 NBA mock drafts to the actual 2017 NBA draft, retrieve similarity scores
that can be used to help evaluate the accuracy of each of the mock drafts
"""

#!/usr/bin/env python3

from sys import stdin, stdout
from difflib import SequenceMatcher, get_close_matches
from datetime import datetime
from enum import Enum, unique
import fileinput
import re

class DraftRanking():
    """A class describing drafts, whether actual or mock"""
    def __init__(self, org_name, time_of_update, player_list):
        self.org_name = org_name
        self.time_of_update = time_of_update
        self.player_list = player_list

    def correct_name(self, old_name, new_name):
        """Change a name in the player list. Assumes that each name in the list is unique"""
        index = self.player_list.index(old_name)
        self.player_list[index] = new_name

    def is_official(self):
        """Indicates whether this DraftRanking is from an official organization"""
        return self.org_name.lower() in DraftRanking.offical_orgs()

    @classmethod
    def offical_orgs(cls):
        """Returns a set of orgs from whom a DraftRanking relects the official order"""
        return {'nba', 'nfl', 'nhl'}

    @classmethod
    def attrs(cls):
        """Returns a tuple of the attributes of DraftRanking"""
        return (DraftAttr.ORG, DraftAttr.TIME, DraftAttr.PLAYER)

    @classmethod
    def init_args_template(cls):
        dr_args = [None for i in range(len(DraftAttr))]
        dr_args[DraftAttr.PLAYER.value] = []
        return dr_args

@unique
class DraftAttr(Enum):
    ORG = 0
    TIME = 1
    PLAYER = 2

def guess_true_year(last_two_digits):
    """
    If a year is written with only two digits, take an educated guess as to which century
    Current approach: allow mock drafts to be made for up to 2 years in the future
    """
    try:
        if last_two_digits not in range(0, 100):
            raise ValueError('The program screwed up!')
    except ValueError as v:
        raise v

    current_year = datetime.today().year
    first_two = current_year // 100 if last_two_digits <= (current_year%100 + 2) else current_year//100 - 1
    return first_two*100 + last_two_digits

def within_month(possible_day, month, year):
    """Determine if a given day of a given month exists"""
    if possible_day < 1 or possible_day > 31:
        return False
    if month in (1, 3, 5, 7, 8, 10, 12) or (month != 2 and possible_day <= 30) or possible_day <= 28:
        return True
    # by this point, only Feb 29 is a possible date
    if month == 2 and possible_day == 29:
        # determine if year is a leap year (divisible by 4 but not by 100 unless also by 400)
        if year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
            return True

    return False

def string_to_YMD(date_string, dt_string):
    """
    Attempt to find the year, month, and day from a string that describes a date and a time
    Assumptions:
     - slash(es) or hyphens will only be used to describe a date
     - Most common ways to represent date: "Word ##, ####"; "##/##/(##)##"; "####-##-##"
     - A month represented in word form ought to be immediately preceded or succeeded by the day
     - Presumably, the only reason a 4-digit number would appear is to represent the year
     - Possible formats involving slashes: (M)M/(D)D/(YY)YY, (D)D/(M)M/(YY)YY, (YY)YY/(M)M/(D)D
    """
    all_months = dict(january=1, february=2, march=3, april=4, may=5, june=6, july=7, august=8, september=9, october=10, november=11, december=12)
    year = month = day = 0

    # If you try to break this, it will break.
    
    # Check for month in word form; this program will require the word to have at least 3 letters
    # Also attempt to find 1- or 2-digit numbers immediately before and after
    # Also tries to account for ordinal phrases such as "5th of November" or "May the 4th"
    # but *not* if an ordinal number is written out, e.g. "first" or "thirtieth", forget that
    m_pattern = r'(?<![:\d])(\d{1,2})?(?:[a-zA-Z]{2})?\s*(?:of)?\s*([a-zA-Z]{3,})\s*(?:the)?\s*(\d{1,2})?(?:[a-zA-Z]{2})?(?![:\d])'
    word_format = re.search(m_pattern, date_string)
    if word_format:
        word = word_format[2].lower()
        # if the month was spelled out entirely, finding it is O(1) time, if abbrev'ed, O(n)
        if word in all_months:
            month = all_months[word]
        else:
            for m in all_months:
                if word in m:
                    month = all_months[m]
                    break

        # if month was successfully found, day should be immediately before or after it
        if month and any((word_format[1], word_format[3])):
            if not all((word_format[1], word_format[3])):
                day = int(word_format[3]) if word_format[3] else int(word_format[1])
                # if day was also successfully found, only year should remain
                year_string = date_string[:word_format.start()] + date_string[word_format.end():]
                find_year = re.findall(r'(?<![:\d])\d{2}(?:\d{2})?(?![:\d])', year_string)
                # there should only be one match
                if len(find_year) == 1:
                    year = int(find_year[0])
                    if year < 100:
                        year = guess_true_year(year)

                    if within_month(day, month, year):
                        return year, month, day
            else:
                # with two 1-/2-digit numbers to consider, see if only one of them can be the day
                nums = tuple(int(word_format[1]), int(word_format[3]))
                for i in range(len(nums)):
                    year = nums[i]
                    day = nums[len(nums) - 1 - i]
                    if within_month(day, month, guess_true_year(year)) and not within_month(year, month, guess_true_year(day)):
                        return guess_true_year(year), month, day

    # now check for slashes or hyphens
    match = re.search(r'(\d+)[/.-](\d+)[/.-](\d+)', date_string)
    first, second, third = (int(i) for i in match.groups())
    # try to eliminate/confirm possibilities out of formats M->D->Y, D->M->Y, Y->M->D
    if second > 12: # then only M->D->Y is possible
        month, day, year = first, second, third if third > 99 else guess_true_year(third)
        if within_month(day, month, year):
            return year, month, day
    elif first > 12: # then M->D->Y is impossible
        # see if only one of D->M->Y or Y->M->D is possible
        month = second
        first_as_year = first if first > 99 else guess_true_year(first)
        third_as_year = third if third > 99 else guess_true_year(third)
        if within_month(first, month, third_as_year) and not within_month(third, month, first_as_year):
            return third_as_year, month, first
        if within_month(third, month, first_as_year) and not within_month(first, month, third_as_year):
            return first_as_year, month, third
    else:
        # by now, the numbers are either ambiguous or impossible with the three formats
        print('Could not determine date from the following line:')
        print(dt_string)
        print('Please input date in the following format: YYYYY-MM-DD')
        stdout.flush()
        date = stdin.readline().rstrip('\n')
        year, month, day = (int(i) for i in day.split('-'))
        return year, month, day

def string_to_HMS(dt_string):
    """
    Attempt to find the hour, minute, and second from a string that describes a date and a time
    Assumptions:
     - colon(s) will and only will be used to describe a time
     - standard hour-minute-second-am/pm format
     - hour and minute must be specified, while second and am/pm specification is optional
    """
    hour = minute = second = 0
    date_string = dt_string

    # If you try to break this, it will break.
    try:
        match = re.search(r'(\d{1,2}):(\d{2})(?::(\d{2}))?(?!\d)(?:\s*([aApP]\.?[mM]\.?))?', dt_string)
        
        hour = int(match[1])
        minute = int(match[2])

    # if colons didn't work, just give up and warn that time could not be extracted from dt_string
    # raise an Exception, show dt_string and ask user to manually input time
    # I'd like to also show org name, but that'd require restructuring this program
    except TypeError as t_e:
        if 'NoneType' in t_e.args:
            print('Could not determine time from the following line:')
            print(dt_string)
            print('Please input time (as on a 24-hour clock) in the following format: HH:MM:SS')
            print('(If time is not known, write 00:00:00)')
            stdout.flush()
            time = stdin.readline().rstrip('\n')
            hour, minute, second = (int(i) for i in time.split(':'))
        else:
            raise

    else:
        if match[3]:
            second = int(match[3])

        # if no am/pm is found, just assume the hour is good as is
        # otherwise, watch out for trickery like 12am/pm
        if match[4]:
            m = match[4].lower()
            if hour == 12 and 'a' in m:
                hour = 0
            if hour < 12 and 'p' in m:
                hour += 12

        # take the time out of dt_string
        date_string = dt_string[:match.start()] + dt_string[match.end():]

    return hour, minute, second, date_string

def string_to_datetime(dt_string):
    """
    Attempt to create a datetime object using a string that describes a date and a time
    """
    # since time should be easier to figure out than date,
    # find time and then take it out of the input for finding date
    hour, minute, second, date_string = string_to_HMS(dt_string)
    year, month, day = string_to_YMD(date_string, dt_string)

    return datetime(year, month, day, hour, minute, second)

def form_drafts():
    """
    each DraftRanking is inputted as follows:
    first line identifies the org that made the draft list
    second line indicates the date and time the list was updated
    each successive line contains a name, in order of draft position
    a blank line ends the current draft list; repeat for a new list
    """
    statuses = DraftRanking.attrs()
    current_status = statuses[0]
    dr_args = DraftRanking.init_args_template()
    with fileinput.input() as f:
        for line in f:
            line = line.rstrip('\n')
            if line:
                # right now, the assumption is that the list of players
                # is the last part of the args because its end is signified
                # by a blank line, which also ends the args overall
                if current_status is DraftAttr.PLAYER:
                    dr_args[current_status.value].append(line)
                else:
                    if current_status is DraftAttr.TIME:
                        # Try to convert the string into a datetime object
                        arg = string_to_datetime(line)
                    else:
                        arg = line

                    # put arg in dr_args
                    dr_args[current_status.value] = arg
                    # go to next status
                    current_status = statuses[current_status.value + 1]

            # a blank line indicates that all args for the current DraftRanking are complete
            else:
                yield DraftRanking(*dr_args)
                # wipe dr_args clean for another DraftRanking
                dr_args = DraftRanking.init_args_template()
                # reset current_status
                current_status = statuses[0]

def read():
    """
    Use the input to retrieve DraftRankings on which work can be done
    Returns DraftRankings in this format: Actual, [Mocks]
    """
    actual, mocks = None, []
    for dr in form_drafts():
        if dr.is_official():
            try:
                if actual:
                    raise Exception('Currently, this program can only work with one league and draft class!')
            except Exception as e:
                raise e
            actual = dr
        else:
            mocks.append(dr)

    return actual, mocks

def evaluate():
    """
    Given the actual draft order and various mock drafts,
    output measures of how close each mock was to the actual
    """
    # get the actual draft and a list of mock drafts
    actual, mocks = read()

    # Use difflib's get_close_matches function to try to account for
    # variations of names in lists
    # For example: go through names in the actual draft and
    # look for close but not exact matches in mock drafts.
    # (actually, check for membership BEFORE finding close matches)
    # for each match, ask the user if the two names are the same
    # and if they are, change the name in the mock draft's list

    # May want a dict recording matches confirmed by the user
    # Since the dict should be capable of assigning multiple values to a key, I guess the values could be in a list
    # Remember, names that aren't in the actual draft don't matter
    # Iterate through actual draft, iterate through list of mocks, checking if name is present. If not, check dict(, look for close matches, ask user, edit dict), edit mock

    # Finding similarity scores:
    # (Right now, just using ratio())
    # Make a SequenceMatcher, assign actual draft to second seq, iterate through mocks
    # --assign to first seq, use string format to print name and ratio

if __name__ == "__main__":
    evaluate()
