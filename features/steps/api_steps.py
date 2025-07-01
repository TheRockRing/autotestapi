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
    # Всё в порядке, данные есть
        print("✅ Данные найдены:", endpoint_response_map[endpoint])
    else:
        print(f"❌ Нет данных для endpoint: {endpoint}")

    json_body = endpoint_response_map[endpoint]
    parts =  key.split(".")
    result = json_body
    for f in parts:
        assert f in result
        field_value_map[key] = result[f]


@then('статус ответа {status_code:d}')
def step_impl(context, status_code):
    assert context.response.status_code == status_code

@then('поле "{field}" равен "{value}"')
def step_impl(context, field, value):
    json_body = context.response.json()
    parts =  field.split(".")
    result = json_body
    for f in parts:
        assert f in result
        result = result[f]
    assert str(result) == value, f"Поле '{field}' не содержит '{value}'. Получено '{result}'"




urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@when('отправляю запрос на получение токена')
def step_impl(context):
    b64_auth = 'Q0xJRU5UX1dFQjowMTgzMGU0NC1kZGE1LTRiNmMtYjE0Mi04NjNmNTc3ZGIzODU='
    context.headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_auth}"
    }
    context.response = context.api_client.post_header(
        "/agent-auth/oauth/token?grant_type=password&password=QWEasd@1234567&username=980516301284&version=1.0.92%2B101",
        context.headers
    )
    token = context.response.json().get("access_token")
    with open("token.txt", "w") as f:
        f.write(token)


@then('ответ содержит поле "{field}"')
def response_contains_field(context, field):
    json_body = context.response.json()
    parts = field.split(".")
    result = json_body
    for part in parts:
        result = result[part]
    print(f"Значение поля '{field}': {result}")

    assert result is not None


@when('я отправляю GET запрос "{endpoint}"')
def step_impl(context, endpoint):
    url = f"https://dev-agent.homecredit.kz/{endpoint}"

    response = requests.get(url, verify=False)
    context.response = response

@then('статус ответа {status_code:d}')
def step_impl(context, status_code):
    actual_status = context.response.status_code
    try:
        body = context.response.text
    except Exception as e:
        body = f"(не удалось прочитать тело: {e})"

    if actual_status != status_code:
        print("\n🚨 Ошибка: статус ответа не совпадает!")
        print(f"Ожидался: {status_code}")
        print(f"Получен:  {actual_status}")
        print("Тело ответа:")
        print(body)
    assert actual_status == status_code


@when('беру ключ из ответа generate и отправляю запрос "/agent-api/v1/otp/validate-save"')
def step_impl(context):
    with open("token.txt") as f:
        token = f.read().strip()

    json_body = context.response.json()
    otp_key = json_body.get("key")

    url = "https://dev-agent.homecredit.kz/agent-api/v1/otp/validate-save"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {
        "code": "1111",
        "key": otp_key
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)
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


# @when('я отправляю GET запрос на "{endpoint}" с токеном')
#  def step_impl_(context, endpoint):
#      match = re.search(r"\{\{\{(.*?)\}\}\}", endpoint)
#      if match:
#          field_name = match.group(1)
#         value = field_value_map[field_name]
#         assert value != ''
#         endpoint = endpoint.replace("{{{"+field_name+"}}}", str(value))
#
#     context.response = context.api_client.get_with_auth(endpoint)
#      endpoint_response_map[endpoint] = context.response.json()


@then('беру из ответа "{endpoint}" offerId из {index:d}-го оффера')
def step_impl(context, endpoint, index):
    data = endpoint_response_map[endpoint]
    offer_id = data['offerDTOList'][index]['offerId']
    field_value_map['offerId'] = offer_id
    print(f"📌 Сохранили offerId = {offer_id}")


@when('я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с offerId и leadId')
def step_impl(context):
    offer_id = field_value_map.get("offerId")
    lead_id = field_value_map.get("leadId")

    assert offer_id, "❌ offerId не найден в field_value_map"
    assert lead_id, "❌ leadId не найден в field_value_map"

    endpoint = "/agent-api/v1/customer-offer/calculate"
    payload = {
        "leadId": lead_id,
        "requiredLoanAmount": 1000000,
        "offerId": offer_id
    }

    context.response = context.api_client.post_with_auth(endpoint, json=payload)
    print("📤 calculate payload:", json.dumps(payload, indent=2, ensure_ascii=False))
    print("📥 Ответ:", context.response.status_code, context.response.text)

