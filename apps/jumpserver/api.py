import time

from django.core.cache import cache
from django.utils import timezone
from django.utils.timesince import timesince
from django.db.models import Count, Max, F
from django.http.response import JsonResponse, HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response

from users.models import User
from assets.models import Asset
from assets.const import AllTypes
from terminal.models import Session, Command
from terminal.utils import ComponentsPrometheusMetricsUtil
from orgs.utils import current_org
from ops.const import JobStatus
from ops.models import Job, JobExecution
from common.utils import lazyproperty
from audits.models import UserLoginLog, PasswordChangeLog, OperateLog
from audits.const import LoginStatusChoices
from common.utils.timezone import local_now, local_zero_hour
from orgs.caches import OrgResourceStatisticsCache

__all__ = ['IndexApi']


class DateTimeMixin:
    request: Request

    @property
    def org(self):
        return current_org

    @lazyproperty
    def days(self):
        query_params = self.request.query_params
        count = query_params.get('days')
        count = int(count) if count else 0
        return count

    @property
    def days_to_datetime(self):
        days = self.days
        if days == 0:
            t = local_zero_hour()
        else:
            t = local_now() - timezone.timedelta(days=days)
        return t

    @lazyproperty
    def dates_list(self):
        now = local_now()
        dates = [(now - timezone.timedelta(days=i)).date() for i in range(self.days)]
        dates.reverse()
        return dates

    def get_dates_metrics_date(self):
        dates_metrics_date = [d.strftime('%m-%d') for d in self.dates_list] or ['0']
        return dates_metrics_date

    @lazyproperty
    def users(self):
        return self.org.get_members()

    @lazyproperty
    def sessions_queryset(self):
        t = self.days_to_datetime
        sessions_queryset = Session.objects.filter(date_start__gte=t)
        return sessions_queryset

    def get_logs_queryset(self, queryset, query_params):
        query = {}
        if not self.org.is_root():
            if query_params == 'username':
                query = {
                    f'{query_params}__in': self.users.values_list('username', flat=True)
                }
            else:
                query = {
                    f'{query_params}__in': [str(user) for user in self.users]
                }
        queryset = queryset.filter(**query)
        return queryset

    @lazyproperty
    def login_logs_queryset(self):
        t = self.days_to_datetime
        queryset = UserLoginLog.objects.filter(datetime__gte=t)
        queryset = self.get_logs_queryset(queryset, 'username')
        return queryset

    @lazyproperty
    def password_change_logs_queryset(self):
        t = self.days_to_datetime
        queryset = PasswordChangeLog.objects.filter(datetime__gte=t)
        queryset = self.get_logs_queryset(queryset, 'user')
        return queryset

    @lazyproperty
    def operate_logs_queryset(self):
        t = self.days_to_datetime
        queryset = OperateLog.objects.filter(datetime__gte=t)
        queryset = self.get_logs_queryset(queryset, 'user')
        return queryset

    @lazyproperty
    def ftp_logs_queryset(self):
        t = self.days_to_datetime
        queryset = OperateLog.objects.filter(datetime__gte=t)
        queryset = self.get_logs_queryset(queryset, 'user')
        return queryset

    @lazyproperty
    def command_queryset(self):
        t = self.days_to_datetime
        t = t.timestamp()
        queryset = Command.objects.filter(timestamp__gte=t)
        return queryset

    @lazyproperty
    def jobs_queryset(self):
        t = self.days_to_datetime
        queryset = Job.objects.filter(date_created__gte=t)
        return queryset

    @lazyproperty
    def jobs_executed_queryset(self):
        t = self.days_to_datetime
        queryset = JobExecution.objects.filter(date_created__gte=t)
        return queryset


