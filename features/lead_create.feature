Feature: Создание лида

#Scenario: Отправка сообщения PERSONALIZED_CONSENT для создания лида
#When я отправляю GET запрос на "/agent-api/v1/otp/generate-save/980811350404/RUS/PERSONALIZED_CONSENT?phone=7074575944&product=HCA_LEAD" с токеном
#Then беру из ответа "/agent-api/v1/otp/generate-save/980811350404/RUS/PERSONALIZED_CONSENT?phone=7074575944&product=HCA_LEAD" поле "key"
#When я отправляю POST запрос на "/agent-api/v1/otp/validate-save" и токеном
#"""json
#    {
#        "code": "1111",
#        "key": "{{{key}}}"
#    }
#    """
#Then статус ответа 200
#When я отправляю POST запрос на "/agent-api/v2/lead-management/create" и токеном
#"""json
#    {
#      "lastName": "Солтаев",
#      "firstName": "Адильджон",
#      "middleName": "",
#      "phoneNumber": "7074575944",
#      "nin": "980811350404",
#      "productCode": "HCA_LEAD",
#      "internalFraudType": "0",
#      "langCode": "KAZ",
#      "cart": null,
#      "isManualIin": false
#    }
#    """
#Then статус ответа 200
#Then беру из ответа "/agent-api/v2/lead-management/create" поле "id"
#When я отправляю GET запрос на "/agent-api/v1/lead-management/get-details/{{{id}}}" с токеном
#Then поле "leadDTO.stateFeature.id" равен "3"
#Then поле "leadDTO.nin" равен "980811350404"

