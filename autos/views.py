import json
import random

import openpyxl
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Max, Sum, Avg, F

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Max, Sum, Avg
from django.db.models import Sum, Count, Q, Avg, Max
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from geopy.distance import geodesic
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .logic import calculate_run_time_by_id, calculate_run_time, calculate_run_time_different_way, calculate_median, \
     validate_url
from .models import Autos, Run, Position, AthleteCoachRelation, ChallengeRecord, \
    CollectableItem, AthleteInfo  # Ensure the Autos model is imported
from .serializers import RunSerializer, PositionSerializer, UserSerializer, DetailAthleteSerializer, \
    DetailCoachSerializer, ChallengeRecordSerializer, ChallengeRecordsWithUsersSerializer, \
    CollectableItemSerializer, AthleteInfoSerializer


def get_autos(request):
    autos = Autos.objects.all()
    # Set safe=False to allow a non-dict object (list) to be serialized
    return JsonResponse([{'name': auto.name} for auto in autos], safe=False)


def subscribe_to_coach_api_url(request, id):
    # Get the coach by ID from the URL
    coach = get_object_or_404(User, id=id)

    # Ensure the identified user is a coach
    if not coach.is_staff:
        return JsonResponse({'status': False, 'error': 'Можно подписываться только на Юзеров с типом Coach'},
                            status=400)

    try:
        # Parse the JSON request body
        data = json.loads(request.body)
        athlete_id = data.get('athlete', None)

        # Get the athlete by the ID provided in the body
        athlete = User.objects.filter(id=athlete_id).first()
        if not athlete:
            return JsonResponse({'status': False, }, status=400)

        if athlete.is_staff:
            return JsonResponse({'status': False, 'error': 'Подписываются могут только Юзеры с типом Athlete'},
                                status=400)
        if AthleteCoachRelation.objects.filter(athlete=athlete, coach=coach).exists():
            return JsonResponse({'status': False}, status=400)

        AthleteCoachRelation.objects.create(athlete=athlete, coach=coach)

        # Return success response
        return JsonResponse(
            {'status': True, 'message': f'{athlete.username} successfully subscribed to {coach.username}'})

    except (json.JSONDecodeError, TypeError, KeyError):
        return JsonResponse({'status': False, 'error': 'Invalid request format'}, status=400)

    except ValidationError as e:
        return JsonResponse({'status': False, 'error': str(e)}, status=400)


def get_company_details(request):
    details = {
        'company_name': settings.COMPANY_NAME,
        'slogan': settings.COMPANY_SLOGAN,
        'contacts': settings.COMPANY_CONTACTS,
    }
    return JsonResponse(details)


class CustomPagination(PageNumberPagination):
    # page_size = 9  # Количество объектов на странице по умолчанию
    page_size_query_param = 'size'
    # max_page_size = 12


class RunPagination(PageNumberPagination):
    # page_size = 9  # Количество объектов на странице по умолчанию
    page_size_query_param = 'size'
    # max_page_size = 12
#

