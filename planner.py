import os
import json
import random
import datetime
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# 独立的大型IP库：包含50+经典/高人气动漫系列
ANIME_IPS = [
    # 热血少年
    {"name": "火影忍者", "characters": "鸣人、佐助、小樱、卡卡西、雏田、我爱罗", "genre": "热血"},
    {"name": "海贼王", "characters": "路飞、索隆、娜美、罗宾、艾斯、女帝", "genre": "热血"},
    {"name": "鬼灭之刃", "characters": "炭治郎、祢豆子、善逸、伊之助、蝴蝶忍、义勇", "genre": "热血"},
    {"name": "咒术回战", "characters": "虎杖悠仁、伏黑惠、�的井野蔷薇、五条悟、夏油杰", "genre": "热血"},
    {"name": "进击的巨人", "characters": "艾伦、三笠、阿尔敏、利威尔、韩吉", "genre": "热血"},
    {"name": "我的英雄学院", "characters": "绿谷出久、爆豪胜己、丽日御茶子、欧尔麦特", "genre": "热血"},
    {"name": "猎人×猎人", "characters": "小杰、奇犽、酷拉皮卡、雷欧力、西索", "genre": "热血"},
    {"name": "龙珠", "characters": "悟空、贝吉塔、悟饭、布尔玛、特兰克斯", "genre": "热血"},
    {"name": "灌篮高手", "characters": "樱木花道、流川枫、赤木晴子、三井寿、宫城良田", "genre": "热血"},
    {"name": "排球少年", "characters": "日向翔阳、影山飞雄、及川彻、研磨", "genre": "热血"},

    # 治愈/日常
    {"name": "夏目友人帐", "characters": "夏目贵志、猫咪老师、田沼要、多轨透", "genre": "治愈"},
    {"name": "间谍过家家", "characters": "黄昏、约尔、安妮亚、邦德", "genre": "治愈"},
    {"name": "葬送的芙莉莲", "characters": "芙莉莲、费伦、修塔尔克、欣梅尔", "genre": "治愈"},
    {"name": "摇曳露营", "characters": "志摩凛、抚子、千明、绫乃、惠那", "genre": "治愈"},
    {"name": "孤独摇滚", "characters": "后藤一里、伊地知虹夏、山田凉、喜多郁代", "genre": "治愈"},
    {"name": "轻音少女", "characters": "平泽唯、秋山澪、田井中律、�的山�的", "genre": "治愈"},

    # 恋爱/青春
    {"name": "辉夜大小姐想让我告白", "characters": "白银御行、四宫辉夜、藤原千花、石上优", "genre": "恋爱"},
    {"name": "五等分的新娘", "characters": "中野一花、二乃、三玖、四叶、五月、风太郎", "genre": "恋爱"},
    {"name": "你的名字", "characters": "立花�的、宫水三叶", "genre": "恋爱"},
    {"name": "天气之子", "characters": "森岛帆高、天野陽菜", "genre": "恋爱"},
    {"name": "CLANNAD", "characters": "冈崎朋也、古河渚、藤林杏、坂上智代", "genre": "恋爱"},
    {"name": "龙与虎", "characters": "逢坂大河、高须龙児、川嶋亚美", "genre": "恋爱"},

    # 奇幻/冒险
    {"name": "刀剑神域", "characters": "桐人、亚丝娜、诗乃、尤吉欧、爱丽丝", "genre": "奇幻"},
    {"name": "Re:从零开始", "characters": "菜月昴、爱蜜莉雅、雷姆、拉姆", "genre": "奇幻"},
    {"name": "无职转生", "characters": "鲁迪乌斯、洛琪希、艾丽丝、希尔菲", "genre": "奇幻"},
    {"name": "魔法少女小圆", "characters": "鹿目圆、晓美焰、巴麻美、美树沙耶香", "genre": "奇幻"},
    {"name": "Fate系列", "characters": "卫宫士郎、Saber、远坂凛、间桐樱、吉尔伽美什", "genre": "奇幻"},
    {"name": "魔卡少女樱", "characters": "木之本樱、李小狼、知世、小可", "genre": "奇幻"},

    # 经典/怀旧
    {"name": "新世纪福音战士", "characters": "碇真嗣、绫波丽、明日香、渚薫", "genre": "经典"},
    {"name": "美少女战士", "characters": "月野兔、水野亚美、火野丽、木野真琴", "genre": "经典"},
    {"name": "犬夜叉", "characters": "犬夜叉、戈薇、杀生丸、桔梗、弥勒、珊瑚", "genre": "经典"},
    {"name": "银魂", "characters": "坂田银时、志村新八、神乐、高杉晋助", "genre": "经典"},
    {"name": "钢之炼金术师", "characters": "爱德华、阿尔冯斯、罗伊、温莉", "genre": "经典"},
    {"name": "星际牛仔", "characters": "斯派克、菲、杰特、艾德", "genre": "经典"},

    # 吉卜力
    {"name": "千与千寻", "characters": "千寻、白龙、无脸男、汤婆婆", "genre": "吉卜力"},
    {"name": "哈尔的移动城堡", "characters": "哈尔、苏菲、荒野女巫、卡西法", "genre": "吉卜力"},
    {"name": "龙猫", "characters": "小月、小梅、龙猫、猫巴士", "genre": "吉卜力"},
    {"name": "天空之城", "characters": "希达、巴鲁、穆斯卡", "genre": "吉卜力"},
    {"name": "幽灵公主", "characters": "阿席达卡、珊、黑帽大人、山犬神", "genre": "吉卜力"},
    {"name": "魔女宅急便", "characters": "琪琪、吉吉、蜻蜓", "genre": "吉卜力"},

    # 赛博/科幻
    {"name": "赛博朋克边缘行者", "characters": "大卫、露西、瑞贝卡", "genre": "科幻"},
    {"name": "攻壳机动队", "characters": "草薙素子、巴特", "genre": "科幻"},
    {"name": "PSYCHO-PASS", "characters": "常守朱、狡噛慎也", "genre": "科幻"},

    # VOCALOID/虚拟偶像
    {"name": "初音未来", "characters": "初音未来、镜音双子、巡音流歌、KAITO、MEIKO", "genre": "虚拟偶像"},

    # 最新人气
    {"name": "蓝色监狱", "characters": "潔世一、蜂乐回、糸师凛、凪�的城", "genre": "热血"},
    {"name": "药屋少女的呢喃", "characters": "猫猫、壬氏", "genre": "治愈"},
    {"name": "我推的孩子", "characters": "星野爱、星野愛久愛海、有马加那", "genre": "恋爱"},
]

