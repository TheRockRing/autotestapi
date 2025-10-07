Feature: Создание лида

Scenario: Отправка сообщения PERSONALIZED_CONSENT для создания лида
When я отправляю GET запрос на "/agent-api/v1/otp/generate-save/010531501486/RUS/PERSONALIZED_CONSENT?phone=7074575944&product=HCA_LEAD" с токеном
Then беру из ответа "/agent-api/v1/otp/generate-save/010531501486/RUS/PERSONALIZED_CONSENT?phone=7074575944&product=HCA_LEAD" поле "key"
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
      "lastName": "Тлеуберген",
      "firstName": "Темирлан",
      "middleName": "",
      "phoneNumber": "7074575944",
      "nin": "010531501486",
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
Then поле "leadDTO.nin" равен "010531501486"
Then Ожидаю когда поле "leadDTO.stateFeature.id" и статус "165"


    When я отправляю GET запрос на "/agent-api/v2/lead-data-controller/doc/{{{id}}}" с токеном
    Then статус ответа 200


    When я отправляю GET запрос на "/agent-api/v1/offer-store/offers/{{{id}}}" с токеном
    Then я извлекаю offerId с типом "[CEL][Cash Xsell][Real]" из ответа


    When я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с сохранёнными leadId и offerId
    Then беру из ответа "/agent-api/v2/lead-management/create" поле "id"

    When я отправляю POST запрос на "/agent-api/v1/application-management/update" с leadApplicationId


    When я отправляю POST запрос на "/agent-api/v1/product-catalog/CEL" и токеном
    """json
    {
        "0" : "XSTNF--FFP" ,
        "1" : "XSTNF--FFP" ,
        "2" : "XSTNF--FFP"
    }
    """

    When я отправляю POST запрос на "/agent-api/v1/files/send-img-to-auth" с 3 фото
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v1/lead-management/get-details/{{{id}}}" с токеном