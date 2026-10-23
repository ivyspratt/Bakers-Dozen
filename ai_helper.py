from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()

def get_search_query(ingredients):
    reply = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=(
            "Turn this list of ingredients into a short web search query "
            "for finding recipes. Reply with only the query, nothing else. "
            "Ingredients: " + ingredients
        ),
    )
    return reply.text

if __name__ == "__main__":
    print(get_search_query("chicken, rice, broccoli"))