class DailyContent(BaseModel):
    date: str = Field(description="Date of the post in YYYY-MM-DD format")
    theme: str = Field(description="The central theme of the 6 images (e.g., 'Summer Rain', 'Train Station at Dusk')")
    style_name: str = Field(description="The art style used for this batch (e.g., 'Makoto Shinkai Style')")
    title: str = Field(description="Catchy Xiaohongshu title (include emojis)")
    content: str = Field(description="Engaging body text for the post, emotional and atmospheric")
    tags: List[str] = Field(description="List of hashtags (e.g., #Ghibli #Anime #Wallpaper)")
    image_prompts: List[str] = Field(description="List of 6 distinct but thematically consistent image prompts for the AI")

STYLES = {
    "makoto_shinkai": {
        "name": "新海诚光影",
        "description": "“新海诚美学”——**极致光影**与**超写实壁纸感**",
        "keywords": "新海诚, 极致光影, 治愈, 壁纸党, 你的名字, 天气之子",
        "prompt_example": "\"(Makoto Shinkai style:1.5), masterpiece, 8K wallpaper quality, photorealistic clouds with golden hour lighting. A young couple standing on a rooftop looking at a comet... --ar 3:4\"",
        "visual_requirements": """
       - 风格权重标记：必须使用 (Makoto Shinkai style:1.5)
       - 极致光影：必须包含复杂的光线效果词汇 (volumetric lighting, god rays, golden hour, lens flare, rim lighting)
       - 天空要素：photorealistic clouds, dramatic sky gradients (orange/purple/deep blue), towering cumulus
       - 场景特征：电车、天台、十字路口、城市夜景、雨后积水反射
       - 质感：8K wallpaper quality, hyper-detailed, photorealistic, cinematic composition
        """,
        "recommended_ips": [
             "新海诚系列：三叶、泷、陽菜、帆高、铃芽、草太",
             "经典少女漫（光影风）：小樱、小狼、月野兔",
             "治愈系：夏目贵志、薇尔莉特"
        ]
    },
    "studio_ghibli": {
        "name": "吉卜力童话",
        "description": "“吉卜力童话”——**手绘质感**、**自然治愈**与**怀旧温情**",
        "keywords": "宫崎骏, 吉卜力, 手绘风, 治愈, 童话感, 怀旧",
        "prompt_example": "\"(Studio Ghibli style:1.5), masterpiece, 8K wallpaper quality, hand-drawn logic, watercolor texture. A young boy adventurer exploring an ancient ruin covered in moss... --ar 3:4\"",
        "visual_requirements": """
       - 风格权重标记：必须使用 (Studio Ghibli style:1.5)
       - 手绘质感：必须包含 (hand-drawn, watercolor texture, gouache style, cel shaded)
       - 自然与色彩：使用饱和度适中、色彩丰富的调色板 (lush greenery, fluffy clouds, vibrant blue sky)
       - 标志性元素：茂密的森林、草地、花海、巨大的积云、欧式小镇、飞行器
       - 氛围：Peaceful, nostalgic, magical realism
        """,
        "recommended_ips": [
            "宫崎骏系列：千寻、哈尔、苏菲、琪琪、珊、阿席达卡",
            "治愈日常：龙猫、波妞",
            "其他适合童话风的角色：小樱、安妮亚、弗里伦"
        ]
    },
    "kyoto_animation": {
        "name": "京阿尼细腻",
        "description": "“京阿尼美学”——**细腻情感**、**唯美光影**与**精致人物**",
        "keywords": "京阿尼, 紫罗兰永恒花园, 唯美, 细腻, 壁纸, 眼睛特写",
        "prompt_example": "\"(Kyoto Animation style:1.5), masterpiece, highly detailed eyes. A girl crying with tears turning into jewels, soft morning light through window... --ar 3:4\"",
        "visual_requirements": """
       - 风格权重标记：必须使用 (Kyoto Animation style:1.5)
       - 精致人物：必须强调 (highly detailed eyes, expressive emotion, delicate hair strands, blush)
       - 唯美光影：soft lighting, bokeh, sparkling particles, emotional atmosphere, light leaks
       - 场景特征：学园、樱花道、欧式庭院、图书馆、窗边
       - 质感：High quality animation art, detailed background art
        """,
        "recommended_ips": [
            "京阿尼系列：薇尔莉特 (Violet Evergarden)、千反田爱瑠、折木奉太郎、御坂美琴",
            "日常系：平泽唯、秋山澪",
            "其他：雷姆、爱蜜莉雅"
        ]
    },
    "retro_90s": {
        "name": "90年代赛璐璐",
        "description": "“90年代复古”——**赛璐璐质感**、**高对比度**与**怀旧颗粒感**",
        "keywords": "90年代, 复古, 赛璐璐, 怀旧, 蒸汽波, CityPop",
        "prompt_example": "\"(90s anime style:1.5), (retro artstyle:1.2), masterpiece, cel shaded. A male detective in a trench coat standing in the rain, neon city lights reflecting... --ar 3:4\"",
        "visual_requirements": """
       - 风格权重标记：必须使用 (90s anime style:1.5), (retro artstyle:1.2)
       - 复古质感：cel shading, bold outlines, grainy texture, chromatic aberration (subtle), VHS effect
       - 色彩风格：pastel colors or neon aesthetic, simple gradients, high contrast
       - 场景特征：90s Tokyo street, sunset beach, retro cafe, vending machine, bedroom with posters
        """,
        "recommended_ips": [
            "经典90s：月野兔 (Sailor Moon)、星际牛仔 (Spike/Faye)、EVA (明日香/绫波丽)",
            "复古风重绘：初音未来、魔卡少女樱",
            "格斗/热血：乱马1/2"
        ]
    },
    "mamoru_hosoda": {
        "name": "细田守夏日",
        "description": "“夏日大作战”——**清爽线条**、**积云**与**充满活力的夏日感**",
        "keywords": "细田守, 夏日大作战, 清爽, 蓝天白云, 少年感",
        "prompt_example": "\"(Mamoru Hosoda style:1.5), masterpiece, clean lines. A boy running in a rural Japanese village, giant cumulus cloud in background... --ar 3:4\"",
        "visual_requirements": """
       - 风格权重标记：必须使用 (Mamoru Hosoda style:1.5)
       - 视觉风格：clean lines, flat shading, vibrant colors, minimal gradients (poster style)
       - 标志性元素：towering cumulonimbus clouds (entry cloud), wide angle lens
       - 场景特征：Japanese countryside in summer, digital space, huge crowds, blue sky
       - 氛围：Energetic, refreshing, summer vibe
        """,
        "recommended_ips": [
            "细田守系列：真琴 (穿越时空的少女)、健二/夏希 (夏日大作战)、铃 (贝儿)",
            "其他夏日感：宝可梦训练师、数码宝贝太一/大和"
        ]
    }
}

