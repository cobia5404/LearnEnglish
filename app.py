import streamlit as st
import re
import yaml
import random
import os
import tempfile
from gtts import gTTS
import base64
import hashlib
from streamlit_option_menu import option_menu

# テキスト正規化関数
def normalize_text(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

# YAMLファイルから教材データを読み込み
def load_lessons():
    with open('data.yaml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        return data['lessons']

lessons = load_lessons()

# セッション状態の初期化
if 'completed_lessons' not in st.session_state:
    st.session_state.completed_lessons = set()

if 'current_lesson' not in st.session_state:
    st.session_state.current_lesson = 0

# ---------------------------
# gTTSを使用した読み上げ関数（英語・日本語対応）
# ---------------------------
def text_to_speech(text, lang="en"):
    """
    gTTSを使用してテキストを音声に変換し、base64エンコードされたオーディオデータを返す
    """
    try:
        # 一時ファイルを作成
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_filename = fp.name

        # gTTSで音声を生成
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_filename)

        # 音声ファイルを読み込み
        with open(temp_filename, "rb") as audio_file:
            audio_data = audio_file.read()

        # 一時ファイルを削除
        os.unlink(temp_filename)

        # base64エンコード
        audio_base64 = base64.b64encode(audio_data).decode()

        return audio_base64
    except Exception as e:
        st.error(f"音声生成エラー: {e}")
        return None

def speak_text(text: str, lang="en", label="", key=None):
    """
    gTTSを使用した音声読み上げ機能（テキスト下に1つだけプレーヤー、ボタンなし、labelが空ならテキスト非表示）
    """
    lang_map = {
        "en-US": "en",
        "ja-JP": "ja"
    }
    gtts_lang = lang_map.get(lang, lang)
    if not text.strip():
        return
    if key is None:
        key = hashlib.md5((text+lang).encode()).hexdigest()
    # labelが空でなければテキスト表示
    if label:
        st.markdown(f"**{label}**")
    audio_base64 = text_to_speech(text, gtts_lang)
    if audio_base64:
        st.audio(f"data:audio/mp3;base64,{audio_base64}", format="audio/mp3")

# ---------------------------
# メインアプリケーション
# ---------------------------
st.markdown("### ✍️ 英文聞き取りトレーニング")

# 進捗表示
completed_count = len(st.session_state.completed_lessons)
total_count = len(lessons)
progress = completed_count / total_count if total_count > 0 else 0

st.sidebar.markdown("## 📊 学習進捗")
st.sidebar.progress(progress)
st.sidebar.markdown(f"完了: {completed_count} / {total_count} レッスン")

with st.sidebar:
    mode = option_menu(
        None,
        ["順番に学習", "ランダム出題"],
        icons=["list-ol", "shuffle"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#f8f9fa"},
            "icon": {"color": "#1976d2", "font-size": "20px"},
            "nav-link": {
                "font-size": "18px",
                "color": "#333",
                "text-align": "left",
                "margin": "4px 0",
                "border-radius": "6px",
            },
            "nav-link-selected": {
                "background-color": "#e6f0fa",
                "color": "#1976d2",
                "font-weight": "bold",
                "border": "2px solid #1976d2",
            },
        }
    )

if mode == "順番に学習":
    lesson_order = list(range(len(lessons)))
elif mode == "ランダム出題":
    if "random_order" not in st.session_state or len(st.session_state["random_order"]) != len(lessons):
        st.session_state["random_order"] = random.sample(range(len(lessons)), len(lessons))
    lesson_order = st.session_state["random_order"]
    st.sidebar.write("ランダム順:", lesson_order)  # デバッグ用

# current_lessonはlesson_orderに従って表示
lesson_index = int(st.session_state.current_lesson)
lesson = lessons[lesson_order[lesson_index]]

# ここから下は「段階的学習」モードのUI・ロジックを常に表示
st.markdown(f"#### 👂 英文聞き取り ({lesson_order[lesson_index] + 1} / {len(lessons)})")
speak_text(lesson['en'], lang="en-US", label="")

# グローバルな選択状態を使う
if "mode_choice_global" not in st.session_state:
    st.session_state["mode_choice_global"] = "全文タイピング"

st.markdown("<div style='font-size: 0.95em; color: #666; margin-bottom: 0.2em;'>出題方法を選択してください</div>", unsafe_allow_html=True)
mode_choice = option_menu(
    None,
    ["全文タイピング", "穴埋め"],
    icons=["keyboard", "list-ul"],
    menu_icon=None,
    orientation="horizontal",
    default_index=0 if st.session_state["mode_choice_global"] == "全文タイピング" else 1,
    styles={
        "container": {"padding": "0 100px !important", "background-color": "#fff0", "justify-content": "center", "gap": "0"},
        "icon": {"color": "#6c757d", "font-size": "18px"},
        "nav-link": {
            "font-size": "18px",
            "text-align": "center",
            "margin": "0 2px",
            "color": "#333",
            "background-color": "#fff0",
            "border": "1.5px solid #ddd",
            "border-radius": "6px",
            "padding": "4px 0",
            "width": "200px",
        },
        "nav-link-selected": {
            "background-color": "#e6f0fa",
            "color": "#1976d2",
            "border": "2px solid #1976d2",
        },
    }
)
st.session_state["mode_choice_global"] = mode_choice

# 3. ヒントボタン
if st.button("💡 ヒント(日本語訳)", key=f"hint_btn_{lesson_index}"):
    st.session_state[f"show_hint_{lesson_index}"] = True
if st.session_state.get(f"show_hint_{lesson_index}", False):
    st.info(f"日本語訳: {lesson['ja']}")

# 4. 問題出題
typing_correct = st.session_state.get(f"typing_correct_{lesson_index}", False)
gap_correct = st.session_state.get(f"gap_correct_{lesson_index}", False)

if mode_choice == "全文タイピング":
    st.markdown("#### ✍️ 全文タイピング")
    user_typing = st.text_area("英文を入力してください:", height=100, key=f"typing_practice_{lesson_index}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ タイピングチェック", key=f"typing_check_btn_{lesson_index}"):
            if normalize_text(user_typing) == normalize_text(lesson['en']):
                st.session_state[f"typing_correct_{lesson_index}"] = True
                st.success("🎉 正解です！")
            else:
                st.session_state[f"typing_correct_{lesson_index}"] = False
                st.error("❌ 間違いがあります。もう一度確認してください。")

    with col2:
        if st.button("😔 ギブアップ", key=f"typing_giveup_btn_{lesson_index}"):
            st.session_state[f"typing_giveup_{lesson_index}"] = True

    # ギブアップ時の正解表示
    if st.session_state.get(f"typing_giveup_{lesson_index}", False):
        st.info(f"💡 正解: {lesson['en']}")
        st.session_state[f"typing_correct_{lesson_index}"] = True  # ギブアップでも次の問題に進める
elif mode_choice == "穴埋め":
    st.markdown("#### 🎯 穴埋めテスト")
    template = lesson["en"]
    gaps = lesson["gaps"]
    for i, word in enumerate(gaps):
        template = template.replace(word, f"___({i+1})___")
    st.markdown(f"<div style='font-size: 1.5em; font-weight: bold;'>{template}</div>", unsafe_allow_html=True)
    gap_answers = []
    for i in range(len(gaps)):
        ans = st.text_input(f"{i+1}. 空欄に入る単語", key=f"gap_learning_{lesson_index}_{i}")
        gap_answers.append(ans.strip())

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 穴埋めチェック", key=f"check_gap_learning_{lesson_index}"):
            correct = 0
            for i, correct_word in enumerate(gaps):
                user_word = gap_answers[i].lower()
                if user_word == correct_word.lower():
                    st.success(f"{i+1}. 正解！({correct_word})")
                    correct += 1
                else:
                    st.error(f"{i+1}. 不正解 ❌")
            st.info(f"正解数：{correct} / {len(gaps)}")
            if correct == len(gaps):
                st.session_state[f"gap_correct_{lesson_index}"] = True
                st.success("🎉 全問正解です！")
            else:
                st.session_state[f"gap_correct_{lesson_index}"] = False

    with col2:
        if st.button("😔 ギブアップ", key=f"giveup_btn_{lesson_index}"):
            st.session_state[f"giveup_{lesson_index}"] = True

    # ギブアップ時の正解表示
    if st.session_state.get(f"giveup_{lesson_index}", False):
        st.info(f"💡 正解: {', '.join(gaps)}")
        st.session_state[f"gap_correct_{lesson_index}"] = True  # ギブアップでも次の問題に進める

# 5. どちらか合格で「次の問題へ」
if st.session_state.get(f"typing_correct_{lesson_index}", False) or st.session_state.get(f"gap_correct_{lesson_index}", False):
    if st.button("次の問題へ", key=f"next_{lesson_index}"):
        # 完了レッスンを記録
        st.session_state.completed_lessons.add(lesson_order[lesson_index])
        st.session_state.current_lesson = (lesson_index + 1) % len(lessons)
        # フラグリセット
        st.session_state[f"typing_correct_{lesson_index}"] = False
        st.session_state[f"gap_correct_{lesson_index}"] = False
        st.session_state[f"show_hint_{lesson_index}"] = False
        # 入力欄のリセットは削除（ウィジェットキーと競合するため）
        st.rerun()
