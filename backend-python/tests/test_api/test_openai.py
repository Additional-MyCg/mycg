# test_openai.py
from openai import OpenAI
from config.settings import settings

# Get AI config
ai_config = settings.get_ai_config()
print(f"OpenAI API Key configured: {'Yes' if ai_config['openai_api_key'] else 'No'}")
print(f"Model: {ai_config['default_model']}")

try:
    # Initialize client
    client = OpenAI(api_key=ai_config['openai_api_key'])
    
    # Test API call
    response = client.chat.completions.create(
        model=ai_config['default_model'],
        messages=[
            {"role": "user", "content": "Hello, test message"}
        ],
        max_tokens=50
    )
    
    print(f"Success! Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")