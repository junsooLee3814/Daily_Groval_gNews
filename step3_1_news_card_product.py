import os
import glob
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from common_utils import get_gsheet

CARD_WIDTH = 1080
CARD_HEIGHT = 1920
TOP_MARGIN = 300
BOTTOM_MARGIN = 180
LEFT_MARGIN = 80
RIGHT_MARGIN = 80
LINE_SPACING = 1.3
SECTION_GAP = 55

CATEGORY_FONT_SIZE = 50
DATE_FONT_SIZE = 40
TITLE_FONT_SIZE = 50
SUMMARY_FONT_SIZE = 44
SOURCE_FONT_SIZE = 38
IMG_DURATIONS = [5]
KOR_FONT_PATH = "C:/Windows/Fonts/Pretendard-Regular.otf"
KOR_FONT_BOLD_PATH = "C:/Windows/Fonts/Pretendard-Bold.otf"

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

category_font = load_font(KOR_FONT_PATH, CATEGORY_FONT_SIZE)
date_font = load_font(KOR_FONT_PATH, DATE_FONT_SIZE)
title_font = load_font(KOR_FONT_BOLD_PATH, TITLE_FONT_SIZE)
summary_font = load_font(KOR_FONT_PATH, SUMMARY_FONT_SIZE)
source_font = load_font(KOR_FONT_PATH, SOURCE_FONT_SIZE)

sheet = get_gsheet('morning_news')
data = sheet.get_all_records()
df = pd.DataFrame(data)
# 국내 30개, 글로벌 20개만 추출
kor_rows = df[df['category'].str.startswith('국내_')].iloc[:30]
glb_rows = df[df['category'].str.startswith('글로벌_')].iloc[:20]
news_rows = pd.concat([kor_rows, glb_rows]).reset_index(drop=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def draw_text_with_letter_spacing(draw, position, text, font, fill, letter_spacing=-2):
    x, y = position
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font) + letter_spacing

def wrap_text(text, font, max_width, draw):
    lines = []
    words = text.split()
    line = ''
    for word in words:
        test_line = line + (' ' if line else '') + word
        w = draw.textlength(test_line, font=font)
        if w <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

os.makedirs('news_card', exist_ok=True)
# news_card 폴더 내 기존 .png 파일 삭제
for f in glob.glob('news_card/*.png'):
    os.remove(f)

for i in range(0, len(news_rows), 2):
    card_path = os.path.join(BASE_DIR, "assets", "card01_1080x1560.png")
    card = Image.open(card_path).convert("RGBA")
    draw = ImageDraw.Draw(card)
    max_text_width = CARD_WIDTH - LEFT_MARGIN - RIGHT_MARGIN

    # 페이지 표시 텍스트 추가
    page_text = f"{i//2+1}/25"
    page_font = category_font
    page_y = TOP_MARGIN
    draw_text_with_letter_spacing(draw, (LEFT_MARGIN, page_y), page_text, page_font, (34,34,34,255))
    # 카테고리 y좌표를 페이지 텍스트 기준 2줄 아래로 조정
    category_y = page_y + int(CATEGORY_FONT_SIZE * LINE_SPACING) * 2

    total_height = 0
    news_heights = []
    news_blocks = []
    pair = news_rows.iloc[i:i+2]
    for idx, data_row in pair.iterrows():
        block_lines = []
        block_height = 0
        category = f"[{data_row['category']}]"
        # 카테고리만 첫 뉴스에만 y좌표를 category_y로 강제 지정
        if idx == 0:
            block_lines.append((category, category_font, (34,34,34,255), category_y))
        else:
            block_lines.append((category, category_font, (34,34,34,255), None))
        block_height += int(CATEGORY_FONT_SIZE * LINE_SPACING) * 2
        date_text = str(data_row['date'])
        block_lines.append((date_text, date_font, (34,34,34,255), None))
        block_height += int(DATE_FONT_SIZE * LINE_SPACING) * 2
        title_lines = wrap_text(str(data_row['title']), title_font, max_text_width, draw)
        for line in title_lines:
            block_lines.append((line, title_font, (0,60,200,255), None))
            block_height += int(TITLE_FONT_SIZE * LINE_SPACING)
        block_height += int(TITLE_FONT_SIZE * LINE_SPACING)
        summary_lines = wrap_text(str(data_row['card_summary']), summary_font, max_text_width, draw)
        for line in summary_lines:
            block_lines.append((line, summary_font, (34,34,34,255), None))
            block_height += int(SUMMARY_FONT_SIZE * LINE_SPACING)
        block_height += int(SUMMARY_FONT_SIZE * LINE_SPACING) * 2
        source_url = str(data_row['source_url'])
        block_lines.append((source_url, source_font, (120,120,120,255), None))
        block_height += int(SOURCE_FONT_SIZE * LINE_SPACING)
        news_blocks.append(block_lines)
        news_heights.append(block_height)
        total_height += block_height

    between_gap = SECTION_GAP * 2
    usable_height = CARD_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN
    # y값은 첫 뉴스의 카테고리 y좌표에서 시작
    y = category_y
    for block_idx, block_lines in enumerate(news_blocks):
        for text, font, fill, custom_y in block_lines:
            if custom_y is not None:
                y = custom_y
            draw_text_with_letter_spacing(draw, (LEFT_MARGIN, y), text, font, fill)
            y += int(font.size * LINE_SPACING)
        if block_idx == 0:
            y += between_gap

    out_path = os.path.join('news_card', f'news_card_{i//2+1:02d}.png')
    card.save(out_path)
    print(f"뉴스 카드 저장: {out_path}")
