# -*- coding: utf-8 -*- 
import calendar, datetime, time
from dateutil.relativedelta import relativedelta

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

MONTHS_OF_YEAR = 12


def current_date():
    """Get current date

    Args:
        None.
    Returns:
        date. The current date.
    """
    return time.strftime(DEFAULT_SERVER_DATE_FORMAT)


def current_time():
    """Get current time of current date

    Args:
        None.

    Returns:
        datetime. The curent time of current date.
    """
    return time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)


def str_to_date(date):
    """Convert string to date type
    Args:
        date (string or unicode). Date string that need to convert
        
    Returns:
        date. If passed date is unicode or string then we return converted date
        otherwise we return itself.
        
    Expamples:
        >>> str_to_date('2015-03-25')
        >>> datetime.date(2015, 3, 25)
    """
    try:
        return datetime.datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT).date()
    except:
        return date


def str_to_datetime(dt):
    """Convert string to datetime type
    Args:
        dt (string or unicode). Datetime string that need to convert

    Returns:
        datetime. If passed date is unicode or string then we return converted datetime
        otherwise we return itself.

    Expamples:
        >>> str_to_date('2015-03-25 19:21:12')
        >>> datetime.datetime(2015, 3, 25, 19, 21, 12)
    """
    try:
        return datetime.datetime.strptime(dt, DEFAULT_SERVER_DATETIME_FORMAT)
    except:
        return dt


def date_to_str(date):
    """Converts a ``datetime.date`` into a value that can be written in a ``fields.date()``.
    Args:
        date (datetime.date). date that need to convert to string

    Returns:
        string. If ``date`` is not a date, returns ``False``, which will be interpreted by OE as a null value.

    Examples:
        >>> date_to_str(datetime.date(2015, 3, 25))
        >>> '2015-03-25'
    """
    try:
        return date.strftime(DEFAULT_SERVER_DATE_FORMAT)
    except AttributeError:
        return False
    return date

def date_to_datetime(dt, str=False):
    """Date to datetime"""
    dt = str_to_date(dt)
    dt_with_time = datetime.datetime.combine(dt, datetime.time.min)
    if not str:
        return dt_with_time
    return datetime_to_str(dt_with_time)

def datetime_to_str(dt):
    """Converts a ``datetime.date`` into a value that can be written in a ``fields.datetime()``.
    Args:
        dt (datetime.datetime). date that need to convert to string

    Returns:
        string. If ``dt`` is not a datetime, returns ``False``, which will be interpreted by OE as a null value.

    Examples:
        >>> date_to_str(datetime.datetime(2015, 3, 25, 12, 30, 0))
        >>> '2015-03-25 12:30:00'
    """
    try:
        return dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
    except AttributeError:
        return False
    return dt

def datetime_to_date(dt, str=False):
    """Convert datetime to date"""
    dt = str_to_datetime(dt)
    if not str:
        return dt.date()
    return date_to_str(dt.date())

def date_equal(date1, date2):
    """Check to see whether date1 is equal to date2 or not"""
    return str_to_date(date1) == str_to_date(date2)


def date_less(date1, date2):
    """Check to see whether date1 is less than date2 or not"""
    return str_to_date(date1) < str_to_date(date2)


def date_less_equal(date1, date2):
    """Check to see whether date1 is less than or equal to date2 or not"""
    return str_to_date(date1) <= str_to_date(date2)


def days_of_year(year):
    """Number of days in year: 365 or 366
    Args:
        year (int): year need to get number of dates

    Returns:
        int. 365 or 366

    Examples:
        >>> days_of_year(2015)
        >>> 315
    """
    return calendar.isleap(year) and 366 or 365


def days_of_month(date):
    """Number of days of month which contains date.
    Args:
        date (string or datetime.date: date contains month we need to get

    Returns:
        int. Number of days of month which contain passed date.

    Examples:
        >>> days_of_month('2015-03-25')
        >>> 31
    """
    date = str_to_date(date)
    return calendar.monthrange(date.year, date.month)[1]


def date_after_n_days(date, n):
    """Date after n days
    Args:
        date (string or datetime.date): from date
        n (int): number of days after from date

    Returns:
        datetime.date or False

    Examples:
        >>> date_after_n_days('2015-03-25', 6)
        >>> datetime.date(2015, 3, 31)
    """
    try:
        return str_to_date(date) + relativedelta(days=+n)
    except:
        return False

def datetime_after_n_days(dt, n):
    """Datetime after n days
    Args:
        date (string or datetime.datetime): from datetime
        n (int): number of days after from datetime

    Returns:
        datetime.datetime or False

    Examples:
        >>> date_after_n_days('2015-03-25 19:00:00', 6)
        >>> datetime.date(2015, 3, 31 19:00:00)
    """
    try:
        return str_to_datetime(dt) + relativedelta(days=+n)
    except:
        return False

def date_before_n_days(date, n):
    """Date before n days
    Args:
        date (string or datetime.date): from date
        n (int): number of days before from date

    Returns:
        datetime.date or False

    Examples:
        >>> date_before_n_days('2015-03-25', 6)
        >>> datetime.date(2015, 3, 19)
    """
    try:
        return date_after_n_days(date, -n)
    except:
        return False


