import requests
import traceback

def chat():
    """
    Simple interactive chat with Ollama via HTTP.
    You can see errors printed in the terminal.
    """
    model = "qwen3:hello8B"
    url = "http://127.0.0.1:11434/v1/chat/completions"
    print(f"Using Ollama model: {model}")
    print("Enter your message (or type 'quit' to exit):")
    
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\\nExiting.")
            break
        if user_input.lower() in ["quit", "exit"]:
            print("Goodbye.")
            break
        if not user_input:
            continue
        
        try:
            resp = requests.post(
                url,
                json={
                    "model": model,
                    "messages": [
                        { "role": "system", "content": "You are a helpful assistant." },
                        { "role": "user",   "content": user_input }
                    ]
                },
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            assistant_msg = data["choices"][0]["message"]["content"]
            print("Assistant:", assistant_msg)
        except Exception as e:
            print("Error occurred:", str(e))
            traceback.print_exc()

if __name__ == "__main__":
    chat()