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
    
    with sync_playwright() as p:
        # 使用持久化上下文，保存登录状态
        os.makedirs(USER_DATA_DIR, exist_ok=True)
        
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,  # 显示浏览器窗口
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )
        
        page = browser.pages[0] if browser.pages else browser.new_page()
        
        # 应用 stealth 模式
        if stealth_sync:
            stealth_sync(page)
        
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
                submit_btn.click()
                print("   已点击发布按钮")
                
                # 检测是否出现验证码（滑块）
                try:
                    # 等待一下看是否有滑块出现
                    slider = page.locator('.nc_scale, .slider-container, #nc_1_n1z').first
                    if slider.count() > 0: # 快速检查，或者用 wait_for with shorter timeout
                         pass
                    
                    # 尝试等待滑块出现，最多等3秒
                    page.wait_for_selector('.nc_scale, .slider-container, #nc_1_n1z', timeout=3000)
                    print("⚠️  检测到滑块验证码！尝试自动滑动...")
                    
                    # 简单的滑块处理逻辑 (拖动滑块)
                    slider_handle = page.locator('#nc_1_n1z, .nc_iconfont.btn_slide').first
                    if slider_handle.count() > 0:
                        box = slider_handle.bounding_box()
                        if box:
                            # 模拟拖拽
                            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                            page.mouse.down()
                            # 稍微带点随机性的移动
                            page.mouse.move(box["x"] + 500, box["y"] + box["height"] / 2, steps=20)
                            page.mouse.up()
                            print("   已模拟滑动操作")
                            time.sleep(2)
                except Exception:
                    # 没有出现滑块，或者没捕捉到
                    pass

                # 等待发布成功提示
                try:
                    print("   等待发布成功确认...")
                    # 成功后通常会跳转或者是弹出提示
                    page.wait_for_url("**/publish/**", timeout=5000) # 如果没有跳转，检查提示
                    # 检查是否有成功toast
                    page.wait_for_selector('text=发布成功', timeout=10000)
                    print("🎉 发布成功！")
                except:
                    print("⚠️  未检测到明确的发布成功信号，请手动检查")
                    
            else:
                print("❌ 未找到发布按钮，请手动点击")
            
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
            # print("\n按 Enter 键关闭浏览器...")
            # input()
            time.sleep(5)
        
        finally:
            browser.close()
            print("\n👋 浏览器已关闭")

if __name__ == "__main__":
    publish_to_xhs()
