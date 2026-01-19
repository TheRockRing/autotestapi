Feature: 2 блок одобрено
  Scenario: Заявка идет на подписание

    When Ожидаю когда поле "leadDTO.stateFeature.id" и статус "61"

    When я отправляю POST запрос на "/agent-api/v1/card-controller/disbursement-channel" с leadId и iban
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v1/application-management/prepareDocument/task/{{{id}}}" с токеном
    Then статус ответа 200

    When я отправляю POST запрос на "/agent-api/v2/lead-management/update" с id
    Then статус ответа 200

    When Ожидаю когда поле "leadDTO.stateFeature.id" и статус "243"
    Then статус ответа 200

    When я отправляю POST запрос на "/agent-api/v1/eds/create-sign/SIGN_CONTRACT" с фото
    Then статус ответа 200

    When я отправляю GET запрос на "/agent-api/v1/eds/certify-sign/{{{id}}}/0000" с токеном
    Then статус ответа 200

    When я отправляю POST запрос на "/agent-api/v2/lead-management/update" с id
    Then статус ответа 200

    When Ожидаю когда поле "leadDTO.stateFeature.id" и статус "63"

    Then статус ответа 200