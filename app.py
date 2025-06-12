import streamlit as st
import re
import yaml
import random
import os
import tempfile
from gtts import gTTS
import base64
import hashlib

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
st.title("✍️ 英文トレーニング")

# 進捗表示
completed_count = len(st.session_state.completed_lessons)
total_count = len(lessons)
progress = completed_count / total_count if total_count > 0 else 0

st.sidebar.markdown("## 📊 学習進捗")
st.sidebar.progress(progress)
st.sidebar.markdown(f"完了: {completed_count} / {total_count} レッスン")

# サイドバーでモード選択
mode = st.sidebar.selectbox(
    "学習モードを選択",
    ["📚 段階的学習", "🎯 穴埋めテスト", "🎲 ランダム学習"]
)

if mode == "📚 段階的学習":
    st.markdown("## 📚 段階的学習モード")
    st.markdown("英文を覚えるための段階的な学習を行います。")

    # レッスン選択
    if 'current_lesson' not in st.session_state:
        st.session_state.current_lesson = 0
    lesson_index = int(st.session_state.current_lesson)
    lesson = lessons[lesson_index]
    st.markdown(f"#### 例文番号（1〜）: {lesson_index + 1}")

    # ランダム選択ボタン
    if st.button("🎲 ランダム選択"):
        available_lessons = [i for i in range(len(lessons)) if i not in st.session_state.completed_lessons]
        if available_lessons:
            lesson_index = random.choice(available_lessons)
            st.session_state.current_lesson = lesson_index
            st.rerun()
        else:
            st.info("すべてのレッスンが完了しています！")

    # セッション状態の初期化
    if f"show_hint_{lesson_index}" not in st.session_state:
        st.session_state[f"show_hint_{lesson_index}"] = False
    if f"show_gap_{lesson_index}" not in st.session_state:
        st.session_state[f"show_gap_{lesson_index}"] = False
    if f"typing_checked_{lesson_index}" not in st.session_state:
        st.session_state[f"typing_checked_{lesson_index}"] = False
    if f"typing_correct_{lesson_index}" not in st.session_state:
        st.session_state[f"typing_correct_{lesson_index}"] = False

    if lesson_index in st.session_state.completed_lessons:
        st.success(f"✅ レッスン {lesson_index} は完了済みです")

    # ステップ1: 英文の音声のみ（テキスト非表示）
    st.markdown("### 📖 ステップ1: 英文を聞く")
    speak_text(lesson['en'], lang="en-US", label="")

    # ステップ2: 日本語ヒント＋タイピング練習
    st.markdown("### 💡 ステップ2: 日本語ヒント & タイピング練習")
    st.info(f"日本語訳: {lesson['ja']}")
    user_typing = st.text_area("英文を入力してください:", height=100, key=f"typing_practice_{lesson_index}")
    if st.button("✅ タイピングチェック", key=f"typing_check_btn_{lesson_index}"):
        st.session_state[f"typing_checked_{lesson_index}"] = True
        if normalize_text(user_typing) == normalize_text(lesson['en']):
            st.session_state[f"typing_correct_{lesson_index}"] = True
        else:
            st.session_state[f"typing_correct_{lesson_index}"] = False

    if st.session_state[f"typing_checked_{lesson_index}"]:
        if st.session_state[f"typing_correct_{lesson_index}"]:
            st.success("🎉 完璧です！正しく入力できました！")
            st.session_state.completed_lessons.add(lesson_index)
            if st.button("次の問題へ", key=f"next_lesson_{lesson_index}"):
                # セッションフラグをリセット
                st.session_state[f"show_gap_{lesson_index}"] = False
                st.session_state[f"giveup_{lesson_index}"] = False
                st.session_state[f"typing_checked_{lesson_index}"] = False
                st.session_state[f"typing_correct_{lesson_index}"] = False
                # 入力欄のリセットはしない（エラー回避のため）
                st.session_state.current_lesson = (lesson_index + 1) % len(lessons)
                st.rerun()
        else:
            st.error("❌ 間違いがあります。もう一度確認してください。")
            # 正解は表示しない
            if st.button("▶️ 穴埋めに進む", key=f"to_gap_{lesson_index}"):
                st.session_state[f"show_gap_{lesson_index}"] = True

    # ステップ3: 穴埋めテスト（フラグがTrueのときのみ表示）
    if st.session_state[f"show_gap_{lesson_index}"]:
        st.markdown("### 🎯 ステップ3: 穴埋めテスト")
        template = lesson["en"]
        gaps = lesson["gaps"]
        for i, word in enumerate(gaps):
            template = template.replace(word, f"___({i+1})___")
        st.markdown(f"**穴埋め英文:** {template}")
        for i in range(len(gaps)):
            st.text_input(f"{i+1}. 空欄に入る単語", key=f"gap_learning_{lesson_index}_{i}")
        if f"giveup_{lesson_index}" not in st.session_state:
            st.session_state[f"giveup_{lesson_index}"] = False
        if st.button("✅ 穴埋めチェック", key=f"check_gap_learning_{lesson_index}"):
            user_answers = [
                st.session_state.get(f"gap_learning_{lesson_index}_{i}", "").strip()
                for i in range(len(gaps))
            ]
            correct = 0
            for i, correct_word in enumerate(gaps):
                user_word = user_answers[i].lower()
                if user_word == correct_word.lower():
                    st.success(f"{i+1}. 正解！({correct_word})")
                    correct += 1
                else:
                    st.error(f"{i+1}. 不正解 ❌")
            st.info(f"正解数：{correct} / {len(gaps)}")
            if correct == len(gaps):
                st.success("🎉 おめでとうございます！このレッスンを完了しました！")
                st.session_state.completed_lessons.add(lesson_index)
                if st.button("次の問題へ", key=f"next_lesson_gap_{lesson_index}"):
                    # セッションフラグをリセット
                    st.session_state[f"show_gap_{lesson_index}"] = False
                    st.session_state[f"giveup_{lesson_index}"] = False
                    st.session_state[f"typing_checked_{lesson_index}"] = False
                    st.session_state[f"typing_correct_{lesson_index}"] = False
                    st.session_state.current_lesson = (lesson_index + 1) % len(lessons)
                    st.rerun()
        # ギブアップボタン
        if st.button("ギブアップ（正解を表示）", key=f"giveup_btn_{lesson_index}"):
            st.session_state[f"giveup_{lesson_index}"] = True
        if st.session_state[f"giveup_{lesson_index}"]:
            st.info(f"正解: {', '.join(gaps)}")
            # 「次の問題へ」ボタンを表示
            if st.button("次の問題へ", key=f"next_lesson_giveup_{lesson_index}"):
                st.session_state.completed_lessons.add(lesson_index)
                st.session_state[f"show_gap_{lesson_index}"] = False
                st.session_state[f"giveup_{lesson_index}"] = False
                st.session_state[f"typing_checked_{lesson_index}"] = False
                st.session_state[f"typing_correct_{lesson_index}"] = False
                st.session_state.current_lesson = (lesson_index + 1) % len(lessons)
                st.rerun()