def first_date_of_month(date, str=False):
    """Get the first date of month
    Args:
        date (string or datetime.date): date contains month we want to get first date

    Returns:
        datetime.date: first date of the month

    Examples:
        >>> first_date_of_month('2015-03-25')
        >>> datetime.date(2015, 3, 1)
    """
    first_date = str_to_date(date) + relativedelta(day=1)
    if str:
        return date_to_str(first_date)
    return first_date


def last_date_of_month(date, str=False):
    """Return the last date of month.
    Args:
        date (string or datetime.date): date contains month we want to get last date

    Returns:
        datetime.date: last date of the month

    Examples:
        >>> last_date_of_month('2015-03-25')
        >>> datetime.date(2015, 3, 31)
    """
    last_date = str_to_date(date) + relativedelta(day=1, months=+1, days=-1)
    if str:
        return date_to_str(last_date)
    return last_date


def number_days_between_date(date1, date2):
    """Return number of days between 2 date
    Args:
        date1 (string or datetime.date): from date
        date2 (string or datetime.date): to date

    Returns:
        int. Number of days between two dates

    Examples:
        >>> number_days_between_date('2015-03-25', '2015-03-29')
        >>> 4
    """
    return abs((str_to_date(date1) - str_to_date(date2)).days)


def first_date_of_next_month(date, month=1):
    """
    Return the first date of next month(s)
    Eg: First date of month which contains date: 15/01/2013 is: 01/02/2013
    """
    return str_to_date(date) + relativedelta(day=1, months=+month)


def first_date_of_previous_month(date, month=1):
    """
    Return the first date of next month(s)
    Eg: First date of month which contains date: 15/01/2013 is: 01/12/2012
    """
    return str_to_date(date) + relativedelta(day=1, months=-month)


def date_after_next_month(date, month=1):
    """
    Return date after next month
    Eg: date after 2 month from 15/01/2013 is: 15/03/2013
    """
    return str_to_date(date) + relativedelta(months=+month)


def last_date_of_next_month(date, month=1):
    """
    Return last date of next month which contains date
    Eg: last date of next month which contains 15/01/2013 is: 28/02/2013
    """
    return date + relativedelta(day=1, months=+month, days=-1)


def date_after_previous_month(date):
    """
    Return date after previous month
    Eg: date after 2 month from 15/03/2013 is: 15/02/2013
    """
    return str_to_date(date) + relativedelta(months=-1)


def total_days(date, number_of_month):
    """
    Return number of days between date and n month(s) after it
    Eg: date = 15/01/2013 and number of months are 2; is: 59 days
    """
    date = str_to_date(date)
    new_date = date + relativedelta(months=+number_of_month)
    return (new_date - date).days


def is_first_day_of_month(date):
    """
    Check this date whether is first date of month or not
    """
    return (str_to_date(date).day == 1) and True or False


def last_day_of_month(date):
    """Get the last day of month
    Args:
        date (string or datetime.date): date contains month we need to get last date
    Eg: the last day of month which contains 01/01/2013 is: 31
    """
    return days_of_month(str_to_date(date))


def is_last_day_of_month(date):
    """
    Check this date whether is last date of month or not
    """
    return (str_to_date(date).day == last_day_of_month(date)) and True or False


def diff_month(date_from, date_to):
    """Get number of months between two dates
    Args:
        date_from (string or date): starting date
        date_to (string or date): ending date
    """
    d1 = str_to_date(date_to)
    d2 = str_to_date(date_from)
    return (d1.year - d2.year) * MONTHS_OF_YEAR + d1.month - d2.month


def get_day_of_week(date):
    """Get day number in week
    -Monday: 1
    -Tuesday: 2
    -...
    -Sunday: 7
    Args:
        date: string or date
    Examples:
    >>> get_day_of_week('2015-03-25')
    >>> 3
    """
    date = str_to_date(date)
    return date.isoweekday()


def get_week_of_year(date):
    """get week number from date"""
    date = str_to_date(date)
    return date.isocalendar()[1]

def week_range(date):
    """Find the first & last day of the week for the given day.
    Assuming weeks start on Sunday and end on Saturday.
    Returns a tuple of ``(start_date, end_date)``.
    """
    # isocalendar calculates the year, week of the year, and day of the week.
    # dow is Mon = 1, Sat = 6, Sun = 7
    year, week, dow = date.isocalendar()

    # Find the first day of the week.
    if dow == 7:
        # Since we want to start with Sunday, let's test for that condition.
        start_date = date
    else:
        # Otherwise, subtract `dow` number days to get the first day
        start_date = date - datetime.timedelta(dow)

    # Now, add 6 for the last day of the week (i.e., count up to Saturday)
    end_date = start_date + datetime.timedelta(6)

    return (start_date, end_date)

def convert_month_number_to_text(date):
    """Get Month Name from datetime
    Imput: date or string
    Output: Month Name"""
    date = str_to_date(date)
    return date.strftime('%B')


def convert_float_to_hour(fl):
    """Convert float value to hour str
    Example:
    >>>>> convert_float_to_hour(1.9)
    >>>>> 1:54
    """
    total_minutes = fl * 60
    hour = int(total_minutes / 60)
    minute = int(total_minutes - hour * 60)
    return '%s:%s' % (hour, minute)


def diff_hour(datetime_start, datetime_stop):
    """
    Delta hours between datetime start to datetime stop
    """
    diff = str_to_datetime(datetime_stop) - str_to_datetime(datetime_start)
    return float(diff.days) * 24 + (float(diff.seconds) / 3600)
