#  Unisoft Group Copyright (c) 2022.
#
#  Created by Nursulton Kholmatoff
#  Before making any changes
#  Please contact by phone number: +998972444334, +998942711661
#  and allow access to this file
#
#  Tashkent, Uzbekistan

import datetime
import json

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from jsonrpcserver import method, Result, Error, Success, dispatch, InvalidParams
from re import compile as Pattern

from .models import Epos, Payments, ToCard, Transfers

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
            "access_token": token.access_token
        })
    return Error(254, "Invalid password")


@method(name='terminal.add')
def terminalAdd(context, merchant: str, terminal: str, type: str, purpose: str, point_code: str) -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if Epos.objects.filter(user=username, terminal=terminal, merchant=merchant).exists():
        result = {"error": {
            "code": 997,
            "message": "This EPOS has already been added for this user"

        }}
        return Success(result)

    epos = Epos(user=username)
    epos.merchant = merchant
    epos.terminal = terminal
    epos.type = type
    epos.purpose = purpose
    epos.point_code = point_code
    epos.originator = "wsuniversal"
    epos.center_id = "Unisoft"
    epos.status = True
    epos.save()

    result = {
        "message": "Epos successfully added!"
    }
    return Success(result)


@method(name='terminal.check')
def terminalCheck(context, merchant: str, terminal: str):
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not Epos.objects.filter(user=username, merchant=merchant, terminal=terminal).exists():
        return Error(code=10001, message="Epos is not authenticated")
    qs = Epos.objects.filter(user=username, terminal=terminal, merchant=merchant)
    if qs.exists():
        epos = qs.first()
    else:
        return Error(code=10001, message="User hasn't permission to use the EPOS")
    status_terminal = epos.status
    status = False
    if status_terminal is True:
        status = True
    result = {
        "message": "User has permission to use the EPOS",
        'status_terminal': status
    }
    return Success(result)


@method(name='terminal.remove')
def terminalRemove(context, merchant: str, terminal: str):
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not Epos.objects.filter(user=username, merchant=merchant, terminal=terminal).exists():
        return Error(code=10001, message="Epos is not authenticated")
    epos = Epos.objects.get(user=username, terminal=terminal, merchant=merchant)
    epos.status = False
    epos.save()
    result = {
        "message": "EPOS successfully removed!"
    }
    return Success(result)


@method(name='card.info')
def cardInfo(context, card_number: str) -> Result:
    if len(card_number) != 16:
        return Error(code=403, message='Card_number length must be 16 digits')
    if card_number[: 4] != '9860':
        return Error(code=404, message='Card not found or the card is not Humo type')

    return Success(
        {
            "card_number": card_number,
            'owner': 'Card owner',
            'bank': 'Bank name',
            'state': 0
        }
    )


@method(name='card.register')
def getBalance(context, card_number: str, expire: str) -> Result:
    if len(card_number) != 16:
        return Error(code=403, message='Card_number length must be 16 digits')
    if card_number[: 4] != '9860':
        return Error(code=404, message='Card not found or the card is not Humo type')
    if len(expire) != 4:
        return Error(code=777, message='Wrong expire!')
    result = {
        'card_number': card_number,
        'expire': expire,
        'mask': card_number[: 6] + '*****' + card_number[12:],
        'phone': '+998yyxxxxxxx',
        'sms': True,
        'balance': int(99999999999),
        'is_corporate': False,
        'status': 0,
        'state': 0,
        'owner': 'Card owner Name',
        'bank': 'Bankname',
        'account': 'Card account number'
    }
    return Success(result)


@method(name='get.by.phone')
def customerList(context, phone: str, bankId: str = "MB_STD", mb_flag: str = "1") -> Result:
    result = {
        'card_number': 9999999999999999,
        'expire': 9999
    }

    return Success(result)


@method(name='cards.passport')
def cardsByPassport(context, serial_no: str, id_card: str) -> Result:
    return Success({'status': 'Ok'})


@method(name='cards.pinfl')
def cardsByPersonCode(context, person_code: str) -> Result:
    return Success({'status': 'Ok'})


