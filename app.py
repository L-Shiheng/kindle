import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from zhdate import ZhDate
from datetime import datetime
import pytz
import requests
import time

# --- 设置页面配置 (隐藏多余菜单，全屏) ---
st.set_page_config(
    page_title="Kindle Clock",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 隐藏 Streamlit 自带的汉堡菜单和页脚 ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .block-container {
                padding-top: 0rem;
                padding-bottom: 0rem;
                padding-left: 0rem;
                padding-right: 0rem;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 核心逻辑 ---
def get_weather():
    try:
        # 使用 wttr.in 获取简单天气，格式：天气图标+温度
        # ?format=%C+%t 意思是：Condition + Temperature
        r = requests.get("http://wttr.in/Shanghai?format=%C+%t", timeout=2)
        return r.text.strip()
    except:
        return "Weather N/A"

def create_clock_image():
    # 1. 定义画布大小 (Kindle PW 比例)
    # 为了防止网络传输太慢，我们不做太大的图，800宽够了
    width, height = 800, 1060 
    canvas = Image.new('L', (width, height), 255) # L 代表灰度
    draw = ImageDraw.Draw(canvas)

    # 2. 加载背景图 (如果存在)
    try:
        img = Image.open("bg.jpg").convert('L')
        # 调整大小并居中裁剪 (Cover模式)
        img_ratio = img.width / img.height
        canvas_ratio = width / height
        
        if img_ratio > canvas_ratio:
            # 图片更宽，按高度缩放
            new_height = height
            new_width = int(new_height * img_ratio)
            img = img.resize((new_width, new_height))
            offset = (new_width - width) // 2
            canvas.paste(img, (-offset, 0))
        else:
            # 图片更高，按宽度缩放
            new_width = width
            new_height = int(new_width / img_ratio)
            img = img.resize((new_width, new_height))
            canvas.paste(img, (0, 0))
            
    except FileNotFoundError:
        # 如果没有图，就纯白背景
        pass

    # 3. 绘制半透明蒙版 (为了让文字看清)
    # PIL L模式不支持透明度，我们只能画实心矩形或直接写字
    # 这里简单画一个白色底框在文字区域
    draw.rectangle([(20, 100), (width-20, 500)], fill=255, outline=0)

    # 4. 获取时间信息 (强制使用中国时区)
    tz = pytz.timezone('Asia/Shanghai')
    now = datetime.now(tz)
    
    time_str = now.strftime("%H:%M")
    date_str = now.strftime("%Y-%m-%d %A")
    lunar = ZhDate.from_datetime(now)
    lunar_str = f"农历 {lunar.chinese()}"
    weather_str = get_weather()

    # 5. 绘制文字 (Streamlit Cloud 只有默认字体，除非你上传字体文件)
    # 为了方便，我们这里使用默认字体，虽然丑一点但不用配置
    # 如果你想好看，需要上传 .ttf 文件并在代码里 ImageFont.truetype("xxx.ttf", size)
    
    # 这里的 None 代表使用系统默认位图字体，不能调大小，只能放大图片
    # 既然在云端，我们尽量画大字。
    # *** 关键技巧：由于云端缺少中文字体，我们用 Streamlit 的 st.markdown 显示文字更安全 ***
    # 所以：Python只负责处理逻辑，显示交给 st 
    
    return time_str, date_str, lunar_str, weather_str

# --- 页面显示 ---

# 创建占位符
placeholder = st.empty()

while True:
    time_str, date_str, lunar_str, weather_str = create_clock_image()
    
    with placeholder.container():
        # 显示背景图
        try:
            st.image("bg.jpg", use_container_width=True)
        except:
            pass
            
        # 使用 CSS 浮层把文字压在图片上 (这是 Kindle 能显示的 HTML)
        st.markdown(
            f"""
            <div style="
                position: fixed; 
                top: 50%; 
                left: 50%; 
                transform: translate(-50%, -50%); 
                background-color: rgba(255,255,255,0.8); 
                padding: 40px; 
                border-radius: 20px; 
                text-align: center; 
                border: 3px solid black;
            ">
                <h1 style="font-size: 80px; margin:0; color: black;">{time_str}</h1>
                <p style="font-size: 30px; margin:0; color: black;">{date_str}</p >
                <hr>
                <p style="font-size: 24px; color: black;">{lunar_str}</p >
                <p style="font-size: 24px; color: black;">{weather_str}</p >
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # 每一分钟刷新一次
    time.sleep(60)
    # Streamlit 会检测代码变动，但我们需要强制刷新循环
    # 注意：在 Streamlit Cloud 这种 while True 循环可能会被杀掉
    # 但这是最简单的实现方式
