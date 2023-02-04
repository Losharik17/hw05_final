import functools
import re
import time

from django.db import connection, reset_queries


def query_debugger(func):
    """Декоратор, который выводит в консоль информацию о количестве
    обращений к БД в функции или классе(для метода as_view)"""

    @functools.wraps(func)
    def inner_func(*args, **kwargs):
        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        print(f"Function : {func.__name__}")
        print(f"Number of Queries : {end_queries - start_queries}")
        print(f"Finished in : {(end - start):.3f}s")
        return result

    return inner_func


#
TRANSTABLE = (
    ("'", "'"),
    ('"', '"'),
    ("‘", "'"),
    ("’", "'"),
    ("«", '"'),
    ("»", '"'),
    ("“", '"'),
    ("”", '"'),
    ("–", "-"),  # en dash
    ("—", "-"),  # em dash
    ("‒", "-"),  # figure dash
    ("−", "-"),  # minus
    ("…", "..."),
    ("№", "#"),
    ("Щ", "Sch"),
    ("Щ", "SCH"),
    ("Ё", "Yo"),
    ("Ё", "YO"),
    ("Ж", "Zh"),
    ("Ж", "ZH"),
    ("Ц", "Ts"),
    ("Ц", "TS"),
    ("Ч", "Ch"),
    ("Ч", "CH"),
    ("Ш", "Sh"),
    ("Ш", "SH"),
    ("Ы", "Yi"),
    ("Ы", "YI"),
    ("Ю", "YU"),
    ("Ю", "Yu"),
    ("Я", "Ya"),
    ("Я", "YA"),
    ("А", "A"),
    ("Б", "B"),
    ("В", "V"),
    ("Г", "G"),
    ("Д", "D"),
    ("Е", "E"),
    ("З", "Z"),
    ("И", "I"),
    ("Й", "J"),
    ("К", "K"),
    ("Л", "L"),
    ("М", "M"),
    ("Н", "N"),
    ("О", "O"),
    ("П", "P"),
    ("Р", "R"),
    ("С", "S"),
    ("Т", "T"),
    ("У", "U"),
    ("Ф", "F"),
    ("Х", "H"),
    ("Э", "E"),
    ("Ъ", "`"),
    ("Ь", "'"),
    ("щ", "sch"),
    ("ё", "yo"),
    ("ж", "zh"),
    ("ц", "ts"),
    ("ч", "ch"),
    ("ш", "sh"),
    ("ы", "yi"),
    ("ю", "yu"),
    ("я", "ya"),
    ("а", "a"),
    ("б", "b"),
    ("в", "v"),
    ("г", "g"),
    ("д", "d"),
    ("е", "e"),
    ("з", "z"),
    ("и", "i"),
    ("й", "j"),
    ("к", "k"),
    ("л", "l"),
    ("м", "m"),
    ("н", "n"),
    ("о", "o"),
    ("п", "p"),
    ("р", "r"),
    ("с", "s"),
    ("т", "t"),
    ("у", "u"),
    ("ф", "f"),
    ("х", "h"),
    ("э", "e"),
    ("ъ", "`"),
    ("ь", "'"),
    ("c", "c"),
    ("q", "q"),
    ("y", "y"),
    ("x", "x"),
    ("w", "w"),
    ("1", "1"),
    ("2", "2"),
    ("3", "3"),
    ("4", "4"),
    ("5", "5"),
    ("6", "6"),
    ("7", "7"),
    ("8", "8"),
    ("9", "9"),
    ("0", "0"),
)

RU_ALPHABET = [x[0] for x in TRANSTABLE]
EN_ALPHABET = [x[1] for x in TRANSTABLE]
ALPHABET = RU_ALPHABET + EN_ALPHABET


def translify(in_string, strict=True):
    """
    Translify russian text

    @param in_string: input string
    @type in_string: C{str}

    @param strict: raise error if transliteration is incomplete.
        (True by default)
    @type strict: C{bool}

    @return: transliterated string
    @rtype: C{str}

    @raise ValueError: when string doesn't transliterate completely.
        Raised only if strict=True
    """
    translit = in_string
    for symb_in, symb_out in TRANSTABLE:
        translit = translit.replace(symb_in, symb_out)

    if strict and any(ord(symb) > 128 for symb in translit):
        raise ValueError("Unicode string doesn't transliterate completely, "
                         "is it russian?")

    return translit


def slugify(in_string):
    """
    Prepare string for slug (i.e. URL or file/dir name)

    @param in_string: input string
    @type in_string: C{basestring}

    @return: slug-string
    @rtype: C{str}

    @raise ValueError: if in_string is C{str}, but it isn't ascii
    """
    try:
        u_in_string = str(in_string).lower()
    except UnicodeDecodeError:
        raise ValueError("We expects when in_string is str type,"
                         "it is an ascii, but now it isn't. Use unicode "
                         "in this case.")
    # convert & to "and"
    u_in_string = re.sub('\&amp\;|\&', ' and ', u_in_string)
    # replace spaces by hyphen
    u_in_string = re.sub('[-\s]+', '-', u_in_string)
    # remove symbols that not in alphabet
    u_in_string = ''.join([symb for symb in u_in_string if symb in ALPHABET])
    # translify it
    out_string = translify(u_in_string)
    # remove non-alpha
    return re.sub('[^\w\s-]', '', out_string).strip().lower()