class RunsViewSet(viewsets.ModelViewSet):
    queryset = Run.objects.all()
    serializer_class = RunSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'athlete']
    ordering_fields = ['created_at']
    pagination_class = RunPagination

    @action(detail=True, methods=['post'], url_path='start')
    def start_run(self, request, pk=None):
        run = self.get_object()  # Получить объект Run по ID из URL

        if run.status == 'in_progress':
            return Response({'status': 'already run'}, status=status.HTTP_400_BAD_REQUEST)

        if run.status == 'finished':
            return Response({'status': 'already stopped'}, status=status.HTTP_400_BAD_REQUEST)

        run.status = 'in_progress'  # Например, метод start() запускает ваш объект
        run.save()
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='stop')
    def stop_run(self, request, pk=None):
        try:
            run = Run.objects.get(pk=pk)
        except Run.DoesNotExist:
            return Response({'error': 'Run not found'}, status=status.HTTP_404_NOT_FOUND)

        if run.status != 'in_progress':
            return Response({'status': 'Run not in progress'}, status=status.HTTP_400_BAD_REQUEST)

        run.status = 'finished'

        run.save()

        positions_list = Position.objects.filter(run=run).values('latitude', 'longitude')

        # Convert to list of tuples
        running_routes = [
            (position['latitude'], position['longitude'])
            for position in positions_list
        ]

        total_distance = 0
        for i in range(len(running_routes) - 1):
            start = running_routes[i]
            end = running_routes[i + 1]
            distance = geodesic(start, end).kilometers
            total_distance += distance

        run.distance = round(total_distance, 2)
        # run.speed = calculate_median(list(Position.objects.filter(run=run).values_list('speed', flat=True)))
        if Position.objects.filter(run=run).exists():
            run.speed = round(calculate_median(run), 2)
            # run.run_time_seconds = calculate_run_time_by_id(run)
            run.run_time_seconds = calculate_run_time_different_way(run)

        # run.calculate_run_time_by_idon_emission = call_carboninterface('123', run.distance)
        # run.save()

        if Run.objects.filter(athlete_id=run.athlete_id, status='finished').count() == 10:
            ChallengeRecord.objects.create(athlete_id=run.athlete_id, name='RUN_10')

        dis = Run.objects.filter(athlete_id=run.athlete_id, status='finished').aggregate(dis=Sum('distance')).get('dis', None)
        if dis and dis or 0 >= 50:

        # amount = 0
        # for run in Run.objects.filter(athlete_id=run.athlete_id, status='finished'):
        #     amount += run.distance
        #     if amount > 50:
            ChallengeRecord.objects.get_or_create(athlete_id=run.athlete_id, name='RUN_50')

        if (run.run_time_seconds and run.run_time_seconds <= 600) and (run.distance and run.distance >= 2):
            ChallengeRecord.objects.get_or_create(athlete_id=run.athlete_id, name='RUN_2_10')

        return Response({'status': 'run stopped'}, status=status.HTTP_200_OK)


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.filter()
    serializer_class = PositionSerializer
    # filter_backends = [DjangoFilterBackend]
    # filterset_fields = ['run']

    def get_queryset(self):
        queryset = Position.objects.all()
        run = self.request.query_params.get('run', None)
        if run:
            queryset = queryset.filter(run=run)
        return queryset

    def perform_create(self, serializer):
        position = serializer.save()
        for item in CollectableItem.objects.all():
            start_item = (item.latitude, item.longitude)
            position_item = (position.latitude, position.longitude)
            distance_to_item = geodesic(start_item, position_item).meters
            if distance_to_item <= 100:
                item.users.add(position.run.athlete_id)

        date_time = position.date_time
        try:
            previous_position = Position.objects.filter(run_id=position.run_id, date_time__lt=date_time).latest(
                'date_time')
            # previous_position = Position.objects.filter(run_id=position.run_id).exclude(id=position.id).latest('date_time')
        except Position.DoesNotExist:
            return

        start = (previous_position.latitude, previous_position.longitude)
        end = (position.latitude, position.longitude)
        distance = geodesic(start, end).kilometers
        if not distance:
            return
        timing = position.date_time - previous_position.date_time
        time_seconds = timing.total_seconds()
        if time_seconds > 0:
            speed_mps = distance * 1000 / time_seconds
            position.speed = round(speed_mps, 2)

        position.distance = round(distance, 2) + previous_position.distance
        position.save()

        return position


class UsersViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['first_name', 'last_name', 'id']
    pagination_class = CustomPagination
    ordering_fields = ['date_joined', 'runs_finished_count', 'average_rating']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            user = self.get_object()
            if user.is_staff:
                return DetailCoachSerializer
            return DetailAthleteSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # Exclude superusers from the queryset
        queryset = queryset.filter(is_superuser=False)

        # Get the 'type' query parameter
        user_type = self.request.query_params.get('type', None)

        # Annotate runs_finished_count for all users
        queryset = queryset.annotate(
            runs_finished_count=Count('run', filter=Q(run__status='finished'))
        )

        # If filtering for coaches, annotate average_rating
        if user_type == 'coach':
            queryset = queryset.filter(is_staff=True)
            # queryset = queryset.annotate(average_rating=Avg('coaches__rate'))

        elif user_type == 'athlete':
            queryset = queryset.filter(is_staff=False)

        queryset = queryset.annotate(average_rating=Avg('coaches__rate'))

        # Let the OrderingFilter handle the ordering
        return queryset
