import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# 画面を広く使うために layout="wide" に変更
st.set_page_config(page_title="Indie Gem Finder A/B", layout="wide")

# ==========================================
# 1. データの読み込み
# ==========================================
@st.cache_data
def load_data():
    return pd.read_csv('recommendation_base.csv')

df_base = load_data()

# ==========================================
# 🧠 セッションステートの初期化（AとBを完全に分ける）
# ==========================================
for side in ['A', 'B']:
    if f'current_idx_{side}' not in st.session_state:
        st.session_state[f'current_idx_{side}'] = 0
        st.session_state[f'keep_list_{side}'] = []
        # 初期値：左(A)はタグ重視、右(B)はポエム重視
        st.session_state[f'last_weight_{side}'] = 0.7 if side == 'A' else 0.3

# ==========================================
# 2. UIの構築（ヘッダー部分）
# ==========================================
st.title("⚖️ 究極のA/Bテスト：デュアル・ディグ画面")
st.markdown("左右で異なるAIブレンドを設定し、どちらのアルゴリズムがあなたの直感に刺さるか直接対決させましょう！")

# 画面を左右に真っ二つに割る
colA, colB = st.columns(2)

# ==========================================
# 3. 左右それぞれのUIを描画する関数
# ==========================================
def render_deck(side, col):
    with col:
        st.header(f"🤖 モデル {side}")
        
        # 🎛️ 個別のスライダー
        current_weight = st.session_state[f'last_weight_{side}']
        weight_tags = st.slider(f"タグ(客観) ↔ ポエム(情熱) [{side}]", 
                                min_value=0.0, max_value=1.0, value=current_weight, step=0.1, key=f"slider_{side}")
        weight_about = 1.0 - weight_tags
        st.caption(f"比率: タグ {weight_tags*100:.0f}% / ポエム {weight_about*100:.0f}%")

        # スライダーが動かされたら、そのデッキの進捗をリセット
        if st.session_state[f'last_weight_{side}'] != weight_tags:
            st.session_state[f'current_idx_{side}'] = 0
            st.session_state[f'last_weight_{side}'] = weight_tags

        # 🚀 リアルタイム計算
        df_base[f'final_score_{side}'] = (df_base['sim_tags'] * weight_tags) + (df_base['sim_about'] * weight_about)
        df_deck = df_base.sort_values(f'final_score_{side}', ascending=False).head(20).reset_index(drop=True)
        total_games = len(df_deck)

        idx = st.session_state[f'current_idx_{side}']

        # 🏁 すべて見終わった場合（リザルト画面）
        if idx >= total_games:
            st.success(f"🎉 モデル {side} のディグり完了！")
            if len(st.session_state[f'keep_list_{side}']) > 0:
                keep_df = pd.DataFrame(st.session_state[f'keep_list_{side}'])
                st.dataframe(keep_df[['name', f'final_score_{side}', 'rating_ratio']], hide_index=True)
            else:
                st.info("キープした原石はありませんでした。")
            
            if st.button(f"🔄 モデル {side} をやり直す", key=f"reset_{side}", use_container_width=True):
                st.session_state[f'current_idx_{side}'] = 0
                st.session_state[f'keep_list_{side}'] = []
                st.rerun()
            return # ここで描画終了

        # 🃏 カードの表示
        current_game = df_deck.iloc[idx]
        appid = int(current_game["appid"])

        st.write("---")
        img_url = f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg"
        movie_urls = str(current_game.get('movies', '')).split(',')
        video_url = movie_urls[0] if movie_urls and movie_urls[0].startswith('http') else ""

        if video_url:
            html_code = f"""
            <div style="width: 100%; border-radius: 8px; overflow: hidden; background: #000;">
                <video src="{video_url}" poster="{img_url}" loop muted playsinline
                       onmouseover="this.play()" onmouseout="this.pause(); this.currentTime = 0;" 
                       style="width: 100%; display: block; cursor: pointer;">
                </video>
            </div>
            """
            components.html(html_code, height=200)
        else:
            st.image(img_url, use_container_width=True)

        st.subheader(f"{current_game['name']}")
        
        c1, c2 = st.columns(2)
        c1.metric(label="🤖 マッチ度", value=f"{current_game[f'final_score_{side}'] * 100:.1f}%")
        c2.metric(label="👍 好評率", value=f"{current_game['rating_ratio'] * 100:.1f}%")

        st.caption(f"**🏷️ タグ:** {current_game['tags']}")
        st.write(f"🔗 [Steamストアで詳細を見る（ブラウザが開きます）](https://store.steampowered.com/app/{appid}/)")
        
        # 👇 ==========================================
        # 🆔 コピー用のAppID表示を追加！
        # ==========================================
        st.write("▼ ナシ判定用コピーボタン")
        st.code(appid, language="text")
        st.write("---")

        # 👆 仕分けボタン
        b1, b2 = st.columns(2)
        with b1:
            if st.button("❌ ナシ", key=f"skip_{side}", use_container_width=True):
                st.session_state[f'current_idx_{side}'] += 1
                st.rerun()
        with b2:
            if st.button("❤️ アリ", key=f"keep_{side}", type="primary", use_container_width=True):
                st.session_state[f'keep_list_{side}'].append(current_game.to_dict())
                st.session_state[f'current_idx_{side}'] += 1
                st.rerun()

        st.progress((idx) / total_games, text=f"進行度: {idx + 1} / {total_games} 件")

# ==========================================
# 4. 関数を呼び出して左右の画面を生成
# ==========================================
render_deck('A', colA)
render_deck('B', colB)