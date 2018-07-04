"""
Compare lists of strings using Python's difflib and other strategies
that may be more appropriate

Original intent: Comparing 2017 NBA mock drafts to the actual 2017 NBA
draft, retrieve similarity scores that can be used to help evaluate the
accuracy of each of the mock drafts
"""

#!/usr/bin/env python3

from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher, get_close_matches
from enum import Enum, unique
from sys import stdin, stdout
import fileinput
import re

import rbo

class DraftRanking():
    """A class describing drafts, whether actual or mock"""

    def __init__(self, org_name, time_of_update, player_list):
        self.org_name = org_name
        self.time_of_update = time_of_update
        self.player_list = player_list
        self.player_set = set(player_list)

    def correct_name(self, old_name, new_name):
        """Change a name in the player list."""
        # presumably, each name in the list is unique
        index = self.player_list.index(old_name)
        self.player_list[index] = new_name
        # update the set too
        self.player_set.remove(old_name)
        self.player_set.add(new_name)

    def is_official(self):
        """Return whether this DraftRanking is from an official org."""
        return self.org_name.casefold() in DraftRanking.offical_orgs()

    @classmethod
    def offical_orgs(cls):
        """Return a set of orgs whose drafts are official."""
        # Can be updated as necessary
        return {'nba', 'nfl', 'nhl'}

    @classmethod
    def attrs(cls):
        """Return a tuple of the attributes of DraftRanking."""
        return (DraftAttr.ORG, DraftAttr.TIME, DraftAttr.PLAYER)

    @classmethod
    def init_args_template(cls):
        """Return a 'blank' list of DraftRanking constructor args."""
        dr_args = [None for i in range(len(DraftAttr))]
        dr_args[DraftAttr.PLAYER.value] = []
        return dr_args

@unique
class DraftAttr(Enum):
    """Represention of DraftRanking constructor args as list indices"""
    ORG = 0
    TIME = 1
    PLAYER = 2

