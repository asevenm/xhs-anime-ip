import os
import json
import time
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv
from openai import OpenAI
from google import genai
import requests

load_dotenv()

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def generate_image_google(prompt, output_path):
    """Generate image using Google Gemini (Imagen 3)."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found")
        
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-3-pro-image-preview",
        contents=prompt,
    )
    
    for part in response.parts:
        if part.inline_data:
            part.as_image().save(output_path)
            return
            
    raise Exception("No image returned from Google API")

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def generate_image_openai(prompt, output_path):
    """Generate image using OpenAI Compatible API (DALL-E 3 protocol)."""
    provider = os.getenv("IMAGE_LLM_PROVIDER", "openai").lower()
    api_key = None
    model = None
    
    if provider == "doubao":
        api_key = os.getenv("ARK_API_KEY")
        base_url = 'https://ark.cn-beijing.volces.com/api/v3'
        model = os.getenv("LLM_IMAGE_MODEL", "doubao-seedream-4-5-251128")
    elif provider == "dashscope":
        api_key = os.getenv("DASHSCOPE_API_KEY")
        base_url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        model = os.getenv("LLM_IMAGE_MODEL", "qwen-image-plus")
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        base_url = 'https://generativelanguage.googleapis.com/v1beta/openai/'
        model = os.getenv("LLM_IMAGE_MODEL", "gemini-3-pro-image-preview")
    
    if not api_key:
        raise ValueError("LLM_API_KEY not found")

    client = OpenAI(api_key=api_key, base_url=base_url) 
    
    response = client.images.generate(
        model=model,
        prompt=prompt,
        n=1,
        size="1024x1024", # Standard size, many providers require this
        quality="standard",
    )
    
    image_url = response.data[0].url
    
    # Download image from URL
    img_data = requests.get(image_url).content
    with open(output_path, 'wb') as f:
        f.write(img_data)

def generate_image(prompt, output_path, index):
    print(f"Generating image {index}...")
    
    provider = os.getenv("IMAGE_LLM_PROVIDER", "gemini").lower()
    
    try:
        if provider == "gemini":
            print(f"Using Provider: Gemini (Imagen 3)")
            generate_image_google(prompt, output_path)
        else:
            # Default to OpenAI Compatible for all other providers
            print(f"Using Provider: OpenAI Compatible ({os.getenv('LLM_BASE_URL')})")
            generate_image_openai(prompt, output_path)
            
        print(f"✅ Saved: {output_path}")
        
    except Exception as e:
        print(f"❌ Error generating image {index}: {e}")
        # Placeholder on failure (optional)
        # from PIL import Image, ImageDraw
        # img = Image.new('RGB', (1024, 1280), color=(50, 50, 50))
        # img.save(output_path)

def run_painter():
    # Find the latest content folder
    content_root = "content"
    if not os.path.exists(content_root):
        print("No content directory found. Run planner.py first.")
        return

    dates = sorted(os.listdir(content_root))
    if not dates:
        print("No dated folders found.")
        return
        
    latest_date = dates[-1]
    work_dir = os.path.join(content_root, latest_date)
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
        
        # Rate limiting
        if i < len(prompts) - 1:
            time.sleep(2)
    
    print("\n" + "=" * 50)
    print("Image generation complete!")

if __name__ == "__main__":
    run_painter()
