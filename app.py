import streamlit as st
import re
import yaml

# YAMLファイルから教材データを読み込み
def load_lessons():
    with open('data.yaml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        return data['lessons']

lessons = load_lessons()

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
# UI表示
# ---------------------------
st.title("✍️ 英作文トレーニング + 🔊 読み上げ")

lesson_index = st.number_input("例文番号（0〜）", 0, len(lessons)-1, 0)
lesson = lessons[lesson_index]

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
    ans = st.text_input(f"{i+1}. 空欄に入る単語", key=f"gap{i}")
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
