import unicodedata


def trim_string(s):
    return s.strip()


def is_graphic(char):
    """Check if a character is a graphic character."""
    return unicodedata.category(char) in ['L', 'M', 'N', 'P', 'S', 'Z']


def preprocess_string(s: str) -> str:
    s = ''.join(char for char in s if not is_graphic(char))
    s = s.replace("\uFEFF", "")
    return s


def find_named_matches(pattern, s):
    match = pattern.match(s)
    if match:
        return match.groupdict()
    return {}


def find_all_string_submatch_index(pattern, s, n=-1):
    matches = []

    for match in pattern.finditer(s):
        # Extracting the start and end indices of the match and all submatches
        # This is equivalent to flattening the match indices as done in the Go code
        flat_indices = []
        for group in range(len(match.groups()) + 1):  # +1 to include the whole match
            flat_indices.extend(match.span(group))

        matches.append(flat_indices)

        # If n is specified and we've reached the limit, break
        if n > 0 and len(matches) >= n:
            break
    return matches


def split_with_regexp(pattern, s):
    # splitIndices = [match.span() for match in pattern.finditer(s)]
    splitIndices = find_all_string_submatch_index(pattern, s)

    result = []
    prevIndex = 0

    if not splitIndices:
        return [s]

    newSplitIndices = []
    for indices in splitIndices:
        newIndicie = []
        for i in range(0, len(indices), 2):
            ia, ib = indices[i], indices[i + 1]
            if i > 0:
                ya, yb = indices[i-2], indices[i-1]
                if ia == ya and ib == yb:
                    continue
            newIndicie.extend([ia, ib])
        newSplitIndices.append(newIndicie)

    splitIndices = newSplitIndices

    if splitIndices[0][0] == 0:
        result.append("")

    for indices in splitIndices:
        for i in range(0, len(indices), 2):
            ia, ib = indices[i], indices[i + 1]
            if prevIndex < ia:
                result.append(s[prevIndex:ia])
            result.append(s[ia:ib])
            prevIndex = ib

    if prevIndex < len(s):
        result.append(s[prevIndex:])

    return result


def reconciliate_split_match(match, minSubstrings, defaultSubstrings, excludeFn):
    str_ = "".join(match[i] for i in defaultSubstrings)
    if len(match) > minSubstrings:
        for i in range(minSubstrings, len(match)):
            if excludeFn and excludeFn(i):
                continue
            str_ += match[i]
    return str_
