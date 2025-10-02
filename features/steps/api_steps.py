import base64
import urllib3
import requests
from behave import given, when, then
import json
import re
import time

endpoint_response_map = {}
field_value_map = {}

@when('я отправляю GET запрос на "{endpoint}"')
def step_impl(context, endpoint):
    context.response = context.api_client.get(endpoint)



@then('беру из ответа "{endpoint}" поле "{key}"')
def step_impl(context, endpoint, key):
    if endpoint in endpoint_response_map and endpoint_response_map[endpoint] is not None:
        print("✅ Данные найдены:", endpoint_response_map[endpoint])
    else:
        print(f"❌ Нет данных для endpoint: {endpoint}")

    json_body = endpoint_response_map[endpoint]
    parts = key.split(".")
    result = json_body
    for f in parts:
        if isinstance(result, list) and f.isdigit():  # если массив
            result = result[int(f)]
        else:
            assert f in result, f"❌ Ключ {f} не найден в {result}"
            result = result[f]

    # сохраняем обычное поле
    field_value_map[key] = result
    print(f"✅ Сохранили {key}: {result}")

    # 👉 если это id из create лида, сразу сохраняем и как leadApplicationId
    if key == "id" and "/agent-api/v2/lead-management/create" in endpoint:
        field_value_map["leadApplicationId"] = result
        print(f"✅ leadApplicationId тоже сохранён: {result}")


@then('статус ответа {status_code:d}')
def step_impl(context, status_code):
    assert context.response.status_code == status_code


@then('ответ содержит поле "{field}"')
def response_contains_field(context, field):
    json_body = context.response.json()
    parts = field.split(".")
    result = json_body
    for part in parts:
        result = result[part]
    print(f"Значение поля '{field}': {result}")

    assert result is not None


@then('поле с "{field}" равен "{value}"')
def step_impl(context, field, value):
    json_body = context.response.json()
    parts =  field.split(".")
    result = json_body
    for f in parts:
        assert f in result
        result = result[f]
    assert str(result) == value, f"Поле '{field}' не содержит '{value}'. Получено '{result}'"



@then('Ожидаю когда поле "leadDTO.stateFeature.id" и статус "165"')
def step_impl(context):
    lead_id = field_value_map.get("id")

    endpoint = f"/agent-api/v1/lead-management/get-details/{lead_id}"
    max_attempts = 20
    interval = 5

    for attempt in range(1, max_attempts + 1):
        response = context.api_client.get_with_auth(endpoint)
        try:
            json_body = response.json()
            state_feature_id = json_body["leadDTO"]["stateFeature"]["id"]

            if str(state_feature_id) == "165":
                print(f"✅ Попытка {attempt}: stateFeature.id = 165")
                return
            else:
                print(f"⏳ Попытка {attempt}: stateFeature.id = {state_feature_id}, ожидаем 165")

        except Exception as e:
            print(f"⚠️ Ошибка при обработке ответа: {e}")
            print("📦 Ответ:", response.text)

        if attempt < max_attempts:
            time.sleep(interval)




urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@when('отправляю запрос на получение токена')
def step_impl(context):
    b64_auth = 'Q0xJRU5UX1dFQjowMTgzMGU0NC1kZGE1LTRiNmMtYjE0Mi04NjNmNTc3ZGIzODU='
    context.headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_auth}"
    }
    context.response = context.api_client.post_header(
        "/agent-auth/oauth/token?grant_type=password&password=QWEasd@54321&username=980516301284&version=1.0.96%2B105",
        context.headers
    )
    token = context.response.json().get("access_token")
    with open("token.txt", "w") as f:
        f.write(token)


@then('поле "{field}" равен "{value}"')
def step_impl(context, field, value):
    json_body = context.response.json()
    parts =  field.split(".")
    result = json_body
    for f in parts:
        assert f in result
        result = result[f]
    assert str(result) == value, f"Поле '{field}' не содержит '{value}'. Получено '{result}'"