def guess_true_year(last_two_digits):
    """
    If a year is written with only two digits,
    take an educated guess as to which century

    Current approach:
    allow mock drafts to be made for up to 2 years in the future
    """
    try:
        if last_two_digits not in range(0, 100):
            raise ValueError('The program screwed up! {} should be between 0 and 100'
                             .format(last_two_digits))
    except ValueError as v_e:
        raise v_e

    current_year = datetime.today().year
    first_two = (current_year // 100 if last_two_digits <= (current_year%100 + 2)
                 else current_year//100 - 1)
    return first_two*100 + last_two_digits

def within_month(possible_day, month, year):
    """Determine if a given day of a given month exists."""
    if possible_day < 1 or possible_day > 31:
        return False
    if (possible_day <= 28 or (month != 2 and possible_day <= 30)
            or month in (1, 3, 5, 7, 8, 10, 12)):
        return True
    # by this point, only Feb 29 is a possible date
    if month == 2 and possible_day == 29:
        # determine if year is a leap year, i.e.
        # divisible by 4 but not by 100 unless also by 400
        if year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
            return True

    return False

def string_to_YMD(date_string, dt_string):
    """
    Find year, month, and day from a string of date (and perhaps time).

    Assumptions:
     - slash(es) or hyphens will only be used to describe a date
     - Most common ways to represent date: "Word ##, ####"; "##/##/(##)##"; "####-##-##"
     - A month represented in word form ought to be immediately preceded or succeeded by the day
     - Presumably, the only reason a 4-digit number would appear is to represent the year
     - Possible formats involving slashes: (M)M/(D)D/(YY)YY, (D)D/(M)M/(YY)YY, (YY)YY/(M)M/(D)D
    """
    all_months = dict(
        january=1, february=2, march=3, april=4, may=5, june=6, july=7,
        august=8, september=9, october=10, november=11, december=12
        )
    year = month = day = 0

    # If you try to break this, it will break.

    # Check for month in word form; this program will require the word to have at least 3 letters
    # Also attempt to find 1- or 2-digit numbers immediately before and after
    # Also tries to account for ordinal phrases such as "5th of November" or "May the 4th"
    # but *not* if an ordinal number is written out, e.g. "first" or "thirtieth", forget that noise
    m_pattern = r'(?<![:\d])(\d{1,2})?(?:[a-zA-Z]{2})?\s*(?:of)?\s*([a-zA-Z]{3,})\s*(?:the)?\s*(\d{1,2})?(?:[a-zA-Z]{2})?(?![:\d])'
    word_format = re.search(m_pattern, date_string)
    if word_format:
        word = word_format.group(2).casefold()
        # if the month was spelled out in its entirety,
        # finding it is O(1) time; if month was abbrev'ed, O(n)
        if word in all_months:
            month = all_months[word]
        else:
            for month_name in all_months:
                if word in month_name:
                    month = all_months[month_name]
                    break

        # if month was successfully found, day should be immediately
        # before or after it
        if month and any((word_format.group(1), word_format.group(3))):
            if not all((word_format.group(1), word_format.group(3))):
                day = int(word_format.group(3)) if word_format.group(3) else int(word_format.group(1))
                # if day has also been found, only year should remain
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
                # with two 1- or 2-digit numbers to consider, see if
                # only one of them can be the day, knowing month and
                # positing the other number to be the year
                first, second = int(word_format.group(1)), int(word_format.group(3))
                first_as_year = guess_true_year(first)
                second_as_year = guess_true_year(second)
                if (within_month(first, month, second_as_year)
                        is not within_month(second, month, first_as_year)):
                    return ((second_as_year, month, first)
                            if within_month(first, month, second_as_year)
                            else (first_as_year, month, second))

    # now check for slashes or hyphens
    match = re.search(r'(\d+)[/.-](\d+)[/.-](\d+)', date_string)
    if match:
        first, second, third = (int(i) for i in match.groups())
        # try to eliminate/confirm possibilities of formats MDY, DMY, YMD
        if second > 12: # then only M->D->Y is possible
            month, day, year = first, second, third if third > 99 else guess_true_year(third)
            if within_month(day, month, year):
                return year, month, day
        elif first > 12: # then M->D->Y is impossible
            # see if only one of D->M->Y or Y->M->D is possible
            month = second
            first_as_year = first if first > 99 else guess_true_year(first)
            third_as_year = third if third > 99 else guess_true_year(third)
            if (within_month(first, month, third_as_year)
                    is not within_month(third, month, first_as_year)):
                return ((third_as_year, month, first)
                        if within_month(first, month, third_as_year)
                        else (first_as_year, month, third))

    # by now, the program was unable to unambiguously find the date and
    # will ask the user to input it manually
    print('Could not determine date from the following line:')
    print(dt_string)
    print('Please input date in the following format: YYYYY-MM-DD')
    stdout.flush()
    date = stdin.readline().rstrip('\n')
    print()
    year, month, day = (int(i) for i in date.split('-'))
    return year, month, day

def string_to_HMS(dt_string):
    """
    Find hour, minute, and second from a string of date and time.

    Assumptions:
     - colon(s) will and only will be used to describe a time
     - standard hour-minute-second-am/pm format
     - hour and minute must be specified, while
       second and am/pm specification are optional
     - a format with just hour and am/pm MAY be interpretable (WIP)
    """
    hour = minute = second = 0
    date_string = dt_string

    # If you try to break this, it will break.
    match = re.search(
        r'(\d{1,2}):(\d{2})(?::(\d{2}))?(?!\d)(?:\s*([aApP]\.?[mM]\.?))?',
        dt_string)

    if match:
        minute = int(match.group(2))
    # trying to account for hour+am/pm without min or sec
    else:
        match = re.search(
            r'(\d{1,2})()()\s*([aApP]\.?[mM]\.?)',
            dt_string)

        minute = 0

        # If many draft rankings don't have time specified or the
        # program can't figure them out, it's annoying for the user to
        # be asked about all of them. Perhaps just automatically
        # assign 00:00:00 as the time
        if not match:
            return hour, minute, second, date_string

    hour = int(match.group(1))

    if match.group(3):
        second = int(match.group(3))

    # if no am/pm is found, just assume the hour is good as is
    # otherwise, watch out for trickery like 12am/pm
    if match.group(4):
        am_pm = match.group(4).casefold()
        if hour == 12 and 'a' in am_pm:
            hour = 0
        if hour < 12 and 'p' in am_pm:
            hour += 12

    # take the time out of dt_string
    date_string = dt_string[:match.start()] + dt_string[match.end():]

    return hour, minute, second, date_string

def string_to_datetime(dt_string):
    """Given a string describing date and time, return a datetime."""
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
    with fileinput.input(openhook=fileinput.hook_encoded('utf-8')) as f_i:
        for line in f_i:
            line = line.rstrip('\n')
            if line:
                # for now, the assumption is that the player list is
                # the last of the args because its end is signified
                # by a blank line, which also ends the args overall
                if current_status is DraftAttr.PLAYER:
                    # remove periods from names
                    line = line.replace('.', '')
                    # casefold each name so that case will not be
                    # considered in comparisons between names
                    dr_args[current_status.value].append(line.casefold())
                else:
                    if current_status is DraftAttr.TIME:
                        # convert the string into a datetime object
                        arg = string_to_datetime(line)
                    else:
                        arg = line

                    # put arg in dr_args
                    dr_args[current_status.value] = arg
                    # go to next status
                    current_status = statuses[current_status.value + 1]

            # a blank line indicates that all args for the current
            # DraftRanking are complete
            else:
                yield DraftRanking(*dr_args)
                # wipe dr_args clean for another DraftRanking
                dr_args = DraftRanking.init_args_template()
                # reset current_status
                current_status = statuses[0]

    # hacky way to create final DR in the file
    yield DraftRanking(*dr_args)

def read():
    """
    Use the input to retrieve DraftRankings on which work can be done
    Returns DraftRankings in this format: Actual, [Mocks]
    """
    actual, mocks = None, []
    for draft in form_drafts():
        if draft.is_official():
            if actual:
                raise Exception('This program currently only works with one league/draft class!')
            actual = draft
        else:
            mocks.append(draft)

    if not actual:
        raise Exception('No official draft found!')
    if not mocks:
        raise Exception('No mock drafts found!')
    return actual, mocks

def standardize_variations(actual, mocks):
    """
    Use difflib's get_close_matches() to account for name variations

    Given an official draft and an iterable of mock drafts,
    look for possible instances of variations in spelling of names and
    adjust drafts so that each name is always spelled the same way
    """
    # dict: key is a name in the actual draft,
    #       value is a set of variations of that name found in mocks
    confirmed_matches = defaultdict(set)
    # a dict(? there may be a better way) of user-confirmed non-matches
    non_matches = defaultdict(set)

    # Iterate through actual draft, iterate through list of mocks, checking if name is present.
    # If not, check dict(, look for close matches, ask user, edit dict), edit mock
    # - an alternate algorithm could be to make mocks the outer loop,
    #   convert the player list into a set, and then loop the actual names
    #   but I think BOTH approaches are O(m*n^3), where m = # of mocks and n = # of names
    # - i GUESS DR could have an attribute player_set initialized with the instance
    for i in actual.player_list: # Should there be a method instead of accessing attribute directly?
        for j in mocks:
            mock_names = j.player_set
            if i not in mock_names:
                corrected = False
                for variation in confirmed_matches[i]:
                    if variation in mock_names:
                        j.correct_name(variation, i)
                        corrected = True
                        break
                if not corrected:
                    for close_match in get_close_matches(i, mock_names, n=len(mock_names)):
                        if (close_match not in non_matches[i]
                                and close_match not in actual.player_set):
                            response = input('Is {} the same person as {}? (yes/no)\n'
                                             .format(close_match, i)).casefold()
                            if 'y' in response:
                                confirmed_matches[i].add(close_match)
                                j.correct_name(close_match, i)
                                # This line is currently unnecessary:
                                # corrected = True
                                break
                            if 'n' in response:
                                non_matches[i].add(close_match)

def sequence_matcher_similarity(actual, mocks):
    """
    Given an official draft and mock drafts, calculate and return the
    similarity of each mock draft to the actual draft as measured by
    SequenceMatcher's method ratio()
    """
    # Make a SequenceMatcher with the actual draft as the second seq
    s_m = SequenceMatcher(b=actual.player_list)

    for mock in mocks:
        s_m.set_seq1(mock.player_list)
        yield mock, s_m.ratio()

def rbo_similarity(actual, mocks, p=0):
    """
    Given an official draft and mock drafts, calculate and return the
    similarity of each mock draft to the actual draft as measured by
    rank biased overlap
    """
    # if a value for p is not provided, use suggestion by RBO creators
    # of (1 - 1/k) where k is the length of the prefix
    if not p:
        p = 1 - 1/len(actual.player_list)
    for mock in mocks:
        yield mock, rbo.score(actual.player_list, mock.player_list)

def display_results(measure_names, measures):
    """
    Extremely rough code for displaying the orgs and their similarity scores in a table

    Able to accomodate for any number of rank similarity measures (as
    long the output window is wide enough to display all their names)
    """
    # for each measure, record the measure's name as it will be shown
    # in the table and the name's length or 7, whichever is greater
    col_lengths = list((name, max(len(name), 7)) for name in measure_names)
    # length of the first column: greatest length between all org names
    # as well as 'Organization' (the column name)
    offset = max(max(len(name) for name in measures[0]), len('Organization'))
    # number of characters in each line taking into account offset, all
    # column lengths, and the number of pipes (used as column dividers)
    # in each line
    line_length = offset + sum(i[1] for i in col_lengths) + 2 + len(col_lengths)

    print()
    print('-' * line_length)
    # table headers: 'Organization' and each measure name
    print(('|{:^{}}').format('Organization', offset),
          *(('{:^{}}').format(i[0], i[1]) for i in col_lengths),
          sep='|', end='|\n')
    print('-' * line_length)
    # create the rows of the table, one row for each mock draft
    for draft in measures[0]:
        # org name followed by each similarity score for the mock draft
        print(('|{:<{}}').format(draft, offset),
              *(('{:>{}.3%}').format(m[draft], c_l[1]) for c_l, m in zip(col_lengths, measures)),
              sep='|', end='|\n')
    print('-' * line_length)

def evaluate():
    """
    Given the actual draft order and various mock drafts,
    output measures of how close each mock was to the actual
    """
    # get the actual draft and a list of mock drafts
    actual, mocks = read()

    # try to adjust names in the mock drafts to have the same spelling
    # as in the actual draft
    standardize_variations(actual, mocks)

    # have to think about how to design the code to make adding
    # additional similarity measures a clean process and also how to
    # display all the info in an easy-to-read way
    ratios = dict((i.org_name, j) for i, j in sequence_matcher_similarity(actual, mocks))
    rbo_scores = dict((i.org_name, j) for i, j in rbo_similarity(actual, mocks))

    # kinda feels like these two variables should be linked together or
    # something, but it also seems unnecessary to do so
    measure_names = ('SequenceMatcher', 'RBO score')
    measures = (ratios, rbo_scores)

    # probably wanna have display_results include a 'time of update'
    # column so multiple mocks from same org can be compared
    display_results(measure_names, measures)

if __name__ == "__main__":
    evaluate()