@method()
def scoring(context, card_number: str, date_from: str, date_to: str) -> Result:
    return Success({'status': 'Ok'})


@method(name='hold.create')
def holdCreate(context, ext_id: str, pan: str, expiry: str, amount: int, ccy_code: str = "860") -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not Epos.objects.filter(user=username, type='1').exists():
        return Error(code=10002, message={'uz': "Epos ro'yxatdan o'tkazilmagan!",
                                          'ru': "Epos is not authenticated",
                                          'en': "Epos is not authenticated"})
    if Payments.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10003, message="This EXT_ID has already been used for this user")
    Payments(user=username, ext_id=ext_id)
    return Success({'status': 'Ok'})


@method(name='hold.confirm')
def holdConfirm(context, ext_id: str) -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    qs = Payments.objects.filter(user=username, ext_id=ext_id)
    if not qs.exists():
        return Error(code=404, message='Payment not found!')
    return Success({'status': 'Ok'})


@method(name='hold.dismiss')
def holdCancel(context, ext_id: str) -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not Payments.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10007, message="Ext_id not found!")
    return Success({'status': 'Ok'})


@method(name='payment.reverse')
def payment_reverse(context, ext_id: str) -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not Payments.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10007, message="Ext_id not found!")
    return Success({'status': 'Ok'})


@method(name='transfer.credit.create')
def toCardCreate(context, ext_id: str, card_number: str, amount: str, merchant_id: str, terminal_id: str,
                 originator: str = 'wsuniversal', point_code: str = "100010104110",
                 center_id: str = 'Universal', ccy_code: str = '860', mb_flag: str = 1) -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not Epos.objects.filter(user=username, merchant=merchant_id, terminal=terminal_id, type='2',
                               status=True).exists():
        return Error(code=10002, message=f"Epos is not authenticated for user {username}")
    if ToCard.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10003, message="This EXT_ID has already been used for this user")
    ToCard(user=username, ext_id=ext_id)
    return Success({'status': 'Ok'})


@method(name='transfer.credit.confirm')
def toCardConfirm(context, ext_id) -> Result:
    username = context.get("user")
    if not username:
        return Error("User is not authenticated")
    if not ToCard.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10003, message="Ext_id not found")
    return Success({'status': 'Ok'})


@method(name='toCard.Cancel')
def toCardCancel(context, ext_id: str) -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not ToCard.objects.filter(user=username, ext_id=ext_id).exists():
        return Error(code=404, message='Payment not found')
    return Success({'status': 'Ok'})


@method(name='transfer.credit.state')
def transferCheck(context, ext_id: str) -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not ToCard.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10003, message="Ext_id not found")
    return Success({'status': 'Ok'})


@method(name='p2p')
def peer2peer(context, ext_id: str, sender: str, expire: str, receiver: str,
              amount: int, ccy_code: str = "860",
              paymentOriginator: str = "wsuniversal") -> Result:
    username = context.get("user")
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if Transfers.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10003, message="This EXT_ID has already been used for this user")
    Transfers(user=username, ext_id=ext_id)
    return Success({'status': 'Ok'})


@method(name='payment.create')
def create_3ds_payment(context, ext_id: str, card_number: str, expire: str, amount: int,
                       ccy_code: str = "860") -> Result:
    username = context.get("user")
    pan = 0
    if not username:
        return Error(code=10001, message="User is not authenticated")
    if not Epos.objects.filter(user=username, type='1').exists():
        return Error(code=10002, message="Epos is not authenticated")
    if Payments.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10003, message="This EXT_ID has already been used for this user")
    Payments(user=username, ext_id=ext_id)
    return Success({'status': 'Ok'})


@method(name='payment.confirm')
def confirmPayment3Ds(context, ext_id: str, code: str) -> Result:
    username = context.get("user")
    if not Payments.objects.filter(ext_id=ext_id, user=username).exists():
        return Error(code=10005, message={'en': "Ext_id does not exist!",
                                          'uz': "Mavjud bo'lmagan Ext_id!",
                                          'ru': "Ext_id, который не существует!"})
    return Success({'status': 'Ok'})

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