elif mode == "🎯 穴埋めテスト":
    st.markdown("## 🎯 穴埋めテストモード")
    st.markdown("直接穴埋めテストを行います。")

    # 例文番号（1〜）で表示
    lesson_no = st.number_input("例文番号（1〜）", 1, len(lessons), 1)
    lesson_index = lesson_no - 1
    lesson = lessons[lesson_index]

    # start_gap_test_{lesson_index} を必ず初期化
    if f"start_gap_test_{lesson_index}" not in st.session_state:
        st.session_state[f"start_gap_test_{lesson_index}"] = False

    st.markdown("### 🇯🇵 和訳：")
    speak_text(lesson["ja"], lang="ja-JP", label="和訳")

    # 穴埋め表示
    template = lesson["en"]
    gaps = lesson["gaps"]
    for i, word in enumerate(gaps):
        template = template.replace(word, f"___({i+1})___")

    st.markdown("### ✍️ 穴埋め英文：")
    st.markdown(template)

    # 入力欄
    user_answers = []
    for i in range(len(gaps)):
        ans = st.text_input(f"{i+1}. 空欄に入る単語", key=f"gap_test_{i}")
        user_answers.append(ans.strip())

    # チェックボタン
    if st.button("✅ チェック"):
        correct = 0
        for i, correct_word in enumerate(gaps):
            user_word = user_answers[i].lower()
            if user_word == correct_word.lower():
                st.success(f"{i+1}. 正解！({correct_word})")
                correct += 1
            else:
                st.error(f"{i+1}. 不正解 ❌（正解: {correct_word}）")
        st.info(f"正解数：{correct} / {len(gaps)}")

    # ヒント表示
    if st.button("💡 ヒントを表示"):
        for i, gap in enumerate(gaps):
            st.write(f"{i+1}. ヒント：{gap[0]}...")

    # 答え表示＋読み上げ
    if st.button("👁 正解をすべて表示"):
        st.markdown("### ✅ 正解英文：")
        speak_text(lesson["en"], lang="en-US", label="正解英文")

