from dotenv import load_dotenv
from pathlib import Path
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI

# Explicitly find and load the .env from C:\Machine Learning\Projects\RAG\.env
env_path = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=env_path)


def main():
    grok_model = ChatGroq(model="openai/gpt-oss-120b", temperature=0.3)

    gemini_model = ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0.3)

    grok_response = grok_model.invoke(
        "What are three key benefits of using a local RAG pipeline?"
    )
    print("Grok-Answer: ", grok_response.content)

    gemini_response = gemini_model.invoke(
        "What are three key benefits of using a local RAG pipeline?"
    )
    print("=" * 60)
    print("Gemini response:", gemini_response.content)


if __name__ == "__main__":
    main()
