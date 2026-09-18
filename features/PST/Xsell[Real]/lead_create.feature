Feature: Создание лида

Scenario: Отправка сообщения PERSONALIZED_CONSENT для создания лида
When я отправляю GET запрос на "/agent-api/v1/otp/generate-save/7777777/RUS/PERSONALIZED_CONSENT?phone=7777777&product=HCA_LEAD" с токеном
Then беру из ответа "/agent-api/v1/otp/generate-save/77777777/RUS/PERSONALIZED_CONSENT?phone=7777777&product=HCA_LEAD" поле "key"
Then беру OTP код из БД по телефону "7777777"
When я отправляю POST запрос на "/agent-api/v1/otp/validate-save" и токеном
"""json
    {
        "code": "{{{otp_code}}}",
        "key": "{{{key}}}"
    }
    """
Then статус ответа 200
When я отправляю POST запрос на "/agent-api/v2/lead-management/create" и токеном
"""json
    {
      "lastName": "ТЛЕУБЕРГЕН",
      "firstName": "ТЕМИРЛАН",
      "middleName": "",
      "phoneNumber": "777777777777",
      "nin": "777777777777",
      "productCode": "HCA_LEAD",
      "internalFraudType": "0",
      "langCode": "KAZ",
      "cart": null,
      "isManualIin": false
    }
    """
Then статус ответа 200
Then беру из ответа "/agent-api/v2/lead-management/create" поле "id"
When я отправляю GET запрос на "/agent-api/v1/lead-management/get-details/{{{id}}}" с токеном
Then поле "leadDTO.stateFeature.id" равен "3"
Then поле "leadDTO.nin" равен "7777777777"
Then Ожидаю когда поле "leadDTO.stateFeature.id" и статус "165" или "5"


