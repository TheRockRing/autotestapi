from utils.api_client import ApiClient

def before_all(context):
    context.api_client = ApiClient(base_url="https://dev-agent.homecredit.kz")
    #context.api_client = ApiClient(base_url="http://localhost:8080")


