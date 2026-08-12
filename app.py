import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date

st.set_page_config(layout="wide")
st.title("🚀 復活のインターン検索システム")

keyword = st.text_input("キーワードを入力:", "インターン")

if st.button("検索開始"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    today = date.today().strftime("%Y/%m/%d")
    search_url = f"https://connpass.com/search/?q={keyword}&start_from={today}&sort=2"
    
    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        cards = soup.select('.event_list.vevent')
        
        if not cards:
            st.warning("イベントが見つかりませんでした。")
        else:
            events = []
            
            progress_text = "イベント詳細を収集中..."
            my_bar = st.progress(0, text=progress_text)
            
            for i, card in enumerate(cards):
                title_tag = card.select_one('.event_title a')
                if not title_tag:
                    continue
                    
                title = title_tag.get_text(strip=True)
                url = title_tag['href']
                
                # --- ここから詳細ページの取得エンジン ---
                d_res = requests.get(url, headers=headers)
                d_soup = BeautifulSoup(d_res.text, 'html.parser')
                
                # 1. 日時の取得（「開催日時」の隣のセルを探す）
                time_th = d_soup.find('th', string=lambda text: text and '開催日時' in text)
                if time_th and time_th.find_next_sibling('td'):
                    raw_time = time_th.find_next_sibling('td').get_text(separator=' ', strip=True)
                    # 「Googleカレンダー」などの余計なボタン文字をカット
                    event_time = raw_time.split('Google')[0].strip()
                else:
                    event_time = "不明"
                
                # 2. 場所の取得（「会場」の隣のセルを探す）
                venue_th = d_soup.find('th', string=lambda text: text and '会場' in text)
                if venue_th and venue_th.find_next_sibling('td'):
                    raw_location = venue_th.find_next_sibling('td').get_text(separator=' ', strip=True)
                    event_location = raw_location.split('マップで見る')[0].strip()
                else:
                    event_location = "未定 / オンラインなど"
                
                # 3. チケット内訳の取得
                ptypes = d_soup.select('.ptype')
                ticket_info = []
                for ptype in ptypes:
                    name = ptype.select_one('.ptype_name')
                    parts = ptype.select_one('.participants')
                    if name and parts:
                        ticket_info.append(f"{name.get_text(strip=True)}: {parts.get_text(strip=True)}")
                ticket_str = " / ".join(ticket_info) if ticket_info else "情報なし"
                
                # 表に追加
                events.append({
                    "日時": event_time,
                    "イベント名": title,
                    "場所": event_location,
                    "チケット": ticket_str,
                    "URL": url
                })
                
                # 進捗バーを更新
                my_bar.progress((i + 1) / len(cards), text=f"データ収集中... ({i+1}/{len(cards)}件完了)")
                
            # 完了したらバーを消してテーブルを表示
            my_bar.empty()
            st.table(pd.DataFrame(events))
            
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")