@when('я отправляю POST запрос на "/agent-api/v1/offer-store/offers/{{{leadId}}}" и сохраняю offerId с типом "[CEL][Cash Xsell][Real]"')
def step_impl(context):
    import json

    # Подставляем leadId в endpoint
    lead_id = field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"
    endpoint = f"/agent-api/v1/offer-store/offers/{lead_id}"

    # Выполняем POST запрос
    context.response = context.api_client.post_with_auth(endpoint)

    try:
        response_json = context.response.json()
        endpoint_response_map[endpoint] = response_json

        print(f"✅ Ответ от {endpoint}:\n{json.dumps(response_json, indent=2, ensure_ascii=False)}")

        offers = response_json.get("offerDTOList", [])
        found = False

        for offer in offers:
            if offer.get("offerTypeName") == "[CEL][Cash Xsell][Real]":
                offer_id = offer.get("offerId")
                assert offer_id, "❌ offerId отсутствует"
                field_value_map["offerId"] = offer_id

                # Сохраняем в файл
                with open("offerId_Cash_Xsell_Real.txt", "w", encoding="utf-8") as f:
                    f.write(offer_id)

                print(f"💾 Сохранён offerId: {offer_id} в offerId_Cash_Xsell_Real.txt")
                found = True
                break

        if not found:
            print("⚠️ Не найдено предложение с типом '[CEL][Cash Xsell][Real]'")

    except Exception as e:
        print(f"❌ Ошибка при обработке JSON: {e}")
        print("📦 Текст ответа:", context.response.text)

@when('я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с сохранёнными leadId и offerId')
def step_impl(context):
    lead_id = field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"


    for _ in range(0, max_wait, poll_interval):
        endpoint = f"/agent-api/v1/offer-store/offers/{lead_id}"
        response = context.api_client.get_with_auth(endpoint)
сохранёнными leadId и offerId
        try:
            response_json = response.json()
            offers = response_json.get("offerDTOList", [])

            for offer in offers:
                if offer.get("offerTypeName") == "[CEL][Cash Xsell][Real]":
                    offer_id = offer.get("offerId")
                    field_value_map["offerId"] = offer_id
                    endpoint_response_map[endpoint] = response_json
                    print(f"✅ Найден offerId: {offer_id}")
                    break

            if offer_id:
                break

        except Exception as e:
            print(f"⚠️ Ошибка при чтении офферов: {e}")

        time.sleep(poll_interval)

    assert offer_id, f"❌ Не удалось найти оффер с типом '[CEL][Cash Xsell][Real]' за {max_wait} секунд"

    # 📦 Отправка запроса calculate
    payload = {
        "leadId": lead_id,
        "offerId": offer_id,
        "requiredLoanAmount": 1_000_000
    }

    print("📦 Тело запроса:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    response = context.api_client.post_with_auth(
        "/agent-api/v1/customer-offer/calculate",
        json=payload
    )

    try:
        response_json = response.json()
        print("✅ Ответ:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        endpoint_response_map["/agent-api/v1/customer-offer/calculate"] = response_json
    except Exception as e:
        print(f"❌ Не удалось распарсить JSON: {e}")
        print("📦 Ответ:", response.text)
        endpoint_response_map["/agent-api/v1/customer-offer/calculate"] = None


@when('в то время когда отправляю GET запрос на "/agent-api/v1/offer-store/offers/{{{leadId}}}" и сохраняю offerId с типом "[CEL][Cash Xsell][Real]"')
def step_impl(context):
    lead_id = field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"
    endpoint = f"/agent-api/v1/offer-store/offers/{lead_id}"

    max_wait = 15  # секунд
    interval = 1   # секунд между попытками
    start = time.time()
    offer_id = None

    while time.time() - start < max_wait:
        context.response = context.api_client.get_with_auth(endpoint)

        try:
            response_json = context.response.json()
            endpoint_response_map[endpoint] = response_json

            offers = response_json.get("offerDTOList", [])
            for offer in offers:
                if offer.get("offerTypeName") == "[CEL][Cash Xsell][Real]":
                    offer_id = offer.get("offerId")
                    field_value_map["offerId"] = offer_id

                    with open("offerId_Cash_Xsell_Real.txt", "w", encoding="utf-8") as f:
                        f.write(offer_id)

                    print(f"✅ Найден offerId: {offer_id}")
                    return  # Успешно найден и сохранён

        except Exception as e:
            print(f"⚠️ Ошибка при разборе JSON: {e}")
            print("📦 Ответ:", context.response.text)

        print("⏳ Ждём генерацию офферов...")
        time.sleep(interval)

    # Если сюда дошли — оффер не найден за время ожидания
    raise AssertionError("❌ Оффер типа '[CEL][Cash Xsell][Real]' не появился за 15 секунд")


@then('когда поле "{field}" равен "{value}"')
def step_impl(context, field, value):
    assert hasattr(context, "last_get_endpoint"), "❌ context.last_get_endpoint не установлен. Сначала сделай GET запрос."

    max_attempts = 20
    interval = 3

    for attempt in range(max_attempts):
        response = context.api_client.get_with_auth(f"/agent-api/v1/lead-management/get-details/")
        try:
            json_body = response.json()
            parts = field.split(".")
            result = json_body
            for f in parts:
                assert f in result, f"❌ Поле '{f}' не найдено в ответе"
                result = result[f]

            if str(result) == value:
                print(f"✅ [{attempt+1}] Поле '{field}' стало равно '{value}'")
                return
            else:
                print(f"⏳ [{attempt+1}] Ожидание: '{field}' = '{value}', сейчас: '{result}'")

        except Exception as e:
            print(f"❌ Ошибка при парсинге JSON: {e}")

        time.sleep(interval)

    assert False, f"⛔ Поле '{field}' не стало '{value}' за {max_attempts * interval} секунд"