Feature: Создание лида Refinance

  Scenario: Получение токена и создание лида
    When отправляю запрос на получение токена
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v1/otp/generate-save/7777777777/RUS/PERSONALIZED_CONSENT?phone=777777777&product=HCA_LEAD" с токеном
    Then беру из ответа "/agent-api/v1/otp/generate-save/777777777777/RUS/PERSONALIZED_CONSENT?phone=777777777&product=HCA_LEAD" поле "key"
    When я отправляю POST запрос на "/agent-api/v1/otp/validate-save" и токеном
    """json
    {
        "code": "1111",
        "key": "{{{key}}}"
    }
    """
    Then статус ответа 200
    When я отправляю POST запрос на "/agent-api/v2/lead-management/create" и токеном
    """json
    {
      "lastName": "777777777",
      "firstName": "7777777777",
      "middleName": "",
      "phoneNumber": "7777777777",
      "nin": "7777777777",
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
    Then поле "leadDTO.nin" равен "777777777777"
    Then Ожидаю когда поле "leadDTO.stateFeature.id" и статус "165" или "5"
