import streamlit as st
import re
import yaml
import random

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
# 読み上げ関数（英語・日本語対応）
# ---------------------------
def speak_text(text: str, lang="en-US"):
    segments = re.split(r'(?<=[。．！？!?]|[.?!])\s*|\n+', text)
    segments = [seg.strip() for seg in segments if seg.strip()]
    js_array = "[" + ", ".join([f'"{s}"' for s in segments]) + "]"

    st.components.v1.html(f"""
        <script>
        const segments = {js_array};
        let index = 0;
        function speakSegment() {{
            if (index >= segments.length) return;
            const utterance = new SpeechSynthesisUtterance(segments[index]);
            utterance.lang = "{lang}";
            utterance.onend = () => {{
                index++;
                speakSegment();
            }};
            speechSynthesis.speak(utterance);
        }}
        function speakAll() {{
            index = 0;
            speakSegment();
        }}
        </script>
        <button onclick="speakAll()">🔊 読み上げ（{lang}）</button>
    """, height=40)

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
    col1, col2 = st.columns([3, 1])
    with col1:
        # 例文番号（1〜）で表示
        lesson_no = st.number_input("例文番号（1〜）", 1, len(lessons), 1)
        lesson_index = lesson_no - 1
    with col2:
        if st.button("🎲 ランダム選択"):
            available_lessons = [i for i in range(len(lessons)) if i not in st.session_state.completed_lessons]
            if available_lessons:
                lesson_index = random.choice(available_lessons)
                st.session_state.current_lesson = lesson_index
                st.rerun()
            else:
                st.info("すべてのレッスンが完了しています！")

    lesson = lessons[lesson_index]

    # start_gap_test_{lesson_index} を必ず初期化
    if f"start_gap_test_{lesson_index}" not in st.session_state:
        st.session_state[f"start_gap_test_{lesson_index}"] = False

    # 完了状態の表示
    if lesson_index in st.session_state.completed_lessons:
        st.success(f"✅ レッスン {lesson_index} は完了済みです")

    # ステップ1: 英文表示（音声ボタンは常に表示）
    st.markdown("### 📖 ステップ1: 英文を確認")
    if not st.session_state[f"start_gap_test_{lesson_index}"]:
        st.markdown(f"**英文:** {lesson['en']}")
    speak_text(lesson['en'], lang="en-US")

    # ステップ2・3は穴埋めテスト開始前のみ表示
    if not st.session_state[f"start_gap_test_{lesson_index}"]:
        # ステップ2: 日本語訳表示
        st.markdown("### 🇯🇵 ステップ2: 日本語訳を確認")
        st.markdown(f"**日本語訳:** {lesson['ja']}")
        speak_text(lesson['ja'], lang="ja-JP")

        # ステップ3: タイピング練習
        st.markdown("### ⌨️ ステップ3: タイピング練習")
        st.markdown("英文を入力して覚えましょう。")
        user_typing = st.text_area("英文を入力してください:", height=100, key="typing_practice")
        typing_correct = False
        if st.button("✅ タイピングチェック"):
            if normalize_text(user_typing) == normalize_text(lesson['en']):
                st.success("🎉 完璧です！正しく入力できました！")
                typing_correct = True
            else:
                st.error("❌ 間違いがあります。もう一度確認してください。")
                st.markdown(f"**正解:** {lesson['en']}")

    # 穴埋めテスト開始フラグ
    if f"start_gap_test_{lesson_index}" not in st.session_state:
        st.session_state[f"start_gap_test_{lesson_index}"] = False

    if not st.session_state[f"start_gap_test_{lesson_index}"]:
        if st.button("▶️ 穴埋めテストを始める", key=f"start_gap_test_btn_{lesson_index}"):
            st.session_state[f"start_gap_test_{lesson_index}"] = True
            st.rerun()

    # ステップ4: 穴埋めテスト（開始フラグがTrueのときのみ表示）
    if st.session_state[f"start_gap_test_{lesson_index}"]:
        st.markdown("### 🎯 ステップ4: 穴埋めテスト")
        template = lesson["en"]
        gaps = lesson["gaps"]
        for i, word in enumerate(gaps):
            template = template.replace(word, f"___({i+1})___")
        st.markdown(f"**穴埋め英文:** {template}")
        for i in range(len(gaps)):
            st.text_input(f"{i+1}. 空欄に入る単語", key=f"gap_learning_{lesson_index}_{i}")
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
                    st.error(f"{i+1}. 不正解 ❌（正解: {correct_word}）")
            st.info(f"正解数：{correct} / {len(gaps)}")
            if correct == len(gaps):
                st.success("🎉 おめでとうございます！このレッスンを完了しました！")
                st.session_state.completed_lessons.add(lesson_index)
                if st.button("次の問題へ", key=f"next_lesson_{lesson_index}"):
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
    st.markdown(lesson["ja"])
    speak_text(lesson["ja"], lang="ja-JP")

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
        st.markdown(lesson["en"])
        speak_text(lesson["en"], lang="en-US")

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
        st.markdown(lesson['en'])
        speak_text(lesson['en'], lang="en-US")

        st.markdown("### 🇯🇵 日本語訳")
        st.markdown(lesson['ja'])

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
