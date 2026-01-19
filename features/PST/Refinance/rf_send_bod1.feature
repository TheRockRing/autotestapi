Feature: Отправка на 1 блок данных

  Scenario: Отправка расчёта предложения с типом "[CEL][Refinance Xsell][Real]"

    When я отправляю GET запрос на "/agent-api/v1/lead-data-controller/doc/{{{id}}}" с токеном
    Then статус ответа 200


    When я отправляю GET запрос на "/agent-api/v1/offer-store/offers/{{{id}}}" с токеном
    Then я извлекаю offerId с типом "[CEL][Refinance Xsell][Real]" из ответа

    When я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с сохранёнными leadId и offerId
    Then беру из ответа "/agent-api/v2/lead-management/create" поле "id"

    When я отправляю POST запрос на "/agent-api/v1/product-catalog/CEL" и токеном
    """json
    {
        "0" : "XSTNF--FFP" ,
        "1" : "XSTNF--FFP" ,
        "2" : "XSTNF--FFP"
    }
    """



    When я отправляю GET запрос "/agent-api/v2/lead-management/create" с токеном
    Then беру из ответа "/agent-api/v2/lead-management/create" поле "id"

    When я отправляю POST запрос на "/agent-api/v1/files/send-img-to-auth" с 3 фото
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v1/lead-management/get-details/{{{id}}}" с токеном
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v2/lead-data-controller/doc/{{{id}}}" с токеном
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v1/offer-store/offers/{{{id}}}" с токеном
    Then я извлекаю offerId с типом "[CEL][Refinance Xsell][Real]" из ответа

    When я отправляю POST запрос на "/agent-api/v1/application-management/update" с leadApplicationId
    Then статус ответа 200

    When я отправляю POST запрос на "/agent-api/v2/lead-management/update" с id и фото
    Then статус ответа 200
