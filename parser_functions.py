
import re
from bs4 import BeautifulSoup


# #########################################################################
# Parse functions
# #########################################################################
pattern = re.compile('^[^A-ZÄÖÜa-zäöüß]+|[^A-ZÄÖÜa-zäöüß\-:0-9.]*|[^A-ZÄÖÜa-zäöüß.]+$')


# =========================================================================
# filter_text(string) -> string
# =========================================================================
# - remove punctuations
# =========================================================================
def filter_text(text):
    tr = str.maketrans({'.': ' ', ',': ' ', '!': ' ', '?': ' ', ';': ' '})
    return text.translate(tr)


# =========================================================================
# filter_word(string) -> [string]
# =========================================================================
def filter_word(word):
    word = word.lower()
    filtered_word = pattern.sub('', word)

    # if we have '.' in the word (z.B., u.a. ...), we do not remove the '.' at end
    # otherwise the '.' will be removed
    if not re.search(r'^.+\..+', filtered_word):
        if filtered_word.endswith('.'):
            filtered_word = filtered_word[:-1]

    filtered_words = re.findall(r'[A-ZÄÖÜa-zäöüß\:0-9.]+[A-ZÄÖÜa-zäöüß\:0-9.]+-|[A-ZÄÖÜa-zäöüß\:0-9.-]*', filtered_word)
    filtered_words = list(filter(None, map(lambda c: re.sub(r'-$', '', c), filtered_words)))

    return filtered_words


# =========================================================================
# parse_json(json) -> dict
# =========================================================================
def parse_json(entry_content):
    # Currently regexp is used to fix entries like
    # <b>I</b><span style="font-weight: 300;">ntegration  -->  Integration
    # <strong>V</strong>olatility                         -->  Volatility
    # TODO: search a solution with soup instead of regexp
    entry_content = re.sub(r'<strong>|</strong>', '', entry_content)
    entry_content = re.sub(r'<span.*?>', '<b>', entry_content)
    entry_content = re.sub(r'</span>', '</b>', entry_content)
    entry_content = re.sub(r'</b><b>', '', entry_content)
    soup = BeautifulSoup(entry_content, features='html.parser')

    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()

    entry_text = ' '.join(soup.stripped_strings)
    entry_words = entry_text.split()

    string_dict = dict()
    for word in entry_words:
        # remove not allowed characters
        words = filter_word(word)

        for filtered_word in words:
            # create or update entry in count map
            if len(filtered_word) > 0:
                # Count the existing/new words
                value_from_map = string_dict.get(filtered_word)
                if value_from_map is None:
                    string_dict[filtered_word] = 1
                else:
                    string_dict[filtered_word] = value_from_map + 1

    # Sorting the map by key
    sorted_string_list = sorted(string_dict.items(), key=lambda x: x[0])

    print('LIST ', sorted_string_list)

    # sorted_string_dict = dict(sorted_string_list)
    #print('DICT ', sorted_string_dict)

    # store the content for possible manual checks
    entry_text = entry_text.replace("\n\n", "\n")
    entry_text = entry_text.replace("\t", " ")

    return {'words': sorted_string_list, 'content': entry_text}
