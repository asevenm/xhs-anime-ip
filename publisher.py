import os
import json
import time
from playwright.sync_api import sync_playwright
# try-except import in case it's not installed
try:
    from playwright_stealth import stealth_sync
except ImportError:
    stealth_sync = None
from dotenv import load_dotenv

load_dotenv()

# 浏览器数据存储路径
USER_DATA_DIR = os.path.join(os.path.dirname(__file__), ".browser_data")

def publish_to_xhs():
    """使用 Playwright 浏览器自动化发布到小红书"""
    
    # 获取最新内容
    if not os.path.exists("content"):
        print("❌ No content directory found. Run planner.py first.")
        return
    
    dates = sorted([d for d in os.listdir("content") if os.path.isdir(os.path.join("content", d))])
    if not dates:
        print("❌ No dated folders found.")
        return
    
    latest_date = dates[-1]
    work_dir = os.path.join("content", latest_date)
    meta_path = os.path.join(work_dir, "meta.json")
    
    if not os.path.exists(meta_path):
        print(f"❌ No meta.json found in {work_dir}")
        return
    
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 准备图片
    image_paths = []
    for i in range(1, 7):
        p = os.path.join(work_dir, f"{i}.png")
        if os.path.exists(p):
            image_paths.append(os.path.abspath(p))
    
    if not image_paths:
        print("❌ No images found to publish.")
        return
    
    print("=" * 50)
    print("小红书 Playwright 发布工具")
    print("=" * 50)
    print(f"\n📝 标题: {data['title']}")
    print(f"🖼️  图片: {len(image_paths)} 张")
    print("=" * 50)
    
    # 检查是否在 GitHub Actions 运行
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    
    with sync_playwright() as p:
        # 使用持久化上下文，保存登录状态
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        
        # 如果是 GitHub Actions，必须使用 headless=True
        # 如果是本地，默认 False 以便调试
        headless_mode = is_github_actions
        
        print(f"🚀 启动浏览器 (Headless: {headless_mode})...")
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=headless_mode,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
            args=["--disable-blink-features=AutomationControlled"] # 尝试规避检测
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # 应用 stealth 模式
        if stealth_sync:
            stealth_sync(page)
            
        # 尝试从环境变量加载 Cookies (用于 GitHub Actions)
        cookies_json = os.environ.get("COOKIES_JSON")
        if cookies_json:
            try:
                print("🍪 检测到 cookies 环境变量，正在注入...")
                cookies = json.loads(cookies_json)
                browser.add_cookies(cookies)
                print("   Cookies 注入成功")
            except Exception as e:
                print(f"❌ Cookies 注入失败: {e}")
        
        try:
            # 访问创作者中心
            print("\n🌐 正在打开小红书创作者中心...")
            page.goto("https://creator.xiaohongshu.com/publish/publish?from=menu&target=image", wait_until="networkidle", timeout=60000)
            
            # 检查是否需要登录
            if "login" in page.url.lower() or page.locator("text=登录").count() > 0:
                print("\n⚠️  请在浏览器中手动登录小红书...")
                print("   登录完成后，脚本会自动继续")
                
                # 等待用户登录，最多等待5分钟
                page.wait_for_url("**/publish/**", timeout=300000)
                print("✅ 登录成功！")
            
            time.sleep(2)  # 等待页面稳定
            
            # 上传图片
            print("\n📤 正在上传图片...")
            
            # 先点击"上传图文"选项卡（如果有的话）
            try:
                image_tab = page.locator('text=发布图文, text=图文, [class*="image"]').first
                if image_tab.count() > 0:
                    image_tab.click()
                    time.sleep(1)
            except:
                pass
            
            # 找到图片上传input（排除视频上传的input）
            # 图片input通常接受 image/* 或 .jpg,.png,.gif 等
            file_inputs = page.locator('input[type="file"]').all()
            
            image_input = None
            for inp in file_inputs:
                accept = inp.get_attribute("accept") or ""
                # 寻找接受图片的input
                if "image" in accept.lower() or ".jpg" in accept.lower() or ".png" in accept.lower() or ".jpeg" in accept.lower():
                    # 检查是否支持多文件
                    multiple = inp.get_attribute("multiple")
                    image_input = inp
                    break
            
            if image_input is None:
                # 如果没找到明确的图片input，尝试找带有multiple属性的
                for inp in file_inputs:
                    multiple = inp.get_attribute("multiple")
                    accept = inp.get_attribute("accept") or ""
                    # 排除视频格式
                    if ".mp4" not in accept and ".mov" not in accept:
                        image_input = inp
                        break
            
            if image_input is None:
                print("⚠️  未找到图片上传按钮，请手动上传图片")
                print(f"   图片路径: {image_paths}")
            else:
                # 逐个上传图片（有些网站不支持多文件一次上传）
                for i, img_path in enumerate(image_paths):
                    try:
                        print(f"   上传图片 {i+1}/{len(image_paths)}...")
                        image_input.set_input_files(img_path)
                        time.sleep(2)  # 等待每张图片上传
                    except Exception as e:
                        print(f"   图片 {i+1} 上传失败: {e}")
            
            # 等待图片上传完成
            print("   等待图片处理...")
            time.sleep(5)  # 给上传一些时间
            
            # 填写标题
            print("📝 正在填写标题...")
            title_input = page.locator('input[placeholder*="标题"], input[class*="title"], #title').first
            if title_input.count() > 0:
                title_input.fill(data['title'][:20])  # 标题限制20字
            else:
                # 尝试其他选择器
                title_input = page.locator('[class*="title"] input, [data-testid="title"]').first
                if title_input.count() > 0:
                    title_input.fill(data['title'][:20])
            
            # 填写正文
            print("📝 正在填写正文...")
            desc_text = data['content'] + "\n\n" + " ".join(data['tags'])
            
            # 尝试多种正文输入选择器
            desc_selectors = [
                '[placeholder*="正文"]',
                '[placeholder*="描述"]',
                '[class*="content"] textarea',
                '[class*="desc"] textarea',
                '#post-textarea',
                '[contenteditable="true"]'
            ]
            
            for selector in desc_selectors:
                desc_input = page.locator(selector).first
                if desc_input.count() > 0:
                    try:
                        desc_input.fill(desc_text[:1000])  # 正文限制1000字
                        break
                    except:
                        continue
            
            print("✅ 内容填写完成！")

            # 自动点击发布
            print("\n🚀 正在自动点击发布...")
            submit_btn = page.locator('button.submit, button:has-text("发布"), .publish-btn').first
            
            if submit_btn.count() > 0:
                # 点击发布按钮的循环，最多尝试3次
                for attempt in range(3):
                    print(f"   点击发布按钮 (尝试 {attempt+1})...")
                    try:
                        submit_btn.click()
                    except:
                        # 可能是被滑块遮挡，尝试 force=True
                        submit_btn.click(force=True)
                    
                    # 检测是否出现验证码（滑块）
                    time.sleep(2)
                    
                    # 检查滑块
                    slider = page.locator('.nc_scale, .slider-container, #nc_1_n1z').first
                    if slider.count() > 0 and slider.is_visible():
                        print("⚠️  检测到滑块验证码！尝试自动滑动...")
                        slider_handle = page.locator('#nc_1_n1z, .nc_iconfont.btn_slide').first
                        if slider_handle.count() > 0:
                            box = slider_handle.bounding_box()
                            if box:
                                page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                                page.mouse.down()
                                page.mouse.move(box["x"] + 500, box["y"] + box["height"] / 2, steps=20)
                                page.mouse.up()
                                time.sleep(2)
                    
                    # 检查是否已经跳转或成功，如果是则退出点击循环
                    if "manage" in page.url or "success" in page.url:
                        break
                    if page.locator('text=发布成功').count() > 0 or \
                       page.locator('text=已发布').count() > 0:
                        break
                    
                    # 如果按钮还在且可见，说明点击可能没生效，继续循环
                    if not submit_btn.is_visible():
                        break
                        
                    print("   似乎未跳转，准备重试...")
                    time.sleep(2)
            else:
                print("❌ 未找到发布按钮，请手动点击")

            # 等待发布成功提示
            try:
                print("   等待发布成功确认...")
                
                # 轮询检查
                start_time = time.time()
                success = False
                while time.time() - start_time < 15:
                    # 检查 URL 是否包含 success 或 manage
                    if "manage" in page.url or "success" in page.url:
                        print("   检测到页面跳转，发布可能成功")
                        success = True
                        break
                    
                    # 检查是否有成功提示元素
                    # 可以根据实际情况添加更多关键词
                    if page.locator('text=发布成功').count() > 0 or \
                       page.locator('text=已发布').count() > 0 or \
                       page.locator('div[class*="success"]').count() > 0:
                        print("   检测到成功提示")
                        success = True
                        break
                    
                    time.sleep(0.5)
                
                if success:
                    print("🎉 发布成功！")
                else:
                    raise Exception("Timeout waiting for success signal")

            except Exception as e:
                print(f"⚠️  未检测到明确的发布成功信号: {e}")
                # 截图以供调试
                screenshot_path = os.path.join(work_dir, "publish_status_debug.png")
                page.screenshot(path=screenshot_path)
                print(f"   已保存页面截图到: {screenshot_path}")
                print("   请手动检查浏览器状态")
            
            # 只有在出错或未确认成功时才暂停，否则直接退出
            if page.locator('text=发布成功').count() == 0:
                print("\n按 Enter 键关闭浏览器...")
                # give user a chance to see what happened if not successful
                # input() 
                # To make it fully automated, we might remove input() but keep a short sleep
                time.sleep(5)
            else:
                time.sleep(3) # Show success for a moment
            
        except Exception as e:
            print(f"\n❌ 发布失败: {e}")
            if not is_github_actions:
                time.sleep(5)
        
        finally:
            # 如果是本地运行，保存 cookies 方便导出到 GitHub
            if not is_github_actions:
                try:
                    cookies = browser.cookies()
                    with open("xhs_cookies.json", "w", encoding="utf-8") as f:
                        json.dump(cookies, f, indent=2)
                    print(f"\n🍪 Cookies 已保存到 {os.path.abspath('xhs_cookies.json')}")
                    print("   请复制此文件内容到 GitHub Secrets (Name: COOKIES_JSON)")
                except Exception as e:
                    print(f"   Cookies 保存失败: {e}")
            
            browser.close()
            print("\n👋 浏览器已关闭")

if __name__ == "__main__":
    publish_to_xhs()
