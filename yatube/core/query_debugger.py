import functools
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