@when('я отправляю GET запрос "{endpoint}"')
def step_impl(context, endpoint):
    url = f"https://dev-agent.homecredit.kz/{endpoint}"

    response = requests.get(url, verify=False)
    context.response = response


@then('получаю ответ равный')
def step_impl(context):
    expected = json.loads(context.text)  # получаем ожидаемый JSON из feature-файла
    actual = context.response.json()     # получаем фактический JSON от API

    assert actual == expected, f"\nОжидалось: {expected}\nПолучено: {actual}"

@when('я отправляю GET запрос на "{endpoint}" с токеном')

def step_impl_(context, endpoint):
    match = re.search(r"\{\{\{(.*?)\}\}\}", endpoint)
    if match:
        field_name = match.group(1)
        value = field_value_map.get(field_name)
        assert value, f"❌ Поле {field_name} не найдено в field_value_map или пустое"
        endpoint = endpoint.replace(f"{{{{{{{field_name}}}}}}}", str(value))

    context.response = context.api_client.get_with_auth(endpoint)

    try:
        response_json = context.response.json()
        endpoint_response_map[endpoint] = response_json
        print(f"✅ JSON из {endpoint}:\n{json.dumps(response_json, indent=2, ensure_ascii=False)}")
        print(response_json)

    except Exception as e:
        print(f"❌ Не удалось распарсить JSON с {endpoint}: {e}")
        print("📦 Ответ:", context.response.text)
        endpoint_response_map[endpoint] = None

    print(response_json)

    context.response = context.api_client.get_with_auth(endpoint)
    endpoint_response_map[endpoint] = context.response.json()

@when('я отправляю POST запрос на "{endpoint}" и токеном')
def step_impl_(context, endpoint):
    # Очищаем текст от \r и \n, но сохраняем структуру JSON
    clean_text = context.text.replace('\r', '').replace('\n', '')

    # Обработка шаблона {{{key}}}
    match = re.search(r"\{\{\{(.*?)\}\}\}", clean_text)
    if match:
        field_name = match.group(1)
        value = field_value_map.get(field_name, '')
        assert value != '', f"Значение поля {field_name} пустое"
        clean_text = clean_text.replace(f"{{{{{{{field_name}}}}}}}", value)

    # Убираем лишние экранирования если они есть
    clean_text = clean_text.replace('\\', '')

    # Преобразуем в JSON
    payload = json.loads(clean_text)

    context.response = context.api_client.post_with_auth(endpoint, payload)
    endpoint_response_map[endpoint] = context.response.json()


@when('я отправляю GET запрос "/agent-api/v2/lead-management/create" с токеном')
def step_impl(context):
    with open("token.txt") as f:
        token = f.read().strip()

    url = "https://dev-agent.homecredit.kz/agent-api/v2/lead-management/create"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers, verify=False)
    context.response = response


@then(u'получаю статус ответа 200')
def step_impl(context):
    assert context.response.status_code == 200, \
        f"Ожидался статус 200, но получен {context.response.status_code}"



