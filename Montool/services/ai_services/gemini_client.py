# gemini_client.py
import google.generativeai as genai
from services.config import API_KEY

# Configure the API client
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash') # Using the fast and efficient model

def get_gemini_response(prompt: str, memories: list[str] = None) -> str:
    """
    Sends a prompt to the Gemini API, including past memories for context using a more explicit system prompt.
    """
    if not API_KEY or "YOUR_API_KEY" in API_KEY:
        return "Lỗi: API Key chưa được cấu hình. Vui lòng kiểm tra file config.py."

    # --- NEW: Improved System Prompt ---
    final_prompt = ""
    if memories:
        # Create a clearer context block for the AI
        memory_context = "\n".join(f"- {mem}" for mem in memories)
        # This explicit instruction format works more reliably
        final_prompt = (
            f"Bạn là một trợ lý AI hữu ích. Đây là những thông tin quan trọng bạn cần phải ghi nhớ để trả lời người dùng:\n"
            f"{memory_context}\n"
            f"--- (kết thúc phần ghi nhớ) ---\n\n"
            f"Bây giờ, hãy trả lời câu hỏi của người dùng một cách tự nhiên: {prompt}"
        )
    else:
        final_prompt = prompt

    try:
        response = model.generate_content(final_prompt)
        if response.parts:
            return response.text
        else:
            return "AI không có phản hồi cho yêu cầu này. Vui lòng thử lại."
            
    except Exception as e:
        print(f"An error occurred with the Gemini API: {e}")
        return f"Đã xảy ra lỗi khi kết nối đến AI. Lỗi: {e}" 