#

class ChallengeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChallengeRecord.objects.all()
    serializer_class = ChallengeRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['athlete', 'name']


def get_challenges(request):
    user_id = request.query_params.get("athlete", None)
    if user_id:
        user_queryset = User.objects.filter(pk=user_id)
        if user_queryset:
            user = user_queryset[0]
            challenges = ChallengeRecord.objects.filter(athlete=user)

            return Response(challenges, status=status.HTTP_200_OK)

    return Response(
        ChallengeRecord.objects.all(), status=status.HTTP_200_OK
    )

def get_challenges_summary(request):  # 6
    result = []
    for challenge_type in ChallengeRecord.CHALLENGE_CHOICES:
        data = {'name_to_display': challenge_type[1], 'athletes': []}
        users_info = User.objects.filter(challenges__name=challenge_type[0])
        for user in users_info:
            data['athletes'].append({'full_name': f'{user.first_name} {user.last_name}', 'id': user.id,
                                     'username': user.username})
        result.append(data)
    return JsonResponse(result, safe=False)


def rate_coach(request, coach_id):
    # Get the coach by ID from the URL
    coach = get_object_or_404(User, id=coach_id)

    # Parse the JSON request body
    data = json.loads(request.body)
    athlete_id = data.get('athlete', None)

    # Get the athlete by the ID provided in the body
    athlete = User.objects.filter(id=athlete_id).first()
    if not athlete:
        return JsonResponse({'status': False, }, status=400)

    if not AthleteCoachRelation.objects.filter(athlete_id=athlete_id, coach=coach).exists():
        return JsonResponse({'error': 'Для того чтобы ставить рейтинг надо быть подписанным на Coach'}, status=400)

    relation = AthleteCoachRelation.objects.filter(athlete_id=athlete_id, coach=coach).get()

    rating = data.get('rating', None)
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return JsonResponse({'status': False, }, status=400)

    relation.rate = rating
    relation.save()

    # Return success response
    return JsonResponse(
        {'status': True, 'message': f'{athlete.username} successfully rated {coach.username}'})


from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.db.models import Max, Sum, Avg, Subquery, OuterRef


# 7
def analytics_for_coach(request, coach_id):
    # Get the coach by ID from the URL
    coach = get_object_or_404(User, id=coach_id)
    athlete_ids = AthleteCoachRelation.objects.filter(coach=coach).values_list('athlete_id', flat=True)

    # Find the athlete with the maximum distance
    max_distance_run = (
        Run.objects.filter(athlete__id__in=athlete_ids)
        .annotate(max_distance=Max('distance'))
        .order_by('-max_distance')
        .values('athlete_id', 'max_distance')
        .first()
    )

    max_sum_distance_run = (
        Run.objects.filter(athlete__id__in=athlete_ids)
        .values('athlete_id')
        .annotate(sum_distance=Sum('distance'))
        .order_by('-sum_distance')
        .values('athlete_id', 'sum_distance')
        .first()
    )

    # Find the athlete with the maximum average speed
    max_avg_speed_run = (
        Run.objects.filter(athlete__id__in=athlete_ids)
        .values('athlete_id')
        .annotate(avg_speed=Avg('speed'))
        .order_by('-avg_speed')
        .values('athlete_id', 'avg_speed')
        .first()
    )

    return JsonResponse(
        {'longest_run_user': max_distance_run['athlete_id'],
         'longest_run_value': max_distance_run['max_distance'],
         'total_run_user': max_sum_distance_run['athlete_id'],
         'total_run_value': max_sum_distance_run['sum_distance'],
         'speed_avg_user': max_avg_speed_run['athlete_id'],
         'speed_avg_value': max_avg_speed_run['avg_speed']
         }
    )