def get_common_prompt(today: str) -> str:
    # Randomly select a style
    style_key = random.choice(list(STYLES.keys()))
    style_config = STYLES[style_key]

    # Randomly select an IP from the independent IP pool
    selected_ip = random.choice(ANIME_IPS)

    # Construct a clear JSON example structure
    json_structure_example = {
        "date": today,
        "theme": "填入主题",
        "style_name": style_config['name'],
        "title": "填入标题",
        "content": "填入正文",
        "tags": ["#标签1", "#标签2"],
        "image_prompts": [
            "image prompt 1 --ar 3:4",
            "image prompt 2 --ar 3:4",
            "image prompt 3 --ar 3:4",
            "image prompt 4 --ar 3:4",
            "image prompt 5 --ar 3:4",
            "image prompt 6 --ar 3:4"
        ]
    }

    return f"""
    你是小红书**{style_config['name']}**风格壁纸账号的创意总监。我们的定位是{style_config['description']}。

    任务：为今天（{today}）策划内容。

    要求：
    1. 选择一个符合**{style_config['name']}**氛围的主题。

    2. 标题、正文、标签必须用中文，要贴合小红书用户喜好，情感共鸣强，适当使用emoji。
       必须包含的关键词/标签：{style_config['keywords']}

    3. 生成6个详细的图片prompt，优化用于{os.getenv('IMAGE_LLM_PROVIDER', 'Nano Banana')}：

       格式示例：
       {style_config['prompt_example']}

       关键要求：
       {style_config['visual_requirements']}

    4. 动漫IP策略（重要）：
       * **本次指定IP**：{selected_ip['name']}
       * **可用角色**：{selected_ip['characters']}
       * **风格适配**：请用「{style_config['name']}」的视觉风格重新演绎上述角色
       * **角色多元**：6张图必须展示该IP下的不同角色，严禁6张图都是同一角色
       * **性别多样**：务必包含男性角色和男女互动场景
       * 角色必须清晰描述外貌特征（发色、服装、标志性物品）以便AI准确生成

    5. 6张图保持**{style_config['name']}**风格统一，场景各异。

    6. 固定后缀：每个prompt必须以" --ar 3:4"结尾。

    输出JSON格式。
    注意：必须直接返回填写好的JSON数据对象，**绝对不要**返回Schema定义，不要包含 "type", "description" 等Schema字段。

    目标JSON结构示例（请填充具体内容）：
    {json.dumps(json_structure_example, ensure_ascii=False, indent=2)}
    """

