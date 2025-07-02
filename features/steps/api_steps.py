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



@then('в случае когда поле "leadDTO.stateFeature.id" и статус "165"')
def step_impl(context):
    lead_id = field_value_map.get("id")

    endpoint = f"/agent-api/v1/lead-management/get-details/{lead_id}"
    max_attempts = 20
    interval = 10

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
        "/agent-auth/oauth/token?grant_type=password&password=QWEasd@1234567&username=980516301284&version=1.0.92%2B101",
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


@then('я извлекаю offerId с типом "[CEL][Cash Xsell][Real]" из ответа "/agent-api/v1/offer-store/offers/6092400"')
def step_impl(context):
    endpoint = "/agent-api/v1/offer-store/offers/6092400"
    data = endpoint_response_map.get(endpoint)

    assert data, f"❌ Нет сохранённого ответа для {endpoint}"

    # Пробуем извлечь список офферов
    try:
        offers = data.get("offerDTOList", [])
        assert offers, "❌ В ответе нет offerDTOList или он пуст"

        # Ищем оффер с нужным типом, кодом и loanOption
        found = None
        for offer in offers:
            if (offer.get("offerTypeName") == "[CEL][Cash Xsell][Real]" and
                    offer.get("offerProductCode") == "CEL" and
                    offer.get("loanOption") == "CASH_LOAN"):
                found = offer
                break

        assert found, "❌ Оффер с типом '[CEL][Cash Xsell][Real]', productCode 'CEL' и loanOption 'CASH_LOAN' не найден"

        # Сохраняем offerId и другие данные
        field_value_map["offerId"] = found["offerId"]
        field_value_map["offerProductCode"] = found["offerProductCode"]
        field_value_map["loanOption"] = found["loanOption"]

        print(f"✅ Найден оффер: offerId={found['offerId']}, offerProductCode={found['offerProductCode']}, loanOption={found['loanOption']}")

    except Exception as e:
        print(f"❌ Ошибка при разборе ответа: {e}")
        print("📦 Ответ:", data)
        raise


@when('я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с сохранёнными leadId и offerId')
def step_impl(context):
    # Получаем значения из сохранённых данных
    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    offer_id = field_value_map.get("offerId")
    offer_product_code = field_value_map.get("offerProductCode")
    loan_option = field_value_map.get("loanOption")

    # Проверяем наличие обязательных полей
    assert lead_id, "❌ leadId не найден в field_value_map"
    assert offer_id, "❌ offerId не найден в field_value_map"
    assert offer_product_code, "❌ offerProductCode не найден в field_value_map"
    assert loan_option, "❌ loanOption не найден в field_value_map"

    # Формируем тело запроса
    payload = {
        "leadId": lead_id,
        "offerId": offer_id,
        "offerProductCode": offer_product_code,
        "loanOption": loan_option,
        "requiredLoanAmount": 1000000
    }

    print("📤 Тело calculate запроса:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # Отправляем запрос
    response = context.api_client.post_with_auth(
        "/agent-api/v1/customer-offer/calculate",
        json=payload
    )
    context.response = response

    # Обрабатываем ответ
    try:
        response_json = response.json()
        print("✅ Ответ на calculate:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        endpoint_response_map["/agent-api/v1/customer-offer/calculate"] = response_json
    except Exception as e:
        print(f"❌ Не удалось распарсить JSON: {e}")
        print("📦 Текст ответа:", response.text)
        endpoint_response_map["/agent-api/v1/customer-offer/calculate"] = None
        raise