@then('я извлекаю offerId с типом "[CEL][Cash Xsell][Real]" из ответа')
def step_impl(context):
    import re

    def is_uuid_like(v: str) -> bool:
        return isinstance(v, str) and bool(re.match(r'^[0-9a-fA-F-]{36}$', v))

    lead_id = field_value_map.get("id")
    assert lead_id, "❌ leadId не найден в field_value_map"

    endpoint = f"/agent-api/v1/offer-store/offers/{lead_id}"
    data = endpoint_response_map.get(endpoint)
    assert data, f"❌ Нет сохранённого ответа для {endpoint}"

    offers = data.get("offerDTOList", [])
    assert offers, "❌ В ответе нет offerDTOList"

    found = next(
        (o for o in offers
         if o.get("offerTypeName") == "[CEL][Cash Xsell][Real]"
         and o.get("offerProductCode") == "CEL"
         and o.get("loanOption") == "CASH_LOAN"),
        None
    )
    assert found, "❌ Оффер '[CEL][Cash Xsell][Real]' не найден"

    raw = found.get("offerId") or found.get("offerUuid") or found.get("code")
    assert raw, "❌ Ни offerId, ни offerUuid, ни code не найдены в оффере"

    # Сохраняем всё, что можем
    if isinstance(raw, int) or (isinstance(raw, str) and raw.isdigit()):
        field_value_map["offerId"] = int(raw)
        print(f"✅ offerId (Long) = {field_value_map['offerId']}")
    elif is_uuid_like(raw):
        field_value_map["offerUuid"] = raw
        print(f"✅ offerUuid (UUID) = {field_value_map['offerUuid']}")
    else:
        field_value_map["offerCode"] = raw
        print(f"✅ offerCode = {field_value_map['offerCode']}")

    field_value_map["offerProductCode"] = found.get("offerProductCode")
    field_value_map["loanOption"]       = found.get("loanOption")

    print("✅ Итог по офферу:",
          {k: field_value_map.get(k) for k in ["offerId","offerUuid","offerCode","offerProductCode","loanOption"]})


# @then('я извлекаю offerId с типом "[CEL][Cash Xsell][Real]" из ответа "/agent-api/v1/offer-store/offers/6092400"')
# def step_impl(context):
#     endpoint = "/agent-api/v1/offer-store/offers/6092400"
#     data = endpoint_response_map.get(endpoint)
#
#     assert data, f"❌ Нет сохранённого ответа для {endpoint}"
#
#     # Пробуем извлечь список офферов
#     try:
#         offers = data.get("offerDTOList", [])
#         assert offers, "❌ В ответе нет offerDTOList или он пуст"
#
#         # Ищем оффер с нужным типом, кодом и loanOption
#         found = None
#         for offer in offers:
#             if (offer.get("offerTypeName") == "[CEL][Cash Xsell][Real]" and
#                     offer.get("offerProductCode") == "CEL" and
#                     offer.get("loanOption") == "CASH_LOAN"):
#                 found = offer
#                 break
#
#         assert found, "❌ Оффер с типом '[CEL][Cash Xsell][Real]', productCode 'CEL' и loanOption 'CASH_LOAN' не найден"
#
#         # Сохраняем offerId и другие данные
#         field_value_map["offerId"] = found["offerId"]
#         field_value_map["offerProductCode"] = found["offerProductCode"]
#         field_value_map["loanOption"] = found["loanOption"]
#
#         print(f"✅ Найден оффер: offerId={found['offerId']}, offerProductCode={found['offerProductCode']}, loanOption={found['loanOption']}")
#
#     except Exception as e:
#         print(f"❌ Ошибка при разборе ответа: {e}")
#         print("📦 Ответ:", data)
#         raise


@when('я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с сохранёнными leadId и offerId')
def step_impl(context):
    lead_id            = field_value_map.get("id") or field_value_map.get("leadId")
    offer_product_code = field_value_map.get("offerProductCode")
    loan_option        = field_value_map.get("loanOption")

    # Для offer — берём то, что нашли ранее (id или uuid или code)
    offer_for_req = (field_value_map.get("offerId") or
                     field_value_map.get("offerUuid") or
                     field_value_map.get("offerCode"))
    assert lead_id, "❌ leadId не найден"
    assert offer_for_req, "❌ offerId/offerUuid/offerCode не найдены"
    assert offer_product_code, "❌ offerProductCode не найден"
    assert loan_option, "❌ loanOption не найден"


    payload = {
        "leadId": lead_id,
        "offerId": offer_for_req,              # сервер принимает строку/число
        "offerProductCode": offer_product_code,
        "loanOption": loan_option,
        "requiredLoanAmount": 1000000
    }
    print("📤 calculate payload:", json.dumps(payload, ensure_ascii=False))

    response = context.api_client.post_with_auth("/agent-api/v1/customer-offer/calculate", payload)
    context.response = response

    resp = response.json()
    endpoint_response_map["/agent-api/v1/customer-offer/calculate"] = resp
    print("✅ Ответ calculate:", json.dumps(resp, indent=2, ensure_ascii=False))

    # Сохраняем code (для update)
    first = resp.get("customerOffers", [{}])[0]
    code  = first.get("code")
    if code:
        field_value_map["customerOfferCode"] = code
        print(f"✅ customerOfferCode={code}")

    # leadApplicationId в calculate может не приходить — фолбэк на lead id
    if not field_value_map.get("leadApplicationId"):
        if lead_id:
            field_value_map["leadApplicationId"] = lead_id
            print(f"ℹ️ leadApplicationId не пришёл — используем id лида: {lead_id}")



