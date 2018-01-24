# Mock-Draft-Evaluator
Evaluate how close a mock draft's ranking was to the actual draft using some simple similarity metrics

## Setup
1. Make sure you have [Python 3](https://www.python.org/downloads/) installed and that you can run Python programs from your command line.
2. Clone or download this repository or its files. You can also make your own text files describing various drafts and mock drafts to use with the program. The files must follow this format:
   * Each draft must contain information describing what organization produced it and at what time it was updated, as well as a list of the players in the draft in order of draft position.
   * The first line is the name of the organization that produced the draft. For an actual draft, the organization should be the league to which the draft pertains, e.g. `NBA`.
   * The second line describes the date and time at which the draft was updated to its given state. For example, one could write `2017-07-21 18:00:00`. The program attempts to interpret a variety of date and time formats, but it's not very good, so please try to keep input reasonable and unambiguous! Note that year, month, day, hour, and minute figures are required (if hour or minute is unknown, a default value of `00` is suggested), but second is not and time zones are not currently accounted for.
   * Each line from the third onward contains the name of a player that was drafted or projected to be drafted, in order of draft position.
   * Leave a blank line to indicate the completion of the draft description, that is to say, that all players in the draft or mock draft have been listed on the preceding lines. The last draft in the file does not have to end in a blank line, and can simply end with the name of the last player in that draft.
   * Repeat the above format for each draft or mock draft.

## Usage
1. Run `sequence_similarities.py` with a text file containing the input as a command line argument. For example, one possible command could be `py sequence_similarities.py 2017_NBA_drafts`.
2. If the program was unable to ascertain a date or a time from a line meant to describe date and time, it will ask for the user to input the date or time described by that line according to a specific format that generally conforms to ISO 8061. This process will repeat until all uncertainties are resolved.
3. The program will try to identify instances in which a player's name in a mock draft may have been spelled differently than in the actual draft. Whenever such an instance is found, the program will ask the user whether or not the two names indeed describe the same player. The user should not find themselves having to confirm or deny the equivalence of the exact same pair of names more than once within one execution of the program. However, these adjustments will not persist through multiple executions, so they will have to be made each time the program is run.
   * Note that periods are removed from names automatically, and so the program will not need to ask about a pair of names whose spellings only differ by the presence or absence of periods.

Once the program has completed this processing of the input, it will display each mock draft by organization name and similarity scores as measured by the SequenceMatcher class of Python's difflib module and an implementation of rank-biased overlap (a top-weighted, convergent similarity measure for indefinite rankings).

## Future Plans

* Be able to work with multiple draft classes (i.e. of different leagues and/or different years) in one execution
* Add more methods for measuring similarity
* Improve the display of results to be more readable and informative
* (Possibly) put information about drafts and their similarity scores into a database
