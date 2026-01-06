import os
import json
import datetime
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DailyContent(BaseModel):
    date: str = Field(description="Date of the post in YYYY-MM-DD format")
    theme: str = Field(description="The central theme of the 6 images (e.g., 'Summer Rain', 'Train Station at Dusk')")
    title: str = Field(description="Catchy Xiaohongshu title (include emojis)")
    content: str = Field(description="Engaging body text for the post, emotional and atmospheric")
    tags: List[str] = Field(description="List of hashtags (e.g., #Ghibli #Anime #Wallpaper)")
    image_prompts: List[str] = Field(description="List of 6 distinct but thematically consistent image prompts for the AI")

def get_common_prompt(today: str) -> str:
    return f"""
    你是小红书新海诚风格壁纸账号的创意总监。我们的定位是"新海诚美学"——**极致光影**与**超写实壁纸感**。
    
    任务：为今天（{today}）策划内容。
    
    要求：
    1. 选择一个光影氛围感极强的主题（如：黄昏的天空、雨后的城市、星空下的少年少女、阳光穿透云层的瞬间等）
    
    2. 标题、正文、标签必须用中文，要贴合小红书用户喜好，情感共鸣强，适当使用emoji，突出"壁纸党"、"治愈"、"光影美学"等关键词
    
    3. 生成6个详细的图片prompt，优化用于Nano Banana：
       
       格式示例：
       "(Makoto Shinkai style:1.5), masterpiece, 8K wallpaper quality, photorealistic clouds with golden hour lighting. A girl in school uniform standing on a rooftop, her hair gently flowing in the wind as she gazes at the dramatic sunset sky. Volumetric god rays piercing through towering cumulus clouds, lens flare, hyper-detailed sky gradients from orange to deep purple, wet rooftop reflecting the colorful sky, atmospheric perspective, cinematic composition --ar 3:4"
       
       关键要求：
       - 风格权重标记：必须使用 (Makoto Shinkai style:1.5)
       - 极致光影：必须包含复杂的光线效果词汇，如：
         * 光线类：volumetric lighting, god rays, golden hour, magic hour, lens flare, rim lighting, backlit, dramatic sunlight, dappled light
         * 天空类：photorealistic clouds, towering cumulus, dramatic sky gradients, sunset afterglow, twilight atmosphere
         * 反射类：wet surface reflections, puddle reflections, glass reflections, city lights reflecting
       - 超写实壁纸感：必须包含以下关键词：8K wallpaper quality, hyper-detailed, photorealistic, cinematic composition, atmospheric perspective
       - 新海诚标志性元素：
         * 天空：层次丰富的云彩、极致的天空渐变色（橙红-粉紫-深蓝）
         * 光线：丁达尔效应/体积光、逆光剪影、黄金时刻/魔幻时刻
         * 场景：电车、天台、十字路口、铁道口、城市夜景、星空
         * 天气：雨滴、飘雪、飞散的樱花花瓣
         * 细节：玻璃反射、水面倒影、湿润的地面
       - 动漫IP策略（重要）：
         * 可使用**任意经典动漫IP**的角色，不限于新海诚作品
         * **一次生成的6张图优先使用同一个动漫IP**，保持角色的统一性和粉丝吸引力
         * 也可以选择**同一作者/工作室的多个作品IP混搭**（如：宫崎骏系列、CLAMP系列、京阿尼系列等）
         * 热门IP推荐：
           - 宫崎骏系列：千寻、白龙、苏菲、哈尔、琪琪、龙猫、阿莉埃蒂
           - 新海诚系列：三叶、的、陽菜、帆高、铃芽、草太
           - 经典少女漫：小樱、小狼、月野兔、木之本樱
           - 热血番：路飞、鸣人、炭治郎、五条悟、杀生丸、犬夜叉
           - 治愈系：夏目贵志、猫咪老师、薇尔莉特
         * 角色必须清晰描述外貌特征（发色、服装、标志性物品）以便AI准确生成
       - 6张图保持**新海诚光影风格统一**，场景各异（如：1张黄昏天台、1张雨中城市、1张星空草原、1张电车窗边、1张樱花飘落、1张城市夜景）
       - 固定后缀：每个prompt必须以" --ar 3:4"结尾
    
    输出JSON格式，严格遵守DailyContent schema。
    """

def get_client_config():
    """Determine API configuration based on environment variables."""
    provider = os.getenv("TEXT_LLM_PROVIDER", "gemini").lower()
    
    if provider == "gemini":
        # Google Gemini via OpenAI Compatible Endpoint
        return {
            "api_key": os.getenv("GEMINI_API_KEY"),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-2.5-pro",
            "provider_name": "Gemini (OpenAI Interface)"
        }
    elif provider == "doubao":
        return {
            "api_key": os.getenv("ARK_API_KEY"),
            "base_url": 'https://ark.cn-beijing.volces.com/api/v3',
            "model": os.getenv("LLM_MODEL_NAME", "Doubao-1.5-pro-32k"),
            "provider_name": "Ark (OpenAI Interface)"
        }
    elif provider == "dashscope":
        return {
            "api_key": os.getenv("DASHSCOPE_API_KEY"),
            "base_url": 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            "model": os.getenv("LLM_MODEL_NAME", "qwen3-max"),
            "provider_name": "Dashscope (OpenAI Interface)"
        }
    else:
        print(f"Unknown provider: {provider}. Falling back to Gemini.")
        return {
            "api_key": os.getenv("GEMINI_API_KEY"),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-2.5-pro",
            "provider_name": "Gemini (OpenAI Interface)"
        }   

def generate_daily_plan():
    """Generates the daily content plan."""
    config = get_client_config()
    
    if not config["api_key"]:
        print(f"Error: API Key not found for provider {config['provider_name']}")
        return None
        
    print(f"Using Provider: {config['provider_name']} | Model: {config['model']}")
    
    today = datetime.date.today().strftime("%Y-%m-%d")

    try:
        client = OpenAI(
            api_key=config["api_key"],
            base_url=config["base_url"]
        )
        
        completion = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Output valid JSON only."},
                {"role": "user", "content": get_common_prompt(today)}
            ],
            response_format={"type": "json_object"}
        )
        
        content = completion.choices[0].message.content
        return json.loads(content)
        
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
            
        print(f"✅ Plan generated for {plan['date']}")
        print(f"📝 Title: {plan['title']}")
    else:
        print("❌ Failed to generate plan.")
