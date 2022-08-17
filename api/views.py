import datetime
import json

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from jsonrpcserver import method, Result, Error, Success, dispatch, InvalidParams
from re import compile as Pattern

from .models import AccessToken, User

authorization_error = {
    'code': -32001,
    'message': "Not authorized",
    'data': 'Use "token" in your headers with given for you token to authorize'
}


@method
def registration(context, username: str, password: str) -> Result:
    user = User(username=username)
    user.set_password(raw_password=password)
    user.save()
    access_token = AccessToken.generate(user)
    return Success(str(access_token))

@method
def login(context, username: str, password: str) -> Result:
    qs = User.objects.filter(username=username)

    if not qs.exists():
        return Error(code=401, message={"uz": "Bunday foydalanuvchi mavjud emas",
                                        "ru": "Неавторизованный пользователь",
                                        "en": "Unauthorized user"})
    user = qs.first()
    token = AccessToken.objects.get(user=user)
    if user.check_password(password):
        return Success({
            "access_token": token.revoke()
        })
    return Error(254, "Invalid password")

@csrf_exempt
def jsonrpc(request):
    body = json.loads(request.body)
    id = body.get('id')

    method = body['method']
    headers = request.headers
    context = {}
    data = {
        "id": id,
        "jsonrpc": "2.0",
        "status": False,
        "error": None,
        "origin": method,
        "host": {
            'host': 'test.unipos.uz',
            'timestamp': None
        }
    }

    authorization = headers.get('Authorization')
    if method not in settings.ALLOWED_METHODS:
        pattern = Pattern(r'Bearer (.+)')
        try:
            if not pattern.match(authorization):
                data = {
                    "jsonrpc": "2.0",
                    "id": id,
                    "error": {
                        "message": "Authorization type must be Bearer",
                        "code": "000"
                    },
                    "status": False,
                    "origin": method,
                    "host": {
                        'host': 'test.unipos.uz',
                        'timestamp': str(datetime.datetime.now())
                    }
                }
                return JsonResponse(data)
        except:
            data = {
                "jsonrpc": "2.0",
                "id": id,
                "error": authorization_error,
                "status": False,
                "origin": method,
                "host": {
                    'host': 'test.unipos.uz',
                    'timestamp': str(datetime.datetime.now())
                }
            }
            return JsonResponse(data)
        input_token = pattern.findall(authorization)[0]

        try:
            token = AccessToken.objects.get(access_token=input_token)
            context['user'] = token.user.username
        except AccessToken.DoesNotExist:
            data = {
                "jsonrpc": "2.0",
                "id": id,
                "error": authorization_error,
                "status": False,
                "origin": method,
                "host": {
                    'host': 'test.unipos.uz',
                    'timestamp': str(datetime.datetime.now())
                }
            }
            return JsonResponse(data)

    data = json.loads(dispatch(request.body.decode(), context=context))

    data['status'] = 'result' in data
    data['origin'] = method
    data['host'] = {
        'host': 'test.unipos.uz',
        'timestamp': str(datetime.datetime.now())
    }
    return HttpResponse(
        json.dumps(data), content_type="application/json")