class DatesLoginMetricMixin:
    dates_list: list
    command_queryset: Command.objects
    sessions_queryset: Session.objects
    ftp_logs_queryset: OperateLog.objects
    jobs_queryset: Job.objects
    jobs_executed_queryset: JobExecution.objects
    login_logs_queryset: UserLoginLog.objects
    operate_logs_queryset: OperateLog.objects
    password_change_logs_queryset: PasswordChangeLog.objects

    @staticmethod
    def get_cache_key(date, tp):
        date_str = date.strftime("%Y%m%d")
        key = "SESSION_DATE_{}_{}_{}".format(current_org.id, tp, date_str)
        return key

    def __get_data_from_cache(self, date, tp):
        if date == timezone.now().date():
            return None
        cache_key = self.get_cache_key(date, tp)
        count = cache.get(cache_key)
        return count

    def __set_data_to_cache(self, date, tp, count):
        cache_key = self.get_cache_key(date, tp)
        cache.set(cache_key, count, 3600 * 24 * 7)

    @staticmethod
    def get_date_start_2_end(d):
        time_min = timezone.datetime.min.time()
        time_max = timezone.datetime.max.time()
        tz = timezone.get_current_timezone()
        ds = timezone.datetime.combine(d, time_min).replace(tzinfo=tz)
        de = timezone.datetime.combine(d, time_max).replace(tzinfo=tz)
        return ds, de

    def get_date_login_count(self, date):
        tp = "LOGIN"
        count = self.__get_data_from_cache(date, tp)
        if count is not None:
            return count
        ds, de = self.get_date_start_2_end(date)
        count = Session.objects.filter(date_start__range=(ds, de)).count()
        self.__set_data_to_cache(date, tp, count)
        return count

    def get_dates_metrics_total_count_login(self):
        data = []
        for d in self.dates_list:
            count = self.get_date_login_count(d)
            data.append(count)
        if len(data) == 0:
            data = [0]
        return data

    def get_date_user_count(self, date):
        tp = "USER"
        count = self.__get_data_from_cache(date, tp)
        if count is not None:
            return count
        ds, de = self.get_date_start_2_end(date)
        count = len(set(Session.objects.filter(date_start__range=(ds, de)).values_list('user_id', flat=True)))
        self.__set_data_to_cache(date, tp, count)
        return count

    def get_dates_metrics_total_count_active_users(self):
        data = []
        for d in self.dates_list:
            count = self.get_date_user_count(d)
            data.append(count)
        return data

    def get_date_asset_count(self, date):
        tp = "ASSET"
        count = self.__get_data_from_cache(date, tp)
        if count is not None:
            return count
        ds, de = self.get_date_start_2_end(date)
        count = len(set(Session.objects.filter(date_start__range=(ds, de)).values_list('asset', flat=True)))
        self.__set_data_to_cache(date, tp, count)
        return count

    def get_dates_metrics_total_count_active_assets(self):
        data = []
        for d in self.dates_list:
            count = self.get_date_asset_count(d)
            data.append(count)
        return data

    def get_date_session_count(self, date):
        tp = "SESSION"
        count = self.__get_data_from_cache(date, tp)
        if count is not None:
            return count
        ds, de = self.get_date_start_2_end(date)
        count = Session.objects.filter(date_start__range=(ds, de)).count()
        self.__set_data_to_cache(date, tp, count)
        return count

    def get_dates_metrics_total_count_sessions(self):
        data = []
        for d in self.dates_list:
            count = self.get_date_session_count(d)
            data.append(count)
        return data

    @lazyproperty
    def get_type_to_assets(self):
        result = Asset.objects.annotate(type=F('platform__type')). \
            values('type').order_by('type').annotate(total=Count(1))
        all_types_dict = dict(AllTypes.choices())
        result = list(result)
        for i in result:
            tp = i['type']
            i['label'] = all_types_dict.get(tp, tp)
        return result

    def get_dates_login_times_assets(self):
        assets = self.sessions_queryset.values("asset") \
            .annotate(total=Count("asset")) \
            .annotate(last=Max("date_start")).order_by("-total")
        assets = assets[:10]
        for asset in assets:
            asset['last'] = str(asset['last'])
        return list(assets)

    def get_dates_login_times_users(self):
        users = self.sessions_queryset.values("user_id") \
            .annotate(total=Count("user_id")) \
            .annotate(user=Max('user')) \
            .annotate(last=Max("date_start")).order_by("-total")
        users = users[:10]
        for user in users:
            user['last'] = str(user['last'])
        return list(users)

    def get_dates_login_record_sessions(self):
        sessions = self.sessions_queryset.order_by('-date_start')
        sessions = sessions[:10]
        for session in sessions:
            session.avatar_url = User.get_avatar_url("")
        sessions = [
            {
                'user': session.user,
                'asset': session.asset,
                'is_finished': session.is_finished,
                'date_start': str(session.date_start),
                'timesince': timesince(session.date_start)
            }
            for session in sessions
        ]
        return sessions

    @lazyproperty
    def user_login_logs_amount(self):
        return self.login_logs_queryset.count()

    @lazyproperty
    def user_login_success_logs_amount(self):
        return self.login_logs_queryset.filter(status=LoginStatusChoices.success).count()

    @lazyproperty
    def user_login_amount(self):
        return self.login_logs_queryset.values('username').distinct().count()

    @lazyproperty
    def operate_logs_amount(self):
        return self.operate_logs_queryset.count()

    @lazyproperty
    def change_password_logs_amount(self):
        return self.password_change_logs_queryset.count()

    @lazyproperty
    def commands_amount(self):
        return self.command_queryset.count()

    @lazyproperty
    def commands_danger_amount(self):
        return self.command_queryset.filter(risk_level=Command.RISK_LEVEL_DANGEROUS).count()

    @lazyproperty
    def jobs_amount(self):
        return self.jobs_queryset.count()

    @lazyproperty
    def jobs_unexecuted_amount(self):
        executed_amount = self.jobs_executed_queryset.values(
            'job_id').order_by('job_id').distinct().count()
        return self.jobs_amount - executed_amount

    @lazyproperty
    def jobs_executed_failed_amount(self):
        return self.jobs_executed_queryset.filter(
            status=JobStatus.failed).count()

    @lazyproperty
    def sessions_amount(self):
        return self.sessions_queryset.count()

    @lazyproperty
    def ftp_logs_amount(self):
        return self.ftp_logs_queryset.count()


