# ai_controller.py
import json

def process_ai_command(prompt: str):
    """
    Analyzes the user's prompt to determine if it's a command for the tool
    or a regular chat message.
    """
    prompt_lower = prompt.lower().strip()
    
    # Command: "hãy nhớ", "ghi nhớ"
    memory_keywords = ["nhớ rằng", "nhớ", "hãy nhớ rằng", "hãy nhớ", "ghi nhớ rằng", "ghi nhớ"]
    for keyword in memory_keywords:
        if prompt_lower.startswith(keyword):
            # Extract the content after the keyword
            content_to_remember = prompt[len(keyword):].strip()
            if content_to_remember:
                return {
                    "tool_name": "add_memory",
                    "parameters": {"text": content_to_remember}
                }

    # Command: "xóa bộ nhớ", "quên hết đi"
    clear_keywords = ["xóa bộ nhớ", "quên hết đi", "xóa hết bộ nhớ"]
    if prompt_lower in clear_keywords:
        return {"tool_name": "clear_memory", "parameters": {}}

    # If no command is detected, return None
    return None 