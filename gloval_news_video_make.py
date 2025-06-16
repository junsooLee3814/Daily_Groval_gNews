import subprocess

if __name__ == "__main__":
    print("[1/3] 뉴스 수집 및 요약 시작...")
    subprocess.run(["python", "Step1_News_Collection.py"], check=True)
    print("[2/3] 뉴스 카드 이미지 생성...")
    subprocess.run(["python", "step3_1_news_card_product.py"], check=True)
    print("[3/3] 뉴스 카드 영상 생성 및 합치기...")
    subprocess.run(["python", "step4_1_news_video_.py"], check=True)
    print("\n[완료] 뉴스 카드 영상 자동화가 모두 끝났습니다!") 