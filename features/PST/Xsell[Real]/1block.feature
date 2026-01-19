Feature: 1 блок одобрено
  Scenario: Отправка на 2-блок данных
    When Ожидаю когда поле "leadDTO.stateFeature.id" и статус "135"

    When я отправляю POST запрос на "/agent-api/v2/lead-management/update" с id
    Then статус ответа 200



