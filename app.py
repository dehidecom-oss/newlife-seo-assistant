import streamlit as st
from google import genai

# =========================
# 基本設定
# =========================
st.set_page_config(
    page_title="Newlife SEOアシスタント β版",
    page_icon="📝",
    layout="wide"
)

MAX_CHARS = 10000

# =========================
# デザイン
# =========================
st.markdown("""
<style>
.main-title {
    font-size: 2.4rem;
    font-weight: 800;
    margin-bottom: 0.2rem;
    color: #14532d;
}
.sub-title {
    color: #4b5563;
    font-size: 1.05rem;
    margin-bottom: 1.5rem;
}
.notice-box {
    background: #f0fdf4;
    border-left: 6px solid #22c55e;
    padding: 1rem 1.2rem;
    border-radius: 10px;
    margin-bottom: 1.2rem;
    color: #14532d;
    font-weight: 500;
}
.small-note {
    color: #6b7280;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)


# =========================
# パスワード認証
# =========================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.markdown('<div class="main-title">Newlife SEOアシスタント β版</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Newlifeメンバー専用のAI記事チェックツールです。</div>',
        unsafe_allow_html=True
    )

    password = st.text_input("メンバー専用パスワードを入力してください", type="password")

    if st.button("ログイン"):
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("パスワードが違います。")

    return False


if not check_password():
    st.stop()


# =========================
# サイドバー
# =========================
with st.sidebar:
    st.title("使い方")

    st.write("""
    1. 狙っているキーワードを入力  
    2. 記事の目的を選択  
    3. ブログ歴を選択  
    4. 記事本文を貼り付け  
    5. 「添削する」をクリック  
    """)

    st.divider()

    st.subheader("使うタイミング")
    st.write("""
    記事を書いた後、公開前のセルフチェックとして使ってください。  
    AIの指摘を見て修正してから、必要に応じて質問・添削依頼してください。
    """)

    st.divider()

    st.subheader("利用上の注意")
    st.markdown("""
    <div style="color: #dc2626; font-weight: 700; line-height: 1.7;">
    ・β版のため、まずは1日1〜3回を目安にご利用ください。<br>
    ・たくさん使いたい方向けには、後日Newlife記事添削Gem版を案内予定です。
    </div>
    """, unsafe_allow_html=True)
    st.info("""
    このツールは、上位表示を狙うために、検索意図・構成・読者満足の観点から改善ポイントをチェックするものです。  
    記事を自動で完成させるものではありません。
    """)

    
    st.warning("""
    ・AIによる一次チェックです。最終判断は、実際の検索結果・読者の悩み・ご自身の体験談をもとに行ってください。  
    ・個人情報、ログイン情報、外部に共有したくない情報は入力しないでください。  
    ・入力内容や添削結果は、このアプリ側では保存しません。ただし、AIによる処理のため、入力内容はGemini APIに送信されます。
    """)




# =========================
# メイン画面
# =========================
st.markdown('<div class="main-title">Newlife SEOアシスタント β版</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">まずは「記事添削機能」からβ公開しています。キーワードと記事本文を入力すると、検索意図・構成・読者満足・収益導線の観点からAIが改善ポイントをチェックします。</div>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="notice-box">
<strong>おすすめの使い方：</strong><br>
記事を書いたあとに、公開前のセルフチェックとして使ってください。<br>
AIで改善点を確認してから修正すると、質問や添削依頼の質も上がります。
</div>
""", unsafe_allow_html=True)

keyword = st.text_input(
    "この記事で狙うキーワード",
    placeholder="例：財布持たない 不便"
)

purpose = st.selectbox(
    "記事の目的",
    [
        "アドセンス収益（集客記事）",
        "アフィリエイト成約（成約記事）",
        "関連記事への内部リンク誘導",
        "自分の商品・サービス販売",
        "その他"
    ]
)

blog_level = st.radio(
    "ブログ歴",
    [
        "初心者（記事作成にまだ慣れていない）",
        "3ヶ月以上（基本は理解している）",
        "1年以上（ある程度記事を書いている）"
    ],
    horizontal=True
)

article = st.text_area(
    "記事本文を貼り付けてください",
    height=350,
    placeholder="ここに記事本文を貼り付けてください"
)

char_count = len(article)
st.caption(f"現在の文字数：{char_count}文字 / 上限：{MAX_CHARS}文字")

if char_count > MAX_CHARS:
    st.error("β版では1回あたり10,000文字までです。長い記事は、前半・後半に分けてチェックしてください。")


