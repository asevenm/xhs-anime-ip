import os
import json
import time
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()

# Configure Gemini API
GENAI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GENAI_API_KEY:
    print("Warning: GEMINI_API_KEY not found in environment variables.")

# Initialize client
client = genai.Client(api_key=GENAI_API_KEY)

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def generate_image(prompt, output_path, index):
    """
    Calls the Google Gemini API for image generation and saves the result.
    Uses gemini-2.5-flash-image model.
    """
    print(f"Generating image {index}...")
    
    # Simulation Mode (if no key provided)
    if not GENAI_API_KEY:
        print(f"SIMULATION: Mocking generation for '{prompt[:30]}...' -> {output_path}")
        from PIL import ImageDraw
        img = Image.new('RGB', (1024, 1280), color=(73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((100, 100), f"Image {index}\n{prompt[:50]}...", fill=(255, 255, 0))
        img.save(output_path)
        time.sleep(1)
        return

    try:
        # Use Gemini 2.5 Flash Image model
        response = client.models.generate_content(
            model="gemini-3-pro-image-preview",
            contents=prompt,
        )
        
        # Extract and save the generated image
        image_saved = False
        for part in response.parts:
            if part.inline_data:
                image = part.as_image()
                image.save(output_path)
                print(f"Saved: {output_path}")
                image_saved = True
                break
        
        if not image_saved:
            print(f"No image generated for prompt {index}")
            raise Exception("No image returned from API")
                
    except Exception as e:
        print(f"Error generating image {index}: {e}")
        raise e

def run_painter():
    # Find the latest content folder
    if not os.path.exists("content"):
        print("No content directory found. Run planner.py first.")
        return

    dates = sorted(os.listdir("content"))
    if not dates:
        print("No dated folders found.")
        return
        
    latest_date = dates[-1]
    work_dir = os.path.join("content", latest_date)
    meta_path = os.path.join(work_dir, "meta.json")
    
    if not os.path.exists(meta_path):
        print(f"No meta.json found in {work_dir}")
        return
        
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    prompts = data.get("image_prompts", [])
    
    print(f"Found {len(prompts)} prompts to generate")
    print(f"Output directory: {work_dir}")
    print("-" * 50)
    
    for i, prompt in enumerate(prompts):
        output_filename = f"{i+1}.png"
        output_path = os.path.join(work_dir, output_filename)
        
        if os.path.exists(output_path):
            print(f"Image {output_filename} already exists. Skipping.")
            continue
        
        print(f"\nPrompt {i+1}: {prompt[:80]}...")
        generate_image(prompt, output_path, i+1)
        
        # Rate limiting - avoid hitting API limits
        if i < len(prompts) - 1:
            print("Waiting 2 seconds before next generation...")
            time.sleep(2)
    
    print("\n" + "=" * 50)
    print("Image generation complete!")

if __name__ == "__main__":
    run_painter()
