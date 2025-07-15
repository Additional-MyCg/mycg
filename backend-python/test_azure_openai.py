# test_azure_openai.py
from openai import AzureOpenAI
from config.settings import settings

print("Testing Azure OpenAI connection...")

ai_config = settings.get_ai_config()
print(f"Endpoint: {ai_config.get('azure_openai_endpoint')}")
print(f"Deployment: {ai_config.get('azure_openai_deployment_name')}")
print(f"Using Azure: {ai_config.get('use_azure_openai')}")

if ai_config.get('use_azure_openai') and ai_config.get('azure_openai_api_key'):
    try:
        client = AzureOpenAI(
            api_key=ai_config["azure_openai_api_key"],
            api_version=ai_config["azure_openai_api_version"],
            azure_endpoint=ai_config["azure_openai_endpoint"]
        )
        
        response = client.chat.completions.create(
            model=ai_config["azure_openai_deployment_name"],
            messages=[
                {"role": "user", "content": "What is GST and what model are you?"}
            ],
            max_tokens=100
        )
        
        print(f"\n✅ Success! Azure OpenAI is working.")
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
else:
    print("\n❌ Azure OpenAI not configured properly. Check your .env file.")