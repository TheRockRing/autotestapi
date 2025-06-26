Feature: Проверка получения клиента по ИИН

  Scenario: Получить клиента по ИИН
    When я отправляю GET запрос на "/agent-api/v1/open/users/user/980516301284"
    Then статус ответа 200
    And поле "user.firstName" равен "үуГДёкЖ"