def get_client_config():
    """Determine API configuration based on environment variables."""
    provider = os.getenv("TEXT_LLM_PROVIDER", "gemini").lower()
    
    if provider == "gemini":
        # Google Gemini via OpenAI Compatible Endpoint
        return {
            "api_key": os.getenv("GEMINI_API_KEY"),
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": "gemini-2.5-pro", # Use a cheaper/faster model if desired, but pro is fine
            "provider_name": "Gemini (OpenAI Interface)"
        }
    elif provider == "doubao":
        return {
            "api_key": os.getenv("ARK_API_KEY"),
            "base_url": 'https://ark.cn-beijing.volces.com/api/v3',
            "model": os.getenv("LLM_MODEL_NAME", "doubao-1-5-pro-32k-250115"),
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
        data = json.loads(content)
        
        # Fix for Doubao/Qwen: sometimes they return the schema wrapped in "properties"
        if "properties" in data:
            data = data["properties"]

        # Fix for Doubao/Qwen: sometimes values are objects with "value" and "description"
        cleaned_data = {}
        for k, v in data.items():
            if isinstance(v, dict) and "value" in v:
                cleaned_data[k] = v["value"]
            elif isinstance(v, dict) and "type" in v and "description" in v:
                 # This looks like a schema definition, not a value. 
                 # We shouldn't use it.
                 pass
            else:
                cleaned_data[k] = v
        
        data = cleaned_data
            
        # Validate against the Pydantic model
        try:
            # removing any extra keys that might cause issues if strict, 
            # though default pydantic ignores extras unless configured otherwise.
            # We recreate the object to ensure field order and types.
            validated = DailyContent(**data)
            return validated.model_dump()
        except Exception as e:
            print(f"Validation error: {e}. Data was not valid.")
            return None
        
    except Exception as e:
        print(f"Error generating content: {e}")
        return None

if __name__ == "__main__":
    plan = generate_daily_plan()
    if plan:
        # Create directory for today
        if 'date' not in plan:
             plan['date'] = datetime.date.today().strftime("%Y-%m-%d")

        date_dir = os.path.join("content", plan['date'])
        os.makedirs(date_dir, exist_ok=True)
        
        # Save metadata
        with open(os.path.join(date_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
            
        print(f"✅ Plan generated for {plan['date']}")
        print(f"📝 Title: {plan['title']}")
    else:
        print("❌ Failed to generate plan.")
