Feature: Отправка на 1 блок данных

  Scenario: Отправка расчёта предложения с типом "[CEL][Cash Xsell][Real]"

    When я отправляю GET запрос на "/agent-api/v2/lead-data-controller/doc/692400" с токеном
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v1/offer-store/offers/6092400" с токеном
    Then я извлекаю offerId с типом "[CEL][Cash Xsell][Real]" из ответа "/agent-api/v1/offer-store/offers/6092400"

    When я отправляю POST запрос на "/agent-api/v1/customer-offer/calculate" с сохранёнными leadId и offerId
    Then статус ответа 200

