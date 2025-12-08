import os
import json
from xhs import XhsClient
from dotenv import load_dotenv

load_dotenv()

def publish_to_xhs():
    # Load cookies from env (User must capture these from browser DevTools)
    # Format: "a=1; b=2; ..."
    cookie_str = os.getenv("XHS_COOKIE")
    
    if not cookie_str:
        print("Error: XHS_COOKIE not found. Cannot publish.")
        print("Please log in to web.xiaohongshu.com, copy your cookies, and set XHS_COOKIE in .env")
        return

    try:
        xhs_client = XhsClient(cookie=cookie_str)
        # Basic verification
        print("Verifying XHS session...")
        # user_info = xhs_client.get_self_info() # method name might vary in lib
        
        # Get latest content
        dates = sorted(os.listdir("content"))
        if not dates:
            print("No content to publish.")
            return
            
        latest_date = dates[-1]
        work_dir = os.path.join("content", latest_date)
        meta_path = os.path.join(work_dir, "meta.json")
        
        with open(meta_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Prepare Images
        image_paths = []
        for i in range(1, 7):
            p = os.path.join(work_dir, f"{i}.png")
            if os.path.exists(p):
                image_paths.append(p)
                
        if not image_paths:
            print("No images found to publish.")
            return
            
        print(f"Publishing: {data['title']}")
        
        # Upload Notes
        # Note: The xhs library usually requires creating a specific structure
        # This is a general pattern, specific library implementation details might vary
        
        note = xhs_client.create_image_note(
            title=data['title'],
            content=data['content'] + "\n\n" + " ".join(data['tags']),
            images=image_paths,
            is_private=False # Set to True to test first
        )
        
        print(f"Successfully published! Note ID: {note.get('note_id')}")
        
    except Exception as e:
        print(f"Publishing Failed: {e}")

if __name__ == "__main__":
    publish_to_xhs()