class IndexApi(DateTimeMixin, DatesLoginMetricMixin, APIView):
    http_method_names = ['get']

    def check_permissions(self, request):
        return request.user.has_perm(['rbac.view_audit', 'rbac.view_console'])

    def get(self, request, *args, **kwargs):
        data = {}

        query_params = self.request.query_params

        caches = OrgResourceStatisticsCache(self.org)

        _all = query_params.get('all')

        if _all or query_params.get('total_count') or query_params.get('total_count_users'):
            data.update({
                'total_count_users': caches.users_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_assets'):
            data.update({
                'total_count_assets': caches.assets_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_users_this_week'):
            data.update({
                'total_count_users_this_week': caches.new_users_amount_this_week,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_assets_this_week'):
            data.update({
                'total_count_assets_this_week': caches.new_assets_amount_this_week,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_login_users'):
            data.update({
                'total_count_login_users': self.user_login_amount
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_today_active_assets'):
            data.update({
                'total_count_today_active_assets': caches.total_count_today_active_assets,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_online_users'):
            data.update({
                'total_count_online_users': caches.total_count_online_users,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_online_sessions'):
            data.update({
                'total_count_online_sessions': caches.total_count_online_sessions,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_today_failed_sessions'):
            data.update({
                'total_count_today_failed_sessions': caches.total_count_today_failed_sessions,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_user_login_logs'):
            data.update({
                'total_count_user_login_logs': self.user_login_logs_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_user_login_success_logs'):
            data.update({
                'total_count_user_login_success_logs': self.user_login_success_logs_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_operate_logs'):
            data.update({
                'total_count_operate_logs': self.operate_logs_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_change_password_logs'):
            data.update({
                'total_count_change_password_logs': self.change_password_logs_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_commands'):
            data.update({
                'total_count_commands': self.commands_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_commands_danger'):
            data.update({
                'total_count_commands_danger': self.commands_danger_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_history_sessions'):
            data.update({
                'total_count_history_sessions': self.sessions_amount - caches.total_count_online_sessions,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_ftp_logs'):
            data.update({
                'total_count_ftp_logs': self.ftp_logs_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_jobs'):
            data.update({
                'total_count_jobs': self.jobs_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_jobs_unexecuted'):
            data.update({
                'total_count_jobs_unexecuted': self.jobs_unexecuted_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_jobs_executed_failed'):
            data.update({
                'total_count_jobs_executed_failed': self.jobs_executed_failed_amount,
            })

        if _all or query_params.get('total_count') or query_params.get('total_count_type_to_assets_amount'):
            data.update({
                'total_count_type_to_assets_amount': self.get_type_to_assets,
            })

        if _all or query_params.get('session_dates_metrics'):
            data.update({
                'dates_metrics_date': self.get_dates_metrics_date(),
                'dates_metrics_total_count_session': self.get_dates_metrics_total_count_sessions(),
            })

        if _all or query_params.get('dates_metrics'):
            data.update({
                'dates_metrics_date': self.get_dates_metrics_date(),
                'dates_metrics_total_count_login': self.get_dates_metrics_total_count_login(),
                'dates_metrics_total_count_active_users': self.get_dates_metrics_total_count_active_users(),
                'dates_metrics_total_count_active_assets': self.get_dates_metrics_total_count_active_assets(),
            })

        if _all or query_params.get('dates_login_times_top10_assets'):
            data.update({
                'dates_login_times_top10_assets': self.get_dates_login_times_assets(),
            })

        if _all or query_params.get('dates_login_times_top10_users'):
            data.update({
                'dates_login_times_top10_users': self.get_dates_login_times_users(),
            })

        if _all or query_params.get('dates_login_record_top10_sessions'):
            data.update({
                'dates_login_record_top10_sessions': self.get_dates_login_record_sessions()
            })

        return JsonResponse(data, status=200)


class HealthApiMixin(APIView):
    pass


class HealthCheckView(HealthApiMixin):
    permission_classes = (AllowAny,)

    @staticmethod
    def get_db_status():
        t1 = time.time()
        try:
            ok = User.objects.first() is not None
            t2 = time.time()
            return ok, t2 - t1
        except Exception as e:
            return False, str(e)

    @staticmethod
    def get_redis_status():
        key = 'HEALTH_CHECK'

        t1 = time.time()
        try:
            value = '1'
            cache.set(key, '1', 10)
            got = cache.get(key)
            t2 = time.time()

            if value == got:
                return True, t2 - t1
            return False, 'Value not match'
        except Exception as e:
            return False, str(e)

    def get(self, request):
        redis_status, redis_time = self.get_redis_status()
        db_status, db_time = self.get_db_status()
        status = all([redis_status, db_status])
        data = {
            'status': status,
            'db_status': db_status,
            'db_time': db_time,
            'redis_status': redis_status,
            'redis_time': redis_time,
            'time': int(time.time()),
        }
        return Response(data)


class PrometheusMetricsApi(HealthApiMixin):
    permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        util = ComponentsPrometheusMetricsUtil()
        metrics_text = util.get_prometheus_metrics_text()
        return HttpResponse(metrics_text, content_type='text/plain; version=0.0.4; charset=utf-8')
