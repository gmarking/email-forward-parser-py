from .utils import split_with_regexp


def loop_regexes_replace(regexes, string) -> str:
    match = string
    for regex in regexes:
        current_match = regex.sub("", string)
        if len(current_match) < len(match):
            match = current_match
            break
    return match


def loop_regexes_split(regexes, string, highest_position):
    # Notes:
    # 1) Successful split must return list with at least 2 items
    #
    match = []
    match_other = []
    for regex in regexes:
        current_match = split_with_regexp(regex, string)
        current_match_other = regex.split(string)
        if len(current_match) > 1:
            if highest_position:
                if not match or len(match[0]) > len(current_match[0]):
                    match = current_match
                if not match_other or len(match_other[0]) > len(current_match_other[0]):
                    match_other = current_match_other
            else:
                match = current_match
                match_other = current_match_other
                break
    return match, current_match_other


def loop_regexes_match(regexes, string):
    # leave match a match object until we are returning, cleans up code
    match = None
    regex_matched = None
    match_index = 0

    for re in regexes:
        current_match = re.search(string)
        if not current_match:  # style note
            continue
        current_match_index = current_match.start()
        # grab match that is closer to beginning of string
        if match is None or current_match_index < match_index:
            match = current_match
            match_index = current_match_index
            regex_matched = re

    # Convert match from None to an empty list if no match is found
    if match is None:
        match = []
    else:
        match = [match.group(0)] + list(match.groups())
    return match, regex_matched
