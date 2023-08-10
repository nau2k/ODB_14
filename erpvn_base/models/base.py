import re, os, base64, zipfile, logging, datetime, calendar, pytz, random, string

from io import BytesIO
from dateutil.relativedelta import relativedelta
from requests import get
from datetime import timedelta
from requests.exceptions import SSLError, ConnectionError

from odoo import api, models, fields, _
from odoo.addons.erpvn_base.tools import utils
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.tools import remove_accents, formataddr

from ..controllers.my_ip import MY_IP_ROUTE

_logger = logging.getLogger(__name__)

class OdooBase(models.AbstractModel):
    _name = 'erpvn.base'
    _description = 'Base Model'

    def random_characters(length):
        return ''.join(random.choice(string.ascii_lowercase.upper() + string.digits) for i in range(length))

    def barcode_exists(self, barcode, model_name=None, barcode_field='barcode', inactive_rec=True):
        """
        Method to check if the barcode exists in the input model

        @param barcode: the barcode to check its existance in the model
        @param model_name: The technical name of the model to check. For example, product.template, product.product, etc. If not passed, the current model will be used
        @param barcode_field: the name of the field storing barcode in the corresponding model
        @param inactive_rec: search both active and inactive records of the model for barcode existance check. Please pass False for this arg if the model does not have active field

        @return: Boolean
        """
        Object = model_name and self.env[model_name] or self
        domain = [(barcode_field, '=', barcode)]
        if inactive_rec:
            found = Object.with_context(active_test=False).search(domain)
        else:
            found = Object.search(domain)
        if found:
            return True
        return False

    def get_ean13(self, base_number):
        if len(str(base_number)) > 12:
            raise UserError(_("Invalid input base number for EAN13 code"))
        # weight number
        ODD_WEIGHT = 1
        EVEN_WEIGHT = 3
        # Build a 12 digits base_number_str by adding 0 for missing first characters
        base_number_str = '%s%s' % (
            '0' * (12 - len(str(base_number))), str(base_number))
        # sum_value
        sum_value = 0
        for i in range(0, 12):
            if i % 2 == 0:
                sum_value += int(base_number_str[i]) * ODD_WEIGHT
            else:
                sum_value += int(base_number_str[i]) * EVEN_WEIGHT
        # calculate the last digit
        sum_last_digit = sum_value % 10
        calculated_digit = 0
        if sum_last_digit != 0:
            calculated_digit = 10 - sum_last_digit
        barcode = base_number_str + str(calculated_digit)
        return barcode

    def convert_time_to_utc(self, dt, tz_name=None, is_dst=None):
        """
        :param dt: an instance of datetime object to convert to UTC
        :param tz_name: the name of the timezone to convert. In case of no tz_name passed, this method will try to find the timezone in context or the login user record
        :param is_dst: respecting daylight saving time or not

        :return: an instance of datetime object in UTC (with timezone notation)
        :rtype: datetime
        """
        tz_name = tz_name or self._context.get('tz') or self.env.user.tz
        if not tz_name:
            raise ValidationError(
                _("Local time zone is not defined. You may need to set a time zone in your user's Preferences."))
        local = pytz.timezone(tz_name)
        local_dt = local.localize(dt, is_dst=is_dst)
        return local_dt.astimezone(pytz.utc)

    def convert_utc_time_to_tz(self, utc_dt, tz_name=None, is_dst=None):
        """
        Method to convert UTC time to local time
        :param utc_dt: datetime in UTC
        :param tz_name: the name of the timezone to convert. In case of no tz_name passed, this method will try to find the timezone in context or the login user record
        :param is_dst: respecting daylight saving time or not

        :return: datetime object presents local time
        """
        tz_name = tz_name or self._context.get('tz') or self.env.user.tz
        if not tz_name:
            raise ValidationError(
                _("Local time zone is not defined. You may need to set a time zone in your user's Preferences."))
        tz = pytz.timezone(tz_name)
        return pytz.utc.localize(utc_dt, is_dst=is_dst).astimezone(tz)

    def time_to_float_hour(self, dt):
        """
        This method will convert a datetime object to a float that present the corresponding time without date. For example,
            datetime.datetime(2019, 3, 24, 12, 44, 0, 307664) will become 12.733418795555554
        @param dt: datetime object
        @param type: datetime

        @return: The extracted time in float. For example, 12.733418795555554 for datetime.time(12, 44, 0, 307664)
        @rtype: float
        """
        return dt.hour + dt.minute / 60.0 + dt.second / (60.0 * 60.0) + dt.microsecond / (60.0 * 60.0 * 1000000.0)

    def _find_last_date_of_period_from_period_start_date(self, period_name, period_start_date):
        """
        This method finds the last date of the given period defined by the period_name and the start date of the period. For example:
        - if you pass 'monthly' as the period_name, date('2018-05-20') as the period_start_date, the result will be date('2018-02-20')
        - if you pass 'quarterly' as the period_name, date('2018-05-20') as the date, the result will be date('2018-08-20')

        @param period_name: (string) the name of the given period which is either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'
        @param period_start_date: (datetime.datetime) the starting date of the period from which the period will be started
        @return: (datetime.datetime) the last date of the period
        @raise ValidationError: when the passed period_name is invalid
        """
        if period_name not in ('weekly', 'monthly', 'quarterly', 'biannually', 'annually'):
            raise ValidationError(_("Wrong value passed to the argument `period_name` of the method `find_last_date_of_period`."
                                    " The value for `period_name` should be either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'"))
        if period_name == 'weekly':
            dt = period_start_date + relativedelta(days=6)
        elif period_name == 'monthly':
            dt = period_start_date + \
                relativedelta(months=1) - relativedelta(days=1)
        elif period_name == 'quarterly':
            dt = period_start_date + \
                relativedelta(months=3) - relativedelta(days=1)
        elif period_name == 'biannually':
            dt = period_start_date + \
                relativedelta(months=6) - relativedelta(days=1)
        else:
            dt = period_start_date + \
                relativedelta(years=1) - relativedelta(days=1)
        return dt

    def _validate_period_name(self, period_name):
        msg = ''
        if period_name not in ('weekly', 'monthly', 'quarterly', 'biannually', 'annually'):
            msg = _("Wrong value passed to the argument `period_name` of the method `find_last_date_of_period`."
                    " The value for `period_name` should be either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'")
            return False, msg
        else:
            return True, msg

    def find_first_date_of_period(self, period_name, date):
        """
        This method finds the first date of the given period defined by period name and any date of the period
        @param period_name: (string) the name of the given period which is either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'
        @param date: (datetime.datetime) any date of the period to find
        @return: (datetime.datetime) the first date of the period
        """
        ret, msg = self._validate_period_name(period_name)
        if not ret:
            raise ValidationError(msg)

        if period_name == 'weekly':
            dt = date - relativedelta(days=date.weekday())
        elif period_name == 'monthly':
            # force day as 1 while keep year and month unchanged
            dt = date + relativedelta(day=1)
        elif period_name == 'quarterly':
            if date.month >= 1 and date.month <= 3:
                dt = fields.Date.to_date('%s-%s-%s' % (date.year, '01', '01'))
            elif date.month >= 4 and date.month <= 6:
                dt = fields.Date.to_date('%s-%s-%s' % (date.year, '04', '01'))
            elif date.month >= 7 and date.month <= 9:
                dt = fields.Date.to_date('%s-%s-%s' % (date.year, '07', '01'))
            else:
                dt = fields.Date.to_date('%s-%s-%s' % (date.year, 10, '01'))
        elif period_name == 'biannually':
            if date.month <= 6:
                dt = fields.Date.to_date('%s-01-01' % date.year)
            else:
                dt = fields.Date.to_date('%s-07-01' % date.year)
        else:
            dt = fields.Date.to_date('%s-01-01' % date.year)
        return dt

    def find_last_date_of_period(self, period_name, date, date_is_start_date=False):
        """
        This method finds the last date of the given period defined by period name and any date of the period. For example:
        - if you pass 'monthly' as the period_name, date('2018-05-20') as the date, the result will be date('2018-05-31')
        - if you pass 'quarterly' as the period_name, date('2018-05-20') as the date, the result will be date('2018-06-30')
        @param period_name: (string) the name of the given period which is either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'
        @param date: (datetime.datetime) either the start date of the given period or any date of the period, depending on the passed value of the arg. date_is_start_date
        @param date_is_start_date: (bool) True to indicate the given date is also the starting date of the given period_name, otherwise, the given date is any of the period's dates
        @return: (datetime.datetime) the last date of the period
        @raise ValidationError: when the passed period_name is invalid
        """
        ret, msg = self._validate_period_name(period_name)
        if not ret:
            raise ValidationError(msg)

        # If the given date is the start date of the period
        if date_is_start_date:
            return self._find_last_date_of_period_from_period_start_date(period_name=period_name, period_start_date=date)

        # else
        if period_name == 'weekly':
            dt = date + relativedelta(days=6 - date.weekday())
        elif period_name == 'monthly':
            days_of_month = self.get_days_of_month_from_date(date)
            dt = fields.Datetime.to_datetime(
                '%s-%s-%s' % (date.year, str(date.month).zfill(2), str(days_of_month).zfill(2)))
        elif period_name == 'quarterly':
            if date.month >= 1 and date.month <= 3:
                dt = fields.Datetime.to_datetime(
                    '%s-%s-%s' % (date.year, '03', 31))
            elif date.month >= 4 and date.month <= 6:
                dt = fields.Datetime.to_datetime(
                    '%s-%s-%s' % (date.year, '06', 30))
            elif date.month >= 7 and date.month <= 9:
                dt = fields.Datetime.to_datetime(
                    '%s-%s-%s' % (date.year, '09', 30))
            else:
                dt = fields.Datetime.to_datetime(
                    '%s-%s-%s' % (date.year, 12, 31))
        elif period_name == 'biannually':
            if date.month <= 6:
                dt = fields.Datetime.to_datetime(
                    '%s-%s-%s' % (date.year, '06', 30))
            else:
                dt = fields.Datetime.to_datetime('%s-12-31' % date.year)
        else:
            dt = fields.Datetime.to_datetime('%s-12-31' % date.year)
        return dt

    def period_iter(self, period_name, dt_start, dt_end, start_day_offset=0):
        """
        Method to generate sorted dates for periods of the given period_name and dt_start and dt_end
        @param period_name: (string) the name of the given period which is either 'weekly' or 'monthly' or 'quarterly' or 'biannually' or 'annually'
        @param dt_start: (datetime.datetime)
        @param dt_end: (datetime.datetime)
        @param start_day_offset: default value is zero, which means that the start days are always the very first day of the period
        @return: [list] list of datetime objects contain dt_start and end dates of found periods. For example:
                if we pass [datetime.date(2018, 7, 4) and datetime.date(2018, 10, 31) and 0 as the dt_start and the dt_end and the
                start_day_offset correspondingly, the result will be
                    [datetime.date(2018, 7, 4),
                    datetime.date(2018, 7, 31), datetime.date(2018, 8, 31), datetime.date(2018, 9, 30), datetime.date(2018, 10, 31)]
        """
        if not start_day_offset >= 0:
            raise ValidationError(
                _("The `start_day_offset` passed to the method `period_iter` must be greater than or equal to zero!"))
        res = [dt_start]
        period_start_date = self.find_first_date_of_period(
            period_name, dt_start) + relativedelta(days=start_day_offset)
        if period_start_date > dt_start:
            res.append(period_start_date - relativedelta(days=1))

        while period_start_date <= dt_end:
            last_dt = self._find_last_date_of_period_from_period_start_date(
                period_name=period_name, period_start_date=period_start_date)
            if last_dt > dt_end:
                last_dt = dt_end
            res.append(last_dt)
            period_start_date = last_dt + relativedelta(days=1)

        res.sort()
        return res

    def get_days_of_month_from_date(self, dt):
        return calendar.monthrange(dt.year, dt.month)[1]

    def get_day_of_year_from_date(self, date):
        """
        Return the day of year from date. For example, 2018-01-06 will return 6

        :param date: date object 
        """
        first_date = fields.Date.to_date('%-01-01' % date.year)
        day = self.get_days_between_dates(first_date, date) + 1
        return day

    def get_days_between_dates(self, dt_from, dt_to):
        """
        Return number of days between two dates
        """
        return (dt_to - dt_from).days

    def get_weekdays_for_period(self, dt_from, dt_to):
        """
        Method to return the a dictionary in form of {int0:date, wd1:date, ...} where int0/int1
            are integer 0~6 presenting weekdays and date1/date2 are dates that are the correspong weekdays
        @param dt_from: datetime.datetime|datetime.date
        @param dt_to: datetime.datetime|datetime.date
        @return: dict{int0:date, wd1:date, ...}
        """
        nb_of_days = self.get_days_between_dates(dt_from, dt_to) + 1
        if nb_of_days > 7:
            raise ValidationError(
                _("The method get_weekdays_for_period(dt_from, dt_to) does not support the periods having more than 7 days"))
        weekdays = {}
        for day in range(0, nb_of_days):
            day_rec = dt_from + timedelta(days=day)
            weekdays[day_rec.weekday()] = day_rec.date()
        return weekdays

    def next_weekday(self, date, weekday=None):
        """
        Method to get the date in the nex tweek of the given `date`'s week with weekday is equal to the given `weekday`. For example,
        - date: 2018-10-18 (Thursday)
        - weekday:
            0: will return 2018-10-22 (Monday next week)
            1: will return 2018-10-23 (Tuesday next week)
            2: will return 2018-10-24 (Wednesday next week)
            3: will return 2018-10-25 (Thursday next week)
            4: will return 2018-10-26 (Friday next week)
            5: will return 2018-10-27 (Saturday next week)
            6: will return 2018-10-28 (Sunday next week)
            None: will return 2018-10-25 (the same week day next week)        
        @param date: (datetime.datetime or datetime.date) the given date to find the date next week
        @param weekday: week day of the next week which is an integer from 0 to 6 presenting a day of week, or None to find the date of the same week day next week

        @return: date of the same weekday next week
        """
        # if weekday is None, set it as the same as the weekday of the given date
        if weekday is None:
            weekday = date.weekday()

        days_ahead = weekday - date.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return date + timedelta(days_ahead)

    def split_date(self, date):
        """
        Method to split a date into year,month,day separatedly
        @param date date:
        """
        year = date.year
        month = date.month
        day = date.day
        return year, month, day

    def hours_time_string(self, hours):
        """ convert a number of hours (float) into a string with format '%H:%M' """
        minutes = int(round(hours * 60))
        return "%02d:%02d" % divmod(minutes, 60)

    def _zip_dir(self, path, zf, incl_dir=False):
        """
        @param path: the path to the directory to zip
        @param zf: the ZipFile object which is an instance of zipfile.ZipFile
        @type zf: ZipFile

        @return: zipfile.ZipFile object that contain all the content of the path
        """
        path = os.path.normpath(path)

        dlen = len(path)
        if incl_dir:
            dir_name = os.path.split(path)[1]
            minus = len(dir_name) + 1
            dlen -= minus
        for root, dirs, files in os.walk(path):
            for name in files:
                full = os.path.join(root, name)
                rel = root[dlen:]
                dest = os.path.join(rel, name)
                zf.write(full, dest)
        return zf

    def zip_dir(self, path, incl_dir=False):
        """
        zip a directory tree into a bytes object which is ready for storing in Binary field

        @param path: the absolute path to the directory to zip
        @type path: string

        @return: return bytes object containing data for storing in Binary fields
        @rtype: bytes
        """
        # initiate A BytesIO object
        file_data = BytesIO()

        # open file_data as ZipFile with write mode
        with zipfile.ZipFile(file_data, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            self._zip_dir(path, zf, incl_dir=incl_dir)

        # Change the stream position to the start of the stream
        # see https://docs.python.org/3/library/io.html#io.IOBase.seek
        file_data.seek(0)
        # read bytes to the EOF
        file_data_read = file_data.read()
        # encode bytes for output to return
        out = base64.encodebytes(file_data_read)
        return out

    def zip_dirs(self, paths):
        """
        zip a tree of directories (defined by paths) into a bytes object which is ready for storing in Binary field

        @param paths: list of absolute paths (string) to the directories to zip
        @type paths: list

        @return: return bytes object containing data for storing in Binary fields
        @rtype: bytes
        """
        # initiate A BytesIO object
        file_data = BytesIO()

        # open file_data as ZipFile with write mode
        with zipfile.ZipFile(file_data, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in paths:
                self._zip_dir(path, zf, incl_dir=True)

        # Change the stream position to the start of the stream
        # see https://docs.python.org/3/library/io.html#io.IOBase.seek
        file_data.seek(0)
        # read bytes to the EOF
        file_data_read = file_data.read()
        # encode bytes for output to return
        out = base64.encodebytes(file_data_read)
        return out

    def guess_lang(self, sample):
        """
        This method is for others to implement.
        """
        raise NotImplementedError(
            _("the method guess_lang has not been implemented yet"))

    def strip_accents(self, s):
        s = remove_accents(s)
        return self._no_accent_vietnamese(s)

    def _no_accent_vietnamese(self, s):
        """
        Convert Vietnamese unicode string from 'Tiếng Việt có dấu' thanh 'Tieng Viet khong dau'
        :param s: text: input string to be converted
        :return : string converted
        """
    #     s = s.decode('utf-8')
        s = re.sub(u'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
        s = re.sub(u'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
        s = re.sub(u'[èéẹẻẽêềếệểễ]', 'e', s)
        s = re.sub(u'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
        s = re.sub(u'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
        s = re.sub(u'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
        s = re.sub(u'[ìíịỉĩ]', 'i', s)
        s = re.sub(u'[ÌÍỊỈĨ]', 'I', s)
        s = re.sub(u'[ùúụủũưừứựửữ]', 'u', s)
        s = re.sub(u'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
        s = re.sub(u'[ỳýỵỷỹ]', 'y', s)
        s = re.sub(u'[ỲÝỴỶỸ]', 'Y', s)
        s = re.sub(u'[Đ]', 'D', s)
        s = re.sub(u'[đ]', 'd', s)
        return s

    def no_accent_vietnamese(self, s):
        _logger.warn(
            'The method `no_accent_vietnamese()` is deprecated. Please use the `_no_accent_vietnamese()` instead')
        return self._no_accent_vietnamese(s)

    def sum_digits(self, n, number_of_digit_return=None):
        """
        This will sum all digits of the given number until the result has x digits where x is number_of_digit_return
        @param n: the given number for sum of its digits
        @type n: int|float
        @param number_of_digit_return: the number of digist in the return result.
            For example, if n=178 and number_of_digit_return=2, the result will be 16. However, if number_of_digit_return <= 1, the result will be 7 (=1+6 again)

        @return: the sum of all the digits until the result has `number_of_digit_return` digits
        @rtype: int
        """
        s = 0
        for d in str(n):
            if d.isdigit():
                s += int(d)

        str_len = len(str(s))
        if isinstance(number_of_digit_return, int) and str_len > number_of_digit_return and str_len > 1:
            return self.sum_digits(s)
        return s

    def find_nearest_lucky_number(self, n, rounding=0, round_up=False):
        """
        9 is lucky number
        This will find the nearest integer if the given number that have digits sum = 9 (sum digits until 1 digit is returned)
        @param n: the given number for finding its nearest lucky number
        @type n: int|float
        @param rounding: the number of digist for rounding
            For example, if n=178999 and rounding=2, the result will be 178900. However, if rounding = 4, the result will be 170000

        @return: the lucky number
        @rtype: int
        """
        if rounding < 0:
            rounding = 0
        # replace last x digits with zero by rounding up/down, where x is the given round_digits
        n = round(n, rounding) if round_up else round(n, -rounding)
        # calculate adjusting step
        step = 1
        for x in range(rounding):
            step = step * 10

        while self.sum_digits(n, 1) != 9:
            if isinstance(n, int):
                if round_up:
                    n += step
                else:
                    n -= step
            else:
                n = round(n)
        return n

    def get_host_ip(self):
        """
        This method return the IP of the host where the Odoo instance is running.
        If the instance is deployed behind a reverse proxy, the returned IP will be the IP of the proxy instead.
        """
        url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url') + MY_IP_ROUTE
        try:
            respond = get(url)
        # catch SSLError when the url comes with an invalid SSL certificate (e.g, a self-signed one)
        except SSLError as e:
            _logger.warn(
                "SSLError occurred while getting URL %s. Here is the details: %s. Now trying without SSL verification...", url, str(e))
            # ignore ssl certificate validation
            respond = get(url, verify=False)
        # catch the ConnectionError that occurs when it failed to establish a new connection to the given URL
        except ConnectionError as e:
            _logger.error(
                "Failed to establish connection to the given URL %s. Here is the details: %s.", url, str(e))
        # catch the remaining possible errors
        except Exception as e:
            _logger.error(
                "Error occurred while getting URL %s. Here is the details: %s.", url, str(e))
        try:
            return respond.text
        except NameError as e:
            return '127.0.0.1'

    def get_users_from_group(self, group_id):
        users_ids = []
        if group_id:
            sql_query = """select uid from res_groups_users_rel where gid = %s"""
            params = (group_id,)
            self.env.cr.execute(sql_query, params)
            results = self.env.cr.fetchall()
            for users_id in results:
                users_ids.append(users_id[0])
        return users_ids

    def represents_int(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    def represents_float(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def time_to_str(self, datetime_obj):
        if not datetime_obj:
            return ''
        return datetime_obj.astimezone(pytz.timezone(self.env.user.tz)).strftime("%d/%m/%Y, %H:%M:%S")

    def float_to_time_str(self, float_time):
        # another way: str(datetime.timedelta(minutes=float_time)) -- %H:%M:%S
        hours, seconds = divmod(float_time * 60, 3600)
        minutes, seconds = divmod(seconds, 60)
        return "{:02.0f}:{:02.0f}:{:02.0f}".format(hours, minutes, seconds)

    def get_value_from_selection_field(self, record, field_name):
        res = dict(record._fields['%s'].selection).get(
            record.state) % field_name
        return res

    def get_object_intervals(self, object_obj=None, calendar_id=None, domain=[], field_dt_fr='', field_dt_to='', dt_from=None, dt_to=None):
        object_ids = object_obj.browse()
        if field_dt_fr and dt_from and hasattr(object_obj, field_dt_fr) and isinstance(dt_from, datetime.datetime):
            domain += [(field_dt_fr, '>=', dt_from)]
        if field_dt_to and dt_to and hasattr(object_obj, field_dt_to) and isinstance(dt_to, datetime.datetime):
            domain += [(field_dt_to, '<=', dt_to)]
        if calendar_id:
            pass
        object_ids = object_obj.search(domain)
        return object_ids

    def send_mail_template(self, model_id, mail_template_id=None, user_ids=None, ctx={}):
        email_values = {'email_to': user_ids[0].work_email}
        if len(user_ids) > 1:
            email_values.update({'email_cc': ','.join(formataddr(
                (user_id.name, user_id.work_email)) for user_id in user_ids[1:] if user_id.work_email)})
        mail_template_id.write(email_values)
        mail_template_id.with_context(ctx).send_mail(model_id.id)

    def _loaddicchar(self):
        dic = {}
        char1252 = 'à|á|ả|ã|ạ|ầ|ấ|ẩ|ẫ|ậ|ằ|ắ|ẳ|ẵ|ặ|è|é|ẻ|ẽ|ẹ|ề|ế|ể|ễ|ệ|ì|í|ỉ|ĩ|ị|ò|ó|ỏ|õ|ọ|ồ|ố|ổ|ỗ|ộ|\
            ờ|ớ|ở|ỡ|ợ|ù|ú|ủ|ũ|ụ|ừ|ứ|ử|ữ|ự|ỳ|ý|ỷ|ỹ|ỵ|À|Á|Ả|Ã|Ạ|Ầ|Ấ|Ẩ|Ẫ|Ậ|Ằ|Ắ|Ẳ|Ẵ|Ặ|È|É|Ẻ|Ẽ|Ẹ|Ề|Ế|Ể|Ễ|Ệ|\
            Ì|Í|Ỉ|Ĩ|Ị|Ò|Ó|Ỏ|Õ|Ọ|Ồ|Ố|Ổ|Ỗ|Ộ|Ờ|Ớ|Ở|Ỡ|Ợ|Ù|Ú|Ủ|Ũ|Ụ|Ừ|Ứ|Ử|Ữ|Ự|Ỳ|Ý|Ỷ|Ỹ|Ỵ'.split('|')
        charutf8 = "à|á|ả|ã|ạ|ầ|ấ|ẩ|ẫ|ậ|ằ|ắ|ẳ|ẵ|ặ|è|é|ẻ|ẽ|ẹ|ề|ế|ể|ễ|ệ|ì|í|ỉ|ĩ|ị|ò|ó|ỏ|õ|ọ|ồ|ố|ổ|ỗ|ộ|\
            ờ|ớ|ở|ỡ|ợ|ù|ú|ủ|ũ|ụ|ừ|ứ|ử|ữ|ự|ỳ|ý|ỷ|ỹ|ỵ|À|Á|Ả|Ã|Ạ|Ầ|Ấ|Ẩ|Ẫ|Ậ|Ằ|Ắ|Ẳ|Ẵ|Ặ|È|É|Ẻ|Ẽ|Ẹ|Ề|Ế|Ể|Ễ|Ệ|\
            Ì|Í|Ỉ|Ĩ|Ị|Ò|Ó|Ỏ|Õ|Ọ|Ồ|Ố|Ổ|Ỗ|Ộ|Ờ|Ớ|Ở|Ỡ|Ợ|Ù|Ú|Ủ|Ũ|Ụ|Ừ|Ứ|Ử|Ữ|Ự|Ỳ|Ý|Ỷ|Ỹ|Ỵ".split('|')
        for i in range(len(char1252)):
            dic[char1252[i]] = charutf8[i]
        return dic

    def covert_unicode(self, txt):
        dicchar = self._loaddicchar()
        return re.sub(r'à|á|ả|ã|ạ|ầ|ấ|ẩ|ẫ|ậ|ằ|ắ|ẳ|ẵ|ặ|è|é|ẻ|ẽ|ẹ|ề|ế|ể|ễ|ệ|ì|í|ỉ|ĩ|ị|ò|ó|ỏ|õ|ọ|ồ|ố|ổ|ỗ|ộ|ờ|ớ|ở|ỡ|ợ|ù|ú|ủ|ũ|ụ|ừ|ứ|ử|ữ|ự|ỳ|ý|ỷ|ỹ|ỵ|À|Á|Ả|Ã|Ạ|Ầ|Ấ|Ẩ|Ẫ|Ậ|Ằ|Ắ|Ẳ|Ẵ|Ặ|È|É|Ẻ|Ẽ|Ẹ|Ề|Ế|Ể|Ễ|Ệ|Ì|Í|Ỉ|Ĩ|Ị|Ò|Ó|Ỏ|Õ|Ọ|Ồ|Ố|Ổ|Ỗ|Ộ|Ờ|Ớ|Ở|Ỡ|Ợ|Ù|Ú|Ủ|Ũ|Ụ|Ừ|Ứ|Ử|Ữ|Ự|Ỳ|Ý|Ỷ|Ỹ|Ỵ', lambda x: dicchar[x.group()], txt)

    # get manager user for current hr.employee.
    def get_parent_employee_user(self, employee):
        result = employee.user_id

        while employee.parent_id and not result:
            if employee.parent_id.user_id:
                result = employee.parent_id.user_id
                break
            employee = employee.parent_id

        return result

class Base(models.AbstractModel):

    _inherit = "base"

    # ----------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------

    
    def _check_parent_field(self):
        if self._parent_name not in self._fields:
            raise TypeError(
                "The parent ({}) field does not exist.".format(self._parent_name)
            )

    
    def _build_search_childs_domain(self, parent_id, domain=[]):
        self._check_parent_field()
        parent_domain = [[self._parent_name, "=", parent_id]]
        return expression.AND([parent_domain, domain]) if domain else parent_domain

    
    def _check_context_bin_size(self, field):
        return any(
            key in self.env.context for key in ["bin_size", "bin_size_{}".format(field)]
        )

    # ----------------------------------------------------------
    # Security
    # ----------------------------------------------------------

    def _filter_access(self, operation, in_memory=True):
        if self.check_access_rights(operation, False):
            if in_memory:
                return self._filter_access_rules_python(operation)
            else:
                return self._filter_access_rules(operation)
        return self.env[self._name]

    def _filter_access_ids(self, operation, in_memory=True):
        return self._filter_access(operation, in_memory=in_memory).ids

    def check_access(self, operation, raise_exception=False):
        """ Verifies that the operation given by ``operation`` is allowed for
            the current user according to the access level.

           :param operation: one of ``read``, ``create``, ``write``, ``unlink``
           :raise AccessError: * if current level of access do not permit this operation.
           :return: True if the operation is allowed
        """
        try:
            access_right = self.check_access_rights(operation, raise_exception)
            access_rule = self.check_access_rule(operation) is None
            return access_right and access_rule
        except AccessError:
            if raise_exception:
                raise
            return False

    # ----------------------------------------------------------
    # Hierarchy Methods
    # ----------------------------------------------------------

    
    def search_parents(self, domain=[], offset=0, limit=None, order=None, count=False):
        """ This method finds the top level elements of the hierarchy for a given search query.

            :param domain: a search domain <reference/orm/domains> (default: empty list)
            :param order: a string to define the sort order of the query (default: none)
            :returns: the top level elements for the given search query
        """
        res = self._search_parents(
            domain=domain, offset=offset, limit=limit, order=order, count=count
        )
        return res if count else self.browse(res)

    
    def search_read_parents(
        self, domain=[], fields=None, offset=0, limit=None, order=None
    ):
        """ This method finds the top level elements of the hierarchy for a given search query.

            :param domain: a search domain <reference/orm/domains> (default: empty list)
            :param fields: a list of fields to read (default: all fields of the model)
            :param order: a string to define the sort order of the query (default: none)
            :returns: the top level elements for the given search query
        """
        records = self.search_parents(
            domain=domain, offset=offset, limit=limit, order=order
        )
        if not records:
            return []
        if fields and fields == ["id"]:
            return [{"id": record.id} for record in records]
        result = records.read(fields)
        if len(result) <= 1:
            return result
        index = {vals["id"]: vals for vals in result}
        return [index[record.id] for record in records if record.id in index]

    
    def _search_parents(self, domain=[], offset=0, limit=None, order=None, count=False):
        self._check_parent_field()
        self.check_access_rights("read")
        if expression.is_false(self, domain):
            return 0 if count else []
        self._flush_search(domain, fields=[self._parent_name], order=order)
        query = self._where_calc(domain)
        self._apply_ir_rules(query, "read")
        from_clause, where_clause, where_clause_arguments = query.get_sql()
        parent_where = where_clause and (" WHERE {}".format(where_clause)) or ""
        parent_query = (
            'SELECT "{}".id FROM '.format(self._table) + from_clause + parent_where
        )
        no_parent_clause = '"{table}"."{field}" IS NULL'.format(
            table=self._table, field=self._parent_name
        )
        no_access_clause = '"{table}"."{field}" NOT IN ({query})'.format(
            table=self._table, field=self._parent_name, query=parent_query
        )
        parent_clause = "({} OR {})".format(no_parent_clause, no_access_clause)
        order_by = self._generate_order_by(order, query)
        from_clause, where_clause, where_clause_params = query.get_sql()
        where_str = (
            where_clause
            and (" WHERE {} AND {}".format(where_clause, parent_clause))
            or (" WHERE {}".format(parent_clause))
        )
        if count:
            query_str = "SELECT count(1) FROM " + from_clause + where_str
            self.env.cr.execute(query_str, where_clause_params + where_clause_arguments)
            return self.env.cr.fetchone()[0]
        limit_str = limit and " limit %d" % limit or ""
        offset_str = offset and " offset %d" % offset or ""
        query_str = (
            'SELECT "{}".id FROM '.format(self._table)
            + from_clause
            + where_str
            + order_by
            + limit_str
            + offset_str
        )
        self.env.cr.execute(query_str, where_clause_params + where_clause_arguments)
        return utils.uniquify_list([x[0] for x in self.env.cr.fetchall()])

    
    def search_childs(
        self, parent_id, domain=[], offset=0, limit=None, order=None, count=False
    ):
        """ This method finds the direct child elements of the parent record for a given search query.

            :param parent_id: the integer representing the ID of the parent record
            :param domain: a search domain <reference/orm/domains> (default: empty list)
            :param offset: the number of results to ignore (default: none)
            :param limit: maximum number of records to return (default: all)
            :param order: a string to define the sort order of the query (default: none)
            :param count: counts and returns the number of matching records (default: False)
            :returns: the top level elements for the given search query
        """
        domain = self._build_search_childs_domain(parent_id, domain=domain)
        return self.search(domain, offset=offset, limit=limit, order=order, count=count)

    
    def search_read_childs(
        self, parent_id, domain=[], fields=None, offset=0, limit=None, order=None
    ):
        """ This method finds the direct child elements of the parent record for a given search query.

            :param parent_id: the integer representing the ID of the parent record
            :param domain: a search domain <reference/orm/domains> (default: empty list)
            :param fields: a list of fields to read (default: all fields of the model)
            :param offset: the number of results to ignore (default: none)
            :param limit: maximum number of records to return (default: all)
            :param order: a string to define the sort order of the query (default: none)
            :returns: the top level elements for the given search query
        """
        domain = self._build_search_childs_domain(parent_id, domain=domain)
        return self.search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order
        )