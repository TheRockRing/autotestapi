Feature: Отправка на 1 блок данных

  Scenario: Отправка расчёта предложения с типом "[CEL][Cash Xsell][Real]"

    When я отправляю GET запрос на "/agent-api/v2/lead-data-controller/doc/{{{id}}}" с токеном
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v1/offer-store/offers/{{{id}}}" с токеном
    Then я извлекаю offerId с типом "[CEL][Cash Xsell][Real]" из ответа


    When я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с сохранёнными leadId и offerId
    Then статус ответа 200

