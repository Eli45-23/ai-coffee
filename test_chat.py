import os
from dotenv import load_dotenv
import openai

# Load your key from the .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_menu_bot(question: str) -> str:
    # Ask the AI Coffee bot any menu question.
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # or "gpt-3.5-turbo"
        messages=[
            {
                "role": "system",
                "content": (
                    "You are AI Coffee, a friendly coffee-menu chatbot. "
                    "Answer customer questions about our drinks, roasts, and specials."
                )
            },
            {"role": "user", "content": question}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

def make_instagram_posts(specials):
    # Generate 3 Instagram post captions based on this week's menu specials.
    prompt = (
        "You are AI Coffee, a social-media expert writing Instagram captions. "
        "Our weekly specials are: " + ", ".join(specials) + ". "
        "Write 3 engaging Instagram posts, each with a fun caption under 150 characters."
    )
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You write Instagram captions for a coffee shop."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
    )
    text = response.choices[0].message.content.strip()
    return [line.strip() for line in text.splitlines() if line.strip()]

if __name__ == "__main__":
    # Test the menu bot with an ASCII-only question
    answer = ask_menu_bot("What's in your cold brew?")
    print("AI Coffee says:", answer)

    # Test the Instagram post generator
    print("\nSample IG posts:")
    for post in make_instagram_posts([
        "Honey Lavender Latte",
        "Vanilla Cold Brew",
        "Pumpkin Spice Cappuccino"
    ]):
        print("-", post)
