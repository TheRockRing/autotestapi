from utils.api_client import ApiClient
from utils.teams_notifier import notify_lead_failure


def before_all(context):
    context.api_client = ApiClient(base_url="https:/")
    #context.api_client = ApiClient(base_url="http://localhost:8080")


def before_scenario(context, scenario):
    context.teams_notified = False
    context.lead_id = None


def after_scenario(context, scenario):
    # Уведомление об ошибке, если упали до статуса 165 (OTP, create и т.д.)
    if getattr(scenario.status, "name", str(scenario.status)) != "failed":
        return
    if getattr(context, "teams_notified", False):
        return

    name = (getattr(scenario, "filename", None) or "").replace("\\", "/").lower()
    if "lead_create" not in name:
        return

    lead_id = getattr(context, "lead_id", None)
    reason = f"Сценарий '{scenario.name}' завершился с ошибкой"
    notify_lead_failure(lead_id=lead_id, reason=reason)
    context.teams_notified = True
