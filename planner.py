import os
import json
import datetime
from typing import List
from pydantic import BaseModel, Field
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables.")

try:
    genai.configure(api_key=GENAI_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini: {e}")

class DailyContent(BaseModel):
    date: str = Field(description="Date of the post in YYYY-MM-DD format")
    theme: str = Field(description="The central theme of the 6 images (e.g., 'Summer Rain', 'Train Station at Dusk')")
    title: str = Field(description="Catchy Xiaohongshu title (include emojis)")
    content: str = Field(description="Engaging body text for the post, emotional and atmospheric")
    tags: List[str] = Field(description="List of hashtags (e.g., #Ghibli #Anime #Wallpaper)")
    image_prompts: List[str] = Field(description="List of 6 distinct but thematically consistent image prompts for the AI")

def generate_daily_plan(model_name="gemini-2.0-flash-exp"):
    """
    Generates the daily content plan using Gemini.
    """
    model = genai.GenerativeModel(model_name)
    
    today = datetime.date.today().strftime("%Y-%m-%d")
    
    prompt = f"""
    You are the creative director for a popular Xiaohongshu (Little Red Book) account.
    Our niche is "Classic Anime Aesthetics" (think Studio Ghibli, Makoto Shinkai, 90s anime nostalgia).
    
    Task: Plan content for today ({today}).
    1. Choose a nostalgic or atmospheric theme.
    2. Write a catchy title and emotional caption suitable for Xiaohongshu users.
    3. Generate 6 detailed image prompts for an AI image generator. The prompts should specify:
       - Style: Studio Ghibli art style, cel shaded, highly detailed, vibrant colors, anime scenery.
       - Content: Scenic views, cozy rooms, or solitary characters (back view), consistent with the theme.
       - Aspect Ratio instructions are not needed here, just the visual description.
    
    Output JSON complying with the DailyContent schema.
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=DailyContent
            )
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generating content: {e}")
        return None

if __name__ == "__main__":
    plan = generate_daily_plan()
    if plan:
        # Create directory for today
        date_dir = os.path.join("content", plan['date'])
        os.makedirs(date_dir, exist_ok=True)
        
        # Save metadata
        with open(os.path.join(date_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
            
        print(f"Plan generated for {plan['date']}")
        print(f"Title: {plan['title']}")
        print(f"Theme: {plan['theme']}")
    else:
        print("Failed to generate plan.")