# =========================
# プロンプト作成
# =========================
def build_prompt(keyword, purpose, blog_level, article):
    return f"""
あなたはNewlifeのSEO記事添削アシスタントです。
初心者〜中級者のブロガーの記事を、Newlife講師が動画添削で話すような、やさしく具体的な口調で添削してください。

【重要な口調】
・最初に「記事作成、お疲れ様でした。」と入れてください。
・まず良い点を認めてから、改善点を伝えてください。
・断定しすぎず、「〜かなと思います」「〜すると良いと思います」を自然に使ってください。
・過度にテンションの高い表現や、営業っぽい表現は避けてください。
・初心者が次に何をすればいいかまで、具体的に落とし込んでください。
・ただし、曖昧に褒めるだけではなく、直すべき点は具体的に伝えてください。

【入力情報】
狙うキーワード：
{keyword}

記事の目的：
{purpose}

ブログ歴：
{blog_level}

記事本文：
{article}

【前提】
想定読者が明示されていない場合は、キーワードと本文から推定してください。

【添削で見る観点】
1. 検索意図に答えられているか
2. 検索意図に対して、冒頭で早く答えているか
3. 読者が知りたい順番で構成されているか
4. タイトルと見出しに狙ったキーワードが自然に入っているか
5. 個人ブログが勝てる切り口になっているか
6. 企業サイトのような一般論だけになっていないか
7. 体験談、失敗談、具体例を入れる余地があるか
8. 読者の不安や疑問に先回りできているか
9. 内部リンクで読者の次の悩みに誘導できるか
10. 記事の目的に合った導線になっているか

【記事目的ごとの重視点】
・アドセンス収益（集客記事）の場合：
読者満足、情報のわかりやすさ、滞在時間、関連記事への回遊を重視してください。

・アフィリエイト成約（成約記事）の場合：
購入前の不安、比較ポイント、デメリット、口コミ・体験談、自然な背中押しを重視してください。

・関連記事への内部リンク誘導の場合：
読者が次に知りたいこと、自然な文脈での内部リンク導線を重視してください。

・自分の商品・サービス販売の場合：
読者の悩み、信頼形成、押し売りにならない導線、申し込み前の不安解消を重視してください。

【出力の長さ】
出力は長くなりすぎないようにしてください。
各項目は具体的に書きつつ、初心者が読み切れる分量にしてください。

目安：
・良い点は3つまで
・まず直すべきポイントは3つまで
・追加見出しは3〜5個程度
・タイトル案は3つ
・次にやることチェックリストは5個以内

【出力形式】
以下の形式で、Markdownで出力してください。

# 総合評価
100点満点の点数を出してください。
ただし、低い点数の場合でも否定的に言い切らず、
「方向性は良い」「ここを直せば改善できる」のように、
次の行動につながる前向きな補足を必ず入れてください。

# この記事の良いところ
良い点を3つ以内で書いてください。

# まず直すべき3つ
優先度が高い順に、理由と修正案をセットで3つ以内で書いてください。

# 検索意図とのズレ
想定読者を推定したうえで、今の記事が検索意図に対して足りている点・足りない点を書いてください。

# 追加した方がいい内容・見出し
H2/H3形式で、追加候補を3〜5個程度提案してください。

# タイトル改善案
狙うキーワードを自然に含めたタイトル案を3つ出してください。

# 冒頭文の改善案
そのまま使える文章で、短めに書いてください。

# 内部リンク・収益導線の提案
記事の目的に合わせて、自然な導線案を提案してください。

# 次にやることチェックリスト
初心者でも行動しやすいように、5個以内で書いてください。
"""


# =========================
# Gemini実行
# =========================
if st.button("添削する", type="primary"):
    if not keyword.strip():
        st.error("狙うキーワードを入力してください。")
        st.stop()

    if not article.strip():
        st.error("記事本文を入力してください。")
        st.stop()

    if len(article) > MAX_CHARS:
        st.error("β版では1回あたり10,000文字までです。長い記事は、前半・後半に分けてチェックしてください。")
        st.stop()

    with st.spinner("AIが記事をチェックしています..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
            prompt = build_prompt(keyword, purpose, blog_level, article)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            st.success("添削が完了しました。")
            st.markdown(response.text)

        except Exception as e:
            error_text = str(e)

            if "503" in error_text or "UNAVAILABLE" in error_text or "high demand" in error_text:
                st.error("現在AIが混雑しているため、添削できませんでした。少し時間をおいて、もう一度お試しください。")
            elif "API_KEY" in error_text or "api key" in error_text.lower():
                st.error("AIの設定に問題がある可能性があります。管理者にご連絡ください。")
            else:
                st.error("エラーが発生しました。時間をおいて再度お試しください。解決しない場合は管理者にご連絡ください。")