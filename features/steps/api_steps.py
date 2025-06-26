import base64
import urllib3
import requests
from behave import given, when, then
import json
import re

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
        print("check")
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