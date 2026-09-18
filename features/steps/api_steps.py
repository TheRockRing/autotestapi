
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
        context.lead_id = result
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



def _normalize_status(value):
    if value is None:
        return ""
    raw = str(value).strip()
    try:
        return str(int(float(raw)))
    except (ValueError, TypeError):
        return raw


def _extract_state_feature_id(json_body):
    lead_dto = json_body.get("leadDTO") if isinstance(json_body, dict) else None
    if not isinstance(lead_dto, dict):
        lead_dto = json_body if isinstance(json_body, dict) else {}

    sf = lead_dto.get("stateFeature")
    if isinstance(sf, dict):
        status = sf.get("id")
    elif isinstance(sf, list) and sf:
        item = sf[-1]
        status = item.get("id") if isinstance(item, dict) else item
    else:
        status = sf

    if status is None:
        status = lead_dto.get("stateFeatureId")
    if status is None and isinstance(lead_dto.get("state"), dict):
        status = lead_dto["state"].get("id")
    return status


@then('Ожидаю когда поле "leadDTO.stateFeature.id" и статус "165" или "5"')
def step_impl(context):
    from utils.teams_notifier import notify_lead_failure, notify_lead_success

    lead_id = field_value_map.get("id") or getattr(context, "lead_id", None)

    endpoint = f"/agent-api/v1/lead-management/get-details/{lead_id}"
    max_attempts = 40
    interval = 5
    last_status = None
    found_status = None
    ok_statuses = {"165", "5"}

    for attempt in range(1, max_attempts + 1):
        response = context.api_client.get_with_auth(endpoint)
        try:
            json_body = response.json()
            state_feature_id = _extract_state_feature_id(json_body)
            last_status = state_feature_id
            status_str = _normalize_status(state_feature_id)

            if status_str in ok_statuses:
                print(f"✅ Попытка {attempt}: stateFeature.id = {state_feature_id}")
                found_status = status_str
                break
            print(f"⏳ Попытка {attempt}: stateFeature.id = {state_feature_id}, ожидаем 165 или 5")
        except Exception as e:
            print(f"⚠️ Ошибка при обработке ответа: {e}")
            print("📦 Ответ:", getattr(response, "text", response))

        if attempt < max_attempts:
            time.sleep(interval)



    reason = f"Статус 165 или 5 не получен (последний: {last_status})"
    notify_lead_failure(lead_id=lead_id, reason=reason)
    context.teams_notified = True
    assert False, f"❌ {reason}, leadId={lead_id}"




urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@when('отправляю запрос на получение токена')
def step_impl(context):
    b64_auth = ''
    context.headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {b64_auth}"
    }
    context.response = context.api_client.post_header(
        "/agent-auth/oauth/token?grant_type=",
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
    url = f"/{endpoint}"

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
    except Exception as e:
        print(f"❌ Не удалось распарсить JSON с {endpoint}: {e}")
        print("📦 Ответ:", context.response.text)
        endpoint_response_map[endpoint] = None


@then('беру OTP код из БД по телефону "{phone}"')
def step_impl(context, phone):
    from utils.db_client import DbClient

    otp_code = DbClient().get_otp_by_phone(phone)
    field_value_map["otp_code"] = otp_code
    print(f"✅ otp_code сохранён: {otp_code}")


@when('я отправляю POST запрос на "{endpoint}" и токеном')
def step_impl_(context, endpoint):
    # Очищаем текст от \r и \n, но сохраняем структуру JSON
    clean_text = context.text.replace('\r', '').replace('\n', '')

    # Обработка всех шаблонов {{{field}}}
    for field_name in re.findall(r"\{\{\{(.*?)\}\}\}", clean_text):
        value = field_value_map.get(field_name, '')
        assert value != '', f"Значение поля {field_name} пустое"
        clean_text = clean_text.replace(f"{{{{{{{field_name}}}}}}}", str(value))

    # Преобразуем в JSON
    payload = json.loads(clean_text)

    context.response = context.api_client.post_with_auth(endpoint, payload)
    endpoint_response_map[endpoint] = context.response.json()


@when('я отправляю GET запрос "/agent-api/v2/lead-management/create" с токеном')
def step_impl(context):
    with open("token.txt") as f:
        token = f.read().strip()

    url = "management/create"

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



@then('я извлекаю offerId с типом "{offer_type}" из ответа')
def step_impl(context, offer_type):
    import re

    def is_uuid_like(v: str) -> bool:
        return isinstance(v, str) and bool(re.match(r'^[0-9a-fA-F-]{36}$', v))

    lead_id = field_value_map.get("id")
    assert lead_id, " leadId не найден в field_value_map"

    endpoint = f"/agent-api/v1/offer-store/offers/{lead_id}"
    data = endpoint_response_map.get(endpoint)
    assert data, f" Нет сохранённого ответа для {endpoint}"

    offers = data.get("offerDTOList", [])
    assert offers, " В ответе нет offerDTOList"

    # ищем оффер по имени (то, что передал ты в feature)
    found = next((o for o in offers if o.get("offerTypeName") == offer_type), None)
    assert found, f" Оффер '{offer_type}' не найден"

    raw = found.get("offerId") or found.get("offerUuid") or found.get("code")
    assert raw, " Ни offerId, ни offerUuid, ни code не найдены в оффере"

    # Сохраняем offerId/Uuid/Code в field_value_map
    if isinstance(raw, int) or (isinstance(raw, str) and raw.isdigit()):
        field_value_map["offerId"] = int(raw)
        print(f" offerId (Long) = {field_value_map['offerId']}")
    elif is_uuid_like(raw):
        field_value_map["offerUuid"] = raw
        print(f" offerUuid (UUID) = {field_value_map['offerUuid']}")
    else:
        field_value_map["offerCode"] = raw
        print(f" offerCode = {field_value_map['offerCode']}")

    # Дополнительно сохраняем полезные поля
    field_value_map["offerProductCode"] = found.get("offerProductCode")
    field_value_map["loanOption"] = found.get("loanOption")

    print("✅ Итог по офферу:",
          {k: field_value_map.get(k) for k in ["offerId","offerUuid","offerCode","offerProductCode","loanOption"]})


@when('я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с сохранёнными leadId и offerId')
def step_impl(context):
    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    offer_product_code = field_value_map.get("offerProductCode")
    loan_option = field_value_map.get("loanOption")

    offer_for_req = (
            field_value_map.get("offerId")
            or field_value_map.get("offerUuid")
            or field_value_map.get("offerCode")
    )

    assert lead_id, " leadId не найден"
    assert offer_for_req, " offerId/offerUuid/offerCode не найдены"
    assert offer_product_code, " offerProductCode не найден"
    assert loan_option, " loanOption не найден"

    # --- payload ---
    payload = {
        "leadId": lead_id,
        "offerId": offer_for_req,
        "offerProductCode": offer_product_code,
        "loanOption": loan_option,
        "requiredLoanAmount": 200000
    }
    print("📤 calculate payload:", json.dumps(payload, ensure_ascii=False))

    # --- запрос ---
    response = context.api_client.post_with_auth("/agent-api/v1/customer-offer/calculate", payload)
    context.response = response

    resp = response.json()
    endpoint_response_map["/agent-api/v1/customer-offer/calculate"] = resp
    print("✅ Ответ calculate:", json.dumps(resp, indent=2, ensure_ascii=False))

    customer_offers = resp.get("customerOffers", [])
    assert customer_offers, f"❌ В ответе calculate нет customerOffers: {json.dumps(resp, indent=2, ensure_ascii=False)}"

    # ⚡ Выбираем нужный оффер
    chosen = next(
        (o for o in customer_offers if o.get("product", {}).get("productType") in ["CEL", "REFIN_CREDIT"]),
        customer_offers[0]
    )

    code = chosen.get("code")
    assert code, f"❌ У выбранного customerOffer нет поля 'code': {json.dumps(chosen, indent=2, ensure_ascii=False)}"

    field_value_map["customerOfferCode"] = str(code)
    print(f" customerOfferCode={field_value_map['customerOfferCode']}")

    # leadApplicationId
    lead_application_id = chosen.get("leadApplicationId") or lead_id
    field_value_map["leadApplicationId"] = lead_application_id
    print(f" leadApplicationId={lead_application_id}")

    # ---  Если продукт — рефинанс ---
    product_type = (chosen.get("product", {}).get("productType") or "").upper()
    if "REFIN" in product_type:
        print("🔁 Обнаружен продукт типа REFINANCE. Ищем контракт в offer-store...")

        field_value_map["isRefinance"] = True
        field_value_map["offerProductType"] = product_type
        field_value_map["loanOption"] = "REFINANCE"

        #  ищем последнее сохранённое обращение к offer-store
        offer_keys = [k for k in endpoint_response_map.keys() if k.startswith("/agent-api/v1/offer-store/offers")]
        assert offer_keys, " Нет ответа offer-store — нужно выполнить GET перед этим шагом"
        offer_keys.sort()
        offer_store_resp = endpoint_response_map[offer_keys[-1]]

        refinance_contracts = offer_store_resp.get("refinanceContracts", [])
        assert refinance_contracts, " В ответе offer-store нет refinanceContracts"

        valid_contracts = []
        for c in refinance_contracts:
            if not c:
                continue
            amount_raw = c.get("amount")
            try:
                amount = float(amount_raw)
            except Exception:
                try:
                    amount = float(str(amount_raw).replace(",", "."))
                except Exception:
                    continue
            if 10000 < amount < 4_900_000:
                valid_contracts.append({
                    "applicationCode": str(c.get("applicationCode")),
                    "amount": amount,
                    "internal": c.get("internal", True),
                    "bankName": c.get("bankName"),
                    "branchCode": c.get("branchCode"),
                })

        assert valid_contracts, " Не найден контракт с amount < 4_900_000 в ответе offer-store"

        chosen_contract = min(valid_contracts, key=lambda x: x["amount"])
        app_code = chosen_contract["applicationCode"]
        amount = chosen_contract["amount"]

        field_value_map["refinancingContracts"] = [
            {
                "applicationCode": app_code,
                "amount": amount,
                "internal": True,
                "accountNumber": None,
                "bankCode": None,
                "bankBranchCode": chosen_contract.get("branchCode"),
                "bankName": chosen_contract.get("bankName"),
            }
        ]

        field_value_map["contractNumber"] = app_code
        field_value_map["contractAmount"] = amount

        print(f"💾 Выбран контракт: applicationCode={app_code}, amount={amount}")
        print("📦 refinancingContracts добавлен:")
        print(json.dumps(field_value_map["refinancingContracts"], indent=2, ensure_ascii=False))
    else:
        print(f"💰 Продукт не рефинанс (тип={product_type})")



@when('я отправляю POST запрос на "/agent-api/v1/files/send-img-to-auth" с 3 фото')
def step_impl(context):
    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    assert lead_id, " leadId не найден в field_value_map"

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
        print(" Ответ:")
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

    raw_offer_id = field_value_map.get("offerId")
    raw_uuid = field_value_map.get("offerUuid")
    offer_code = field_value_map.get("offerCode")
    calc_code = field_value_map.get("customerOfferCode")  # 👉 код из calculate
    sales_room_code = field_value_map.get("salesRoomCode")
    customer_offer_code = field_value_map.get("customerOfferCode")
    assert customer_offer_code, "❌ customerOfferCode не найден (его вернул calculate)"

    # --- Базовый payload ---
    payload = {
        "leadApplicationId": lead_application_id,
        "creditAmount": 200000,
        "downPayment": 0,
        "loanOption": "CASH_LOAN",
        "offerProductCode": field_value_map.get("offerProductCode"),
        "offerProductType": field_value_map.get("offerProductType", "CEL"),
        "actualAmount": None,
        "creditType": None,
        "incomeAmount": None,
        "incomeAmountTypeCode": None,
        "instantCardType": None,
        "namePartner": None,
        "offerRelipCode": None,
        "paymentServiceCode": None,
        "saleRoomCode": None,
        "saleRoomName": str(sales_room_code),
        "offerId": str(customer_offer_code)
    }

    # --- Дополнительные офферные поля ---
    if calc_code is not None:
        payload["customerOfferCode"] = str(calc_code)
    if isinstance(raw_offer_id, int):
        payload["offerId"] = raw_offer_id
    elif isinstance(raw_offer_id, str) and raw_offer_id.isdigit():
        payload["offerId"] = int(raw_offer_id)
    elif raw_uuid:
        payload["offerUuid"] = raw_uuid
    elif offer_code and "customerOfferCode" not in payload:
        payload["customerOfferCode"] = str(offer_code)

    # 🔴 Проверяем — рефинанс ли это
    loan_option = str(payload.get("loanOption") or field_value_map.get("loanOption") or "").upper()
    product_type = str(payload.get("offerProductType") or field_value_map.get("offerProductType") or "").upper()
    offer_code = str(field_value_map.get("offerProductCode") or "").upper()

    is_refinance = (
            "REFIN" in product_type or
            offer_code == "REF" or
            field_value_map.get("isRefinance") is True
    )

    # --- Если рефинанс, достаём контракт из offer-store ---
    if is_refinance:
        print("🔁 Тип продукта: REFINANCE — ищем контракт в ответе offer-store")
        payload["loanOption"] = field_value_map.get("loanOption", "REFINANCE")
        payload["offerProductType"] = field_value_map.get("offerProductType", "REFIN_CREDIT")

        offer_keys = [k for k in endpoint_response_map.keys() if k.startswith("/agent-api/v1/offer-store/offers")]
        assert offer_keys, "❌ Нет ответа offer-store — нужно выполнить GET перед этим шагом"
        offer_keys.sort()
        offer_store_resp = endpoint_response_map[offer_keys[-1]]

        refinance_contracts = offer_store_resp.get("refinanceContracts", [])
        assert refinance_contracts, "❌ В ответе offer-store нет refinanceContracts"

        valid_contracts = []
        for c in refinance_contracts:
            if not c:
                continue
            amount_raw = c.get("amount")
            try:
                amount = float(amount_raw)
            except Exception:
                try:
                    amount = float(str(amount_raw).replace(",", "."))
                except Exception:
                    continue
            if 10000 < amount < 4_900_000:
                valid_contracts.append({
                    "contractNumber": str(c.get("applicationCode")),
                    "contractAmount": amount,
                    "internal": c.get("internal", True),
                    "bankName": c.get("bankName"),
                    "bankBranchCode": c.get("branchCode"),
                    "accountNumber": None,
                    "bankCode": None
                })

        assert valid_contracts, "❌ Не найден контракт с amount < 4_900_000 в ответе offer-store"

        chosen = min(valid_contracts, key=lambda x: x["contractAmount"])
        payload["refinancingContracts"] = field_value_map.get("refinancingContracts") or [chosen]

        field_value_map["isRefinance"] = True
        field_value_map["contractNumber"] = chosen["contractNumber"]
        field_value_map["contractAmount"] = chosen["contractAmount"]
        field_value_map["refinancingContracts"] = payload["refinancingContracts"]

        print(f"💾 Выбран контракт: {chosen['contractNumber']} сумма={chosen['contractAmount']}")
        print("📦 refinancingContracts добавлен в payload:")
        print(json.dumps(payload["refinancingContracts"], indent=2, ensure_ascii=False))
    else:
        print(f"💰 Тип продукта: {product_type or 'CASH_LOAN'} — без блока refinancingContracts")

    response = context.api_client.post_with_auth("/agent-api/v1/application-management/update", payload)
    context.response = response
    endpoint_response_map["/agent-api/v1/application-management/update"] = response.json()



@when('я отправляю POST запрос на "/agent-api/v2/lead-management/update" с id')
def step_impl(context):
    import base64, json, os

    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"

    def file_to_base64(path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"📁 Файл не найден: {path}")
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    # 🟢 Базовый payload
    payload = {
        "id": lead_id,
        "lastName": None,
        "lastNameLat": None,
        "firstName": None,
        "loanOption": "CASH_LOAN",
        "firstNameLat": None,
        "middleName": None,
        "nin": None,
        "phoneNumber": None,
        "salesRoomCode": None,
        "iban": None,
        "productCode": None,
        "langCode": "RUS",
        "bankBranch": None,
        "statusId": None,
        "contacts": [
            {
                "id": None,
                "phoneNumber": "7776532332",
                "lastName": "Вывффвфыв",
                "firstName": "Ввыфвыф",
                "middleName": None,
                "type": "Brat-Sestra",
                "dictId": None,
                "leadId": None
            }
        ],
        "refinancingContracts": None,
        "securityQuestion": 3211,
        "securityQuestionID": 144,
        "codeDisbursementChannel": None,
        "leadPensionersID": None,
        "leadFilesDTOS": None
    }

    # 🟡 Если нет JSON-текста во feature, автоприкрепляем фото
    if not context.text:
        payload["leadFilesDTOS"] = [
            {"type": "id_card_front", "data": file_to_base64("features/resources/id_card_front.jpg"), "fileId": None},
            {"type": "id_card_back", "data": file_to_base64("features/resources/id_card_back.jpg"), "fileId": None},
            {"type": "selfie", "data": file_to_base64("features/resources/selfie.jpg"), "fileId": None}
        ]
    else:
        extra = json.loads(context.text)
        payload.update(extra)

    # 🟣 Если рефинанс — добавляем refinancingContracts
    if field_value_map.get("isRefinance"):
        payload["refinancingContracts"] = field_value_map.get("refinancingContracts")
        payload["loanOption"] = field_value_map.get("loanOption", "REFINANCE")
        print("🔁 Добавлен блок refinancingContracts из field_value_map")

    # 🚀 Отправляем запрос
    print("📤 Тело запроса к /agent-api/v2/lead-management/update:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    response = context.api_client.post_with_auth("/agent-api/v2/lead-management/update", payload)
    context.response = response

    # 💬 Логируем ответ
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




@when('я отправляю POST запрос на "/agent-api/v2/lead-management/update" с id и фото')
def step_impl(context):
    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"

    def file_to_base64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    contacts_payload = [
        {
            "id": None,
            "phoneNumber": "7776532332",
            "lastName": "Вывффвфыв",
            "firstName": "Ввыфвыф",
            "middleName": None,
            "type": "Brat-Sestra",
            "dictId": None,
            "leadId": None
        }
    ]

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
        "contacts": contacts_payload,
        "refinancingContracts": None,
        "securityQuestion": 3211,
        "securityQuestionID": 144,
        "geolocation": None,
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

    if field_value_map.get("isRefinance"):
        payload["refinancingContracts"] = field_value_map.get("refinancingContracts")
        payload["loanOption"] = field_value_map.get("loanOption", "REFINANCE")
        print("🔁 Добавлен блок refinancingContracts из field_value_map")

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


@when('Ожидаю когда поле "leadDTO.stateFeature.id" и статус "135"')
def step_impl(context):
    lead_id = field_value_map.get("id")

    endpoint = f"/agent-api/v1/lead-management/get-details/{lead_id}"
    max_attempts = 30
    interval = 5

    for attempt in range(1, max_attempts + 1):
        response = context.api_client.get_with_auth(endpoint)
        try:
            json_body = response.json()
            state_feature_id = json_body["leadDTO"]["stateFeature"]["id"]

            if str(state_feature_id) == "135":
                print(f"✅ Попытка {attempt}: stateFeature.id = 135")
                return
            else:
                print(f"⏳ Попытка {attempt}: stateFeature.id = {state_feature_id}, ожидаем 135")

        except Exception as e:
            print(f"⚠️ Ошибка при обработке ответа: {e}")
            print("📦 Ответ:", response.text)

        if attempt < max_attempts:
            time.sleep(interval)


@when('Ожидаю когда поле "leadDTO.stateFeature.id" и статус "61"')
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

            if str(state_feature_id) == "61":
                print(f"✅ Попытка {attempt}: stateFeature.id = 61")
                return
            else:
                print(f"⏳ Попытка {attempt}: stateFeature.id = {state_feature_id}, ожидаем 61")

        except Exception as e:
            print(f"⚠️ Ошибка при обработке ответа: {e}")
            print("📦 Ответ:", response.text)

        if attempt < max_attempts:
            time.sleep(interval)


@when('я отправляю POST запрос на "/agent-api/v1/card-controller/disbursement-channel" с leadId и iban')
def step_impl(context):
    lead_id = field_value_map.get("id") or field_value_map.get("leadId")
    assert lead_id, "❌ leadId не найден в field_value_map"

    payload = {
        "leadId": lead_id,
        "iban": "kz",   # можно брать из field_value_map
        "codeDisbursementChannel": "DEBIT_CARD",
        "bankBranch": None
    }

    print("📤 disbursement payload:", json.dumps(payload, indent=2, ensure_ascii=False))

    response = context.api_client.post_with_auth(
        "/agent-api/v1/card-controller/disbursement-channel",
        payload
    )
    context.response = response

    try:
        resp = response.json()
        print("✅ Ответ disbursement:", json.dumps(resp, indent=2, ensure_ascii=False))
        endpoint_response_map["/agent-api/v1/card-controller/disbursement-channel"] = resp
    except Exception as e:
        print(f"❌ Ошибка парсинга disbursement: {e}")
        print("📦 raw:", response.text)
        endpoint_response_map["/agent-api/v1/card-controller/disbursement-channel"] = None
        raise


@when('Ожидаю когда поле "leadDTO.stateFeature.id" и статус "243"')
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

            if str(state_feature_id) == "243":
                print(f"✅ Попытка {attempt}: stateFeature.id = 243")
                return
            else:
                print(f"⏳ Попытка {attempt}: stateFeature.id = {state_feature_id}, ожидаем 243")

        except Exception as e:
            print(f"⚠️ Ошибка при обработке ответа: {e}")
            print("📦 Ответ:", response.text)

        if attempt < max_attempts:
            time.sleep(interval)


@when('я отправляю POST запрос на "/agent-api/v1/eds/create-sign/SIGN_CONTRACT" с фото')
def step_impl(context):
    lead_id = field_value_map.get("id") or field_value_map.get("leadApplicationId")
    assert lead_id, "❌ leadId не найден в field_value_map"

    def file_to_base64(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "fileId": None,
        "type": "selfie",
        "data": file_to_base64("features/resources/selfie.jpg")
    }

    endpoint = f"/agent-api/v1/eds/create-sign/{lead_id}/SIGN_CONTRACT"
    print("📤 Тело запроса к create-sign:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    response = context.api_client.post_with_auth(endpoint, payload)
    context.response = response

    try:
        resp_json = response.json()
        print("✅ Ответ create-sign:", json.dumps(resp_json, indent=2, ensure_ascii=False))
        endpoint_response_map[endpoint] = resp_json
    except Exception as e:
        print(f"❌ Ошибка при разборе ответа: {e}")
        print("📦 raw:", response.text)
        endpoint_response_map[endpoint] = None
        raise


@when('Ожидаю когда поле "leadDTO.stateFeature.id" и статус "63"')
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

            if str(state_feature_id) == "63":
                print(f"✅ Попытка {attempt}: stateFeature.id = 63")
                return
            else:
                print(f"⏳ Попытка {attempt}: stateFeature.id = {state_feature_id}, ожидаем 63")

        except Exception as e:
            print(f"⚠️ Ошибка при обработке ответа: {e}")
            print("📦 Ответ:", response.text)

        if attempt < max_attempts:
            time.sleep(interval)