class AnalyticsForCoachAPIView(APIView):
    def get(self, request, coach_id):
        try:
            coach = User.objects.get(id=coach_id, is_staff=True)
        except User.DoesNotExist:
            return Response({'error': 'Тренер не найден'}, status=status.HTTP_404_NOT_FOUND)

        subscribed_athletes = AthleteCoachRelation.objects.filter(coach_id=coach_id).values_list('athlete_id',
                                                                                                      flat=True)

        if not subscribed_athletes:
            return Response({
                'longest_run_user': None,
                'longest_run_value': None,
                'total_run_user': None,
                'total_run_value': None,
                'speed_avg_user': None,
                'speed_avg_value': None
            }, status=status.HTTP_200_OK)

        finished_runs = Run.objects.filter(athlete_id__in=subscribed_athletes, status='finished')

        # Самый длинный забег
        longest_run = finished_runs.order_by('-distance').first()
        longest_run_user = longest_run.athlete_id if longest_run else None
        longest_run_value = longest_run.distance if longest_run else None

        # Общая дистанция по атлетам
        total_distance_by_athlete = finished_runs.values('athlete_id').annotate(
            total_distance=Sum('distance')
        ).order_by('-total_distance').first()

        total_run_user = total_distance_by_athlete['athlete_id'] if total_distance_by_athlete else None
        total_run_value = total_distance_by_athlete['total_distance'] if total_distance_by_athlete else None

        athletes_with_speed = User.objects.filter(
            id__in=subscribed_athletes
        ).annotate(
            avg_speed=Avg('run__speed', filter=Q(run__status='finished'))
        ).order_by('-avg_speed')

        # Берём атлета с максимальной средней скоростью
        speed_avg_user = None
        speed_avg_value = None

        print(f'DEBUG_0 {User.objects.filter(
            id__in=subscribed_athletes
        ).values('run__speed')}')

        for a_id in subscribed_athletes:
            for run in Run.objects.filter(athlete_id=a_id):
                print(f'DEBUG_1_run_1 {run.id}')
                print(f'DEBUG_1_run_2 {run.speed}')

        if athletes_with_speed.exists():
            print(f'DEBUG_1 {athletes_with_speed.exists()}')
            fastest_athlete = athletes_with_speed.first()
            print(f'DEBUG_2 {athletes_with_speed.first()}')
            if fastest_athlete.avg_speed is not None:
                print(f'DEBUG_3 {fastest_athlete.id}')
                speed_avg_user = fastest_athlete.id
                print(f'DEBUG_4 {fastest_athlete.avg_speed}')
                speed_avg_value = round(fastest_athlete.avg_speed, 2)

        analytics = {
            'longest_run_user': longest_run_user,
            'longest_run_value': longest_run_value,
            'total_run_user': total_run_user,
            'total_run_value': total_run_value,
            'speed_avg_user': speed_avg_user,
            'speed_avg_value': speed_avg_value
        }

        return Response(analytics, status=status.HTTP_200_OK)


# test 2
class UploadXLSX(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

        # Open the workbook
        workbook = openpyxl.load_workbook(file_obj)

        # Select the active worksheet
        worksheet = workbook.active

        # Read the contents
        data = []
        to_create = []
        for i, row in enumerate(worksheet.iter_rows(values_only=True)):
            if i == 0:
                continue
            valid = True
            types = [str, str, int, float, float, str]
            for index, sub_row in enumerate(row):
                if type(sub_row) != types[index]:
                    valid = False

            # TODO add feature here!!!

            if not type(row[3]) == float or not (-90 <= row[3] <= 90):
                valid = False

            if not type(row[4]) == float or not (-180 <= row[4] <= 180):
                valid = False

            if not validate_url(row[5]):
                valid = False

            if not valid:
                data.append(row)
            else:
                to_create.append(row)

        for item in to_create:
            CollectableItem.objects.create(name=item[0],
                                           uid=item[1],
                                           value=item[2],
                                           latitude=item[3],
                                           longitude=item[4],
                                           picture=item[5],
                                           )

        # Return the parsed data as JSON
        return JsonResponse(data, safe=False)


class CollectableItemViewSet(viewsets.ModelViewSet):
    queryset = CollectableItem.objects.all()
    serializer_class = CollectableItemSerializer


class AthleteInfoViewSet(viewsets.ModelViewSet):
    queryset = AthleteInfo.objects.all()
    serializer_class = AthleteInfoSerializer
    lookup_field = 'user_id'  # Use the native user ID for lookup

    def get_object(self):
        user_id = self.kwargs.get(self.lookup_field)
        user = get_object_or_404(User, id=user_id)
        user_info, _ = AthleteInfo.objects.get_or_create(user=user)
        return user_info
