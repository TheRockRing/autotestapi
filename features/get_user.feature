Feature: Получение данных агента по ИИН

  Scenario: Получение данных агента по ИИН
    When я отправляю GET запрос на "/agent-api/v1/open/users/user/777777777"
    Then статус ответа 200
    And поле "user.firstName" равен "Проверка"