@when('я отправляю POST запрос на "/agent-api/v1/files/send-img-to-auth" с 3 фото')
def step_impl(context):
    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"

    def file_to_base64(filepath):
        with open(filepath, "rb") as file:
            return base64.b64encode(file.read()).decode("utf-8")

    payload = {
        "leadId": lead_id,
        "lang": "RUS",
        "leadFilesDTOS": [
            {
                "type": "id_card_front",
                "data": file_to_base64("features/resources/id_card_front.jpg"),
                "fileId": None
            },
            {
                "type": "id_card_back",
                "data": file_to_base64("features/resources/id_card_back.jpg"),
                "fileId": None
            },
            {
                "type": "selfie",
                "data": file_to_base64("features/resources/selfie.jpg"),
                "fileId": None
            }
        ]
    }

    print("📤 Тело запроса:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    url = f"{context.api_client.base_url}/agent-api/v1/files/send-img-to-auth"
    with open("token.txt") as f:
        token = f.read().strip()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, verify=False)
    context.response = response

    try:
        response_json = response.json()
        print("✅ Ответ:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        endpoint_response_map["/agent-api/v1/files/send-img-to-auth"] = response_json
    except Exception as e:
        print(f"❌ Ошибка при разборе ответа: {e}")
        print("📦 Текст ответа:", response.text)
        endpoint_response_map["/agent-api/v1/files/send-img-to-auth"] = None
        raise


@when('я отправляю POST запрос на "/agent-api/v1/application-management/update" с leadApplicationId')
def step_impl(context):
    lead_application_id = field_value_map.get("leadApplicationId") or field_value_map.get("id")
    assert lead_application_id, "❌ leadApplicationId не найден (и id лида тоже)"

    # Разруливаем тип offer: если UUID — НЕ отправлять offerId, а отправить offerUuid
    raw_offer_id = field_value_map.get("offerId")
    raw_uuid     = field_value_map.get("offerUuid")
    offer_code   = field_value_map.get("offerCode")
    calc_code    = field_value_map.get("customerOfferCode")  # code из calculate

    payload = {
        "leadApplicationId": lead_application_id,
        "creditAmount": 1000000,
        "downPayment": 0,
        "loanOption": "CASH_LOAN",
        "offerProductCode": field_value_map.get("offerProductCode", "XSTNF--FFP"),
        "offerProductType": "CEL",
        "actualAmount": None,
        "creditType": None,
        "incomeAmount": None,
        "incomeAmountTypeCode": None,
        "instantCardType": None,
        "namePartner": None,
        "offerRelipCode": None,
        "paymentServiceCode": None,
        "saleRoomCode": None,
        "saleRoomName": None
    }

    # добавляем code из calculate (обязательно)
    if calc_code:
        payload["code"] = calc_code

    # добавляем offerId/offerUuid корректно
    if isinstance(raw_offer_id, int):
        payload["offerId"] = raw_offer_id                # Long OK
    elif isinstance(raw_offer_id, str) and raw_offer_id.isdigit():
        payload["offerId"] = int(raw_offer_id)           # привести к Long
    elif raw_uuid:
        payload["offerUuid"] = raw_uuid                  # UUID -> отдельное поле
    elif offer_code and "code" not in payload:
        # как крайний случай можно положить code от оффера (если сервер это поддерживает)
        payload["code"] = offer_code

    print("📤 update payload:", json.dumps(payload, indent=2, ensure_ascii=False))

    response = context.api_client.post_with_auth("/agent-api/v1/application-management/update", payload)
    context.response = response

    try:
        resp = response.json()
        print("✅ Ответ update:", json.dumps(resp, indent=2, ensure_ascii=False))
        endpoint_response_map["/agent-api/v1/application-management/update"] = resp
    except Exception as e:
        print("❌ Ошибка парсинга update:", e)
        print("📦 raw:", response.text)
        endpoint_response_map["/agent-api/v1/application-management/update"] = None
        raise



@when('я отправляю POST запрос на "/agent-api/v2/lead-management/update" с id и фото')
def step_impl(context):
    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"

    def file_to_base64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "id": lead_id,
        "userId": None,
        "lastName": None,
        "lastNameLat": None,
        "firstName": None,
        "firstNameLat": None,
        "middleName": None,
        "nin": None,
        "phoneNumber": None,
        "salesRoomCode": None,
        "iban": None,
        "productCode": None,
        "langCode": None,
        "bankBranch": None,
        "statusId": None,
        "contacts": None,
        "refinancingContracts": None,
        "securityQuestion": None,
        "securityQuestionID": None,
        "codeDisbursementChannel": None,
        "leadPensionersID": None,
        "leadFilesDTOS": [
            {
                "type": "id_card_front",
                "data": file_to_base64("features/resources/id_card_front.jpg"),
                "fileId": None
            },
            {
                "type": "id_card_back",
                "data": file_to_base64("features/resources/id_card_back.jpg"),
                "fileId": None
            },
            {
                "type": "selfie",
                "data": file_to_base64("features/resources/selfie.jpg"),
                "fileId": None
            }
        ]
    }

    print("📤 Тело запроса к /agent-api/v2/lead-management/update:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    response = context.api_client.post_with_auth(
        "/agent-api/v2/lead-management/update",
        payload
    )
    context.response = response

    try:
        response_json = response.json()
        print("✅ Ответ:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        endpoint_response_map["/agent-api/v2/lead-management/update"] = response_json
    except Exception as e:
        print(f"❌ Ошибка при разборе ответа: {e}")
        print("📦 Текст ответа:", response.text)
        endpoint_response_map["/agent-api/v2/lead-management/update"] = None
        raise


@when('я отправляю POST запрос на "/agent-api/v1/files/send-img-to-auth" с base64 фото')
def step_impl(context):
    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"

    def file_to_base64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "leadId": lead_id,
        "lang": "RUS",
        "leadFilesDTOS": [
            {
                "type": "id_card_front",
                "data": file_to_base64("features/resources/id_card_front.jpg"),
                "fileId": None
            },
            {
                "type": "id_card_back",
                "data": file_to_base64("features/resources/id_card_back.jpg"),
                "fileId": None
            },
            {
                "type": "selfie",
                "data": file_to_base64("features/resources/selfie.jpg"),
                "fileId": None
            }
        ]
    }

    print("📤 Тело запроса (send-img-to-auth):")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    url = "https://dev-agent.homecredit.kz/agent-api/v1/files/send-img-to-auth"
    with open("token.txt") as f:
        token = f.read().strip()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, verify=False)
    context.response = response

    try:
        response_json = response.json()
        print("✅ Ответ send-img-to-auth:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        endpoint_response_map["/agent-api/v1/files/send-img-to-auth"] = response_json
    except Exception as e:
        print(f"❌ Ошибка при парсинге ответа: {e}")
        print("📦 Текст ответа:", response.text)
        endpoint_response_map["/agent-api/v1/files/send-img-to-auth"] = None
        raise
