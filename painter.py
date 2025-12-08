import os
import json
import requests
import time
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv

load_dotenv()

# Configuration for "Nano Banana" (Placeholder for the actual API)
# User needs to set these in .env
IMAGE_API_URL = os.getenv("IMAGE_API_URL", "https://api.nano-banana.example.com/generate") # Replace with actual
IMAGE_API_KEY = os.getenv("IMAGE_API_KEY")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def generate_image(prompt, output_path, index):
    """
    Calls the Image Generation API and saves the result.
    This is a generic implementation. Update the payload structure based on the specific provider.
    """
    print(f"Generating image {index}...")
    
    # Example Payload - Adjust based on actual API requirements
    payload = {
        "prompt": prompt + ", studio ghibli style, anime background, 4k, detailed",
        "negative_prompt": "low quality, text, watermark, ugly, deformed",
        "width": 1024,
        "height": 1280, # 4:5 ratio best for Xiaohongshu
        "steps": 25
    }
    
    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Content-Type": "application/json"
    }

    # Simulation Mode (if no key provided)
    if not IMAGE_API_KEY or "example.com" in IMAGE_API_URL:
        print(f"SIMULATION: Mocking generation for '{prompt[:30]}...' -> {output_path}")
        # Create a dummy placeholder image
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (1024, 1280), color = (73, 109, 137))
        d = ImageDraw.Draw(img)
        d.text((100,100), f"Image {index}\n{prompt[:50]}...", fill=(255,255,0))
        img.save(output_path)
        time.sleep(1) # Simulate delay
        return

    try:
        response = requests.post(IMAGE_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        
        # Assuming response returns binary image data or a URL
        # Case A: JSON with URL
        if "url" in response.json():
            image_url = response.json()["url"]
            img_data = requests.get(image_url).content
            with open(output_path, 'wb') as f:
                f.write(img_data)
        # Case B: Direct Binary
        else:
             with open(output_path, 'wb') as f:
                f.write(response.content)
                
        print(f"Saved: {output_path}")
        
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
    
    for i, prompt in enumerate(prompts):
        output_filename = f"{i+1}.png"
        output_path = os.path.join(work_dir, output_filename)
        
        if os.path.exists(output_path):
            print(f"Image {output_filename} already exists. Skipping.")
            continue
            
        generate_image(prompt, output_path, i+1)

if __name__ == "__main__":
    run_painter()
