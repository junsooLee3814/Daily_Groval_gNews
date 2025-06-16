import os
import subprocess
from datetime import datetime
import shutil

durations = [2] + [4] + [4]*10 + [3]*9 + [5]*4 + [5]
WIDTH, HEIGHT = 1080, 1920
now_str = datetime.now().strftime('%Y%m%d_%H%M%S')

INTRO_IMG_PATH = os.path.join('assets', 'intro_news.png')
INTRO_OUT_PATH = os.path.join('news_video', f'intro_news_{now_str}.mp4')
SINGLE_DIR = os.path.join('news_video', 'single')
COMBINE_OUT_PATH = os.path.join('news_video', 'merged_news.mp4')
FINAL_OUT_PATH = os.path.join('news_video', 'merged_news_bgm.mp4')
BGM_PATH = os.path.join('assets', 'bgm.mp3')

# 0. 인트로 영상 생성

def make_intro_video(img_path, out_path, duration):
    if os.path.exists(img_path):
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_path,
            "-t", str(duration),
            "-vf", f"zoompan=z='min(zoom+0.0015,1.1)':d={duration*25}:s={WIDTH}x{HEIGHT}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path
        ]
        print("[인트로] " + " ".join(cmd))
        subprocess.run(cmd, check=True)
        print(f"[인트로] 인트로 영상 저장 완료: {out_path}")
        return out_path
    print("[인트로] intro_news.png 파일이 없어 인트로 영상 생략")
    return None

# 1. 카드별 뉴스 이미지 → mp4 생성

def make_card_videos(durations, now_str):
    video_paths = []
    os.makedirs(SINGLE_DIR, exist_ok=True)
    for idx, duration in enumerate(durations):
        img_path = os.path.join('news_card', f'news_card_{idx+1:02d}.png')
        out_path = os.path.join(SINGLE_DIR, f'card_{idx+1:02d}_{now_str}.mp4')
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", img_path,
            "-t", str(duration),
            "-vf", f"zoompan=z='min(zoom+0.0015,1.1)':d={duration*25}:s={WIDTH}x{HEIGHT}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", out_path
        ]
        print("[카드] " + " ".join(cmd))
        subprocess.run(cmd, check=True)
        print(f"[카드 {idx+1}] 뉴스 카드 영상 저장 완료: {out_path}")
        video_paths.append(out_path)
    return video_paths

# 2. 카드별 mp4 합치기 (ffmpeg concat)
def merge_videos_ffmpeg(video_paths, out_path):
    with open("video_list.txt", "w", encoding="utf-8") as f:
        for v in video_paths:
            abs_path = os.path.abspath(v).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", "video_list.txt",
        "-c", "copy",
        out_path
    ]
    subprocess.run(cmd, check=True)
    os.remove("video_list.txt")
    print(f"[합친 뉴스 카드 영상 저장 완료] {out_path}")

# 3. 배경음악 삽입 (페이드인 1초, 페이드아웃 2초)
def add_bgm_to_video(video_path, bgm_path, out_path, total_duration):
    cmd_bgm = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter:a", f"volume=0.5,afade=t=in:st=0:d=1,afade=t=out:st={total_duration-2}:d=2",
        "-shortest",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        out_path
    ]
    subprocess.run(cmd_bgm, check=True)
    print(f"[배경음악 합친 뉴스 카드 영상 저장 완료] {out_path}")

# 4. 중간 파일/폴더 삭제
def clean_temp_news_videos(single_dir, combine_out_path, intro_out_path=None):
    # single 폴더 삭제
    if os.path.exists(single_dir):
        for f in os.listdir(single_dir):
            try:
                os.remove(os.path.join(single_dir, f))
            except Exception as e:
                print(f"[삭제 실패] {os.path.join(single_dir, f)}: {e}")
        try:
            shutil.rmtree(single_dir)
        except Exception as e:
            print(f"[폴더 삭제 실패] {single_dir}: {e}")
    # merged_news.mp4 삭제
    if os.path.exists(combine_out_path):
        try:
            os.remove(combine_out_path)
        except Exception as e:
            print(f"[삭제 실패] {combine_out_path}: {e}")
    # 인트로 mp4 삭제
    if intro_out_path and os.path.exists(intro_out_path):
        try:
            os.remove(intro_out_path)
        except Exception as e:
            print(f"[인트로 삭제 실패] {intro_out_path}: {e}")
    # 00combine 폴더 삭제(혹시 남아있으면)
    combine_dir = os.path.join('news_video', '00combine')
    if os.path.exists(combine_dir):
        try:
            shutil.rmtree(combine_dir)
        except Exception as e:
            print(f"[폴더 삭제 실패] {combine_dir}: {e}")
    print(f"[정리 완료] 최종 파일만 남김: {FINAL_OUT_PATH}")

if __name__ == "__main__":
    intro_duration = durations[0]
    card_durations = durations[1:]
    intro_out_path = make_intro_video(INTRO_IMG_PATH, INTRO_OUT_PATH, intro_duration)
    card_video_paths = make_card_videos(card_durations, now_str)
    video_paths = ([intro_out_path] if intro_out_path else []) + card_video_paths
    merge_videos_ffmpeg(video_paths, COMBINE_OUT_PATH)
    total_duration = sum(durations)
    add_bgm_to_video(COMBINE_OUT_PATH, BGM_PATH, FINAL_OUT_PATH, total_duration)
    clean_temp_news_videos(SINGLE_DIR, COMBINE_OUT_PATH, intro_out_path) 