else:  # ランダム学習モード
    st.markdown("## 🎲 ランダム学習モード")
    st.markdown("ランダムにレッスンを選択して学習します。")

    # 未完了のレッスンからランダム選択
    available_lessons = [i for i in range(len(lessons)) if i not in st.session_state.completed_lessons]

    if available_lessons:
        if 'random_lesson' not in st.session_state:
            st.session_state.random_lesson = random.choice(available_lessons)

        lesson_index = st.session_state.random_lesson
        lesson = lessons[lesson_index]

        st.markdown(f"**選択されたレッスン: {lesson_index}**")

        # 簡潔な学習フロー
        st.markdown("### 📖 英文")
        speak_text(lesson['en'], lang="en-US", label="英文")

        st.markdown("### 🇯🇵 日本語訳")
        speak_text(lesson['ja'], lang="ja-JP", label="日本語訳")

        # 穴埋めテスト
        st.markdown("### 🎯 穴埋めテスト")
        template = lesson["en"]
        gaps = lesson["gaps"]
        for i, word in enumerate(gaps):
            template = template.replace(word, f"___({i+1})___")

        st.markdown(f"**穴埋め英文:** {template}")

        user_answers = []
        for i in range(len(gaps)):
            ans = st.text_input(f"{i+1}. 空欄に入る単語", key=f"gap_random_{i}")
            user_answers.append(ans.strip())

        if st.button("✅ チェック"):
            correct = 0
            for i, correct_word in enumerate(gaps):
                user_word = user_answers[i].lower()
                if user_word == correct_word.lower():
                    st.success(f"{i+1}. 正解！({correct_word})")
                    correct += 1
                else:
                    st.error(f"{i+1}. 不正解 ❌（正解: {correct_word}）")
            st.info(f"正解数：{correct} / {len(gaps)}")

            if correct == len(gaps):
                # st.balloons()  # 風船演出を削除
                st.success("🎉 おめでとうございます！このレッスンを完了しました！")
                st.session_state.completed_lessons.add(lesson_index)
                if st.button("次の問題へ", key=f"next_lesson_{lesson_index}"):
                    st.rerun()

        # 次のランダムレッスン
        if st.button("🎲 次のランダムレッスン"):
            st.session_state.random_lesson = random.choice(available_lessons)
            st.rerun()

    else:
        st.success("🎉 すべてのレッスンが完了しています！お疲れ様でした！")
        if st.button("🔄 進捗をリセット"):
            st.session_state.completed_lessons = set()
            st.rerun()
