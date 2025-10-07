Feature: Отправка на 1 блок данных

  Scenario: Отправка расчёта предложения с типом "[CEL][Cash Xsell][Real]"

    When я отправляю GET запрос "/agent-api/v2/lead-management/create" с токеном
    Then беру из ответа "/agent-api/v2/lead-management/create" поле "id"
    When я отправляю GET запрос на "/agent-api/v2/lead-data-controller/doc/{{{id}}}" с токеном
    Then статус ответа 200


    When я отправляю GET запрос на "/agent-api/v1/offer-store/offers/{{{id}}}" с токеном
    Then я извлекаю offerId с типом "[CEL][Cash Xsell][Real]" из ответа


    When я отправляю POST запрос на "/agent-api/v1/application-management/update" с leadApplicationId
    Then статус ответа 200


     When я отправляю POST запрос на "/agent-api/v2/lead-management/update" с id и фото
     """
      {
        "leadFilesDTOS": []
      }
      """

    Then статус ответа 200
