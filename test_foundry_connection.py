import os

from ai_assistant_app_sdk import FoundryClient, UserTokenAuth

auth = UserTokenAuth(token=os.environ["FOUNDRY_TOKEN"])

client = FoundryClient(auth=auth, hostname="https://magic.usw-3.palantirfoundry.com")

test_call = client.ontology.queries.empty_aip_logic(
    prompt='return only the word "hello"'
)
print(test_call)
