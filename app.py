import streamlit as st
from google import genai
from google.genai import types

# =========================
# 基本設定
# =========================
st.set_page_config(
    page_title="Newlife SEOアシスタント β版",
    page_icon="📝",
    layout="wide"
)

MAX_CHARS = 10000
GEMINI_MODEL = "gemini-2.5-flash"
PURPOSE_OPTIONS = [
    "アドセンス収益（集客記事）",
    "アフィリエイト成約（成約記事）",
    "関連記事への内部リンク誘導",
    "自分の商品・サービス販売",
    "その他",
]
BLOG_LEVEL_OPTIONS = [
    "初心者（記事作成にまだ慣れていない）",
    "3ヶ月以上（基本は理解している）",
    "1年以上（ある程度記事を書いている）",
]
TARGET_LENGTH_OPTIONS = [3500, 5000, 8000]

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
        '<div class="sub-title">Newlifeメンバー専用のAI記事作成・チェックツールです。</div>',
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


def init_session_state():
    defaults = {
        "mode": "記事作成",
        "outline": "",
        "draft_article": "",
        "review_article": "",
        "create_keyword": "",
        "review_keyword": "",
        "create_purpose": PURPOSE_OPTIONS[0],
        "review_purpose": PURPOSE_OPTIONS[0],
        "create_blog_level": BLOG_LEVEL_OPTIONS[0],
        "review_blog_level": BLOG_LEVEL_OPTIONS[0],
        "flash_success": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def consume_flash_success():
    message = st.session_state.get("flash_success", "")
    if message:
        st.success(message)
        st.session_state.flash_success = ""


def purpose_weight_text():
    return """
【記事目的ごとの重視点】
・アドセンス収益（集客記事）の場合：
読者満足、情報のわかりやすさ、滞在時間、関連記事への回遊を重視してください。

・アフィリエイト成約（成約記事）の場合：
購入前の不安、比較ポイント、デメリット、口コミ・体験談、自然な背中押しを重視してください。

・関連記事への内部リンク誘導の場合：
読者が次に知りたいこと、自然な文脈での内部リンク導線を重視してください。

・自分の商品・サービス販売の場合：
読者の悩み、信頼形成、押し売りにならない導線、申し込み前の不安解消を重視してください。
"""


def build_review_prompt(keyword, purpose, blog_level, article):
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

{purpose_weight_text()}

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


def build_serp_research_prompt(keyword, purpose, notes):
    notes_block = notes.strip() if notes.strip() else "（特になし）"
    return f"""
あなたはSEOリサーチャーです。Google検索でキーワード「{keyword}」の現在の上位記事を調べ、構成設計用の調査メモを作ってください。
必ずGoogle検索ツールを使い、実際の検索結果に基づいて書いてください。

【記事の目的】
{purpose}

【独自の切り口・伝えたいこと（任意）】
{notes_block}

【調査してまとめること】
1. 想定される検索意図（知りたいこと／不安／次にしたい行動）
2. 上位記事（目安5〜10件）で共通して書かれているトピック・見出し傾向
3. 上位記事ごとの主なカバー内容（タイトルと要点）
4. 上位では弱い／欠けている視点（個人ブログが足せる差別化）
5. 検索意図に対して、構成に必ず入れるべき答え

【出力形式】
調査メモのみをMarkdownで出力してください。挨拶や励ましは不要です。
"""


def build_outline_prompt(keyword, purpose, blog_level, notes, target_length, serp_research):
    notes_block = notes.strip() if notes.strip() else "（特になし）"
    return f"""
あなたはSEO記事の構成設計者です。
下の「上位記事調査メモ」を使って、狙うキーワードの記事構成案だけを作成してください。

【構成づくりのルール】
1. 上位記事で重複して書かれている重要トピックは、構成に含める
2. そのうえで、個人ブログならではのプラスアルファ（体験・具体例・判断基準・失敗回避など）を見出しで足す
3. 先に検索意図を整理し、調査メモの答え合わせ結果を反映して構成をブラッシュアップする
4. 読者が迷わず本文を書ける具体性にする（各見出しに書く要点を箇条書き）

【入力情報】
狙うキーワード：
{keyword}

記事の目的：
{purpose}

ブログ歴：
{blog_level}

独自の切り口・伝えたいこと（任意）：
{notes_block}

目標文字数（本文）：
約{target_length}文字

【上位記事調査メモ】
{serp_research}

{purpose_weight_text()}

【構成案に含める項目】
1. 想定読者
2. 検索意図（知りたいこと／不安／次にしたい行動）
3. タイトル案を3つ（狙うキーワードを自然に含める）
4. 推奨タイトル（1つ選ぶ）
5. H2/H3の見出し構成
6. 各見出しで書く要点（箇条書き）
7. 冒頭で先に答える結論の一文案
8. 内部リンク・収益導線を置く位置の提案
9. 体験談を入れるべき箇所（本文では捏造禁止なので「要追記」と明記）

【禁止（重要）】
・構成案以外の文章を一切書かない
・挨拶・導入トーク・励まし・締めの応援文は禁止
・「構成案を作っていきましょう」「参考にして書いてみてください」「応援しています」などの会話文は禁止
・Newlife、講師、添削、アシスタントなど運営・メタ言及は禁止
・架空の体験談や口コミを事実として書かない
・薬機法・景表法に触れやすい断定表現の指示をしない

【出力形式】
構成案のMarkdownのみ。次の見出し順で出力してください。前置き・後書きは不要です。

# 想定読者
# 検索意図
# タイトル案
# 推奨タイトル
# 見出し構成と書く要点
# 冒頭の結論案
# 内部リンク・収益導線
# 体験談を追記すべき箇所
"""


def build_draft_prompt(keyword, purpose, blog_level, notes, target_length, outline):
    notes_block = notes.strip() if notes.strip() else "（特になし）"
    return f"""
あなたはブログ記事の執筆者です。
確定した構成案に厳密に沿って、一般読者向けの完成稿寄りのブログ記事本文だけを書いてください。

【文体】
・です・ます調の通常のブログ記事
・結論先行（冒頭で検索意図の中心に答える）
・一般論だけで終わらせず、比較軸・向き不向き・注意点・具体例を入れる
・過度にテンションの高い表現や、営業っぽい煽りは避ける
・読者に直接語りかける自然な文章にする

【入力情報】
狙うキーワード：
{keyword}

記事の目的：
{purpose}

ブログ歴：
{blog_level}

独自の切り口・伝えたいこと（任意）：
{notes_block}

目標文字数：
約{target_length}文字（前後15%程度まで可。極端に短くしない）

確定構成案：
{outline}

{purpose_weight_text()}

【厳守】
1. 確定構成案の見出し順・意図を守る（勝手に大幅省略しない）
2. 狙うキーワードをタイトル・見出し・本文に自然に入れる（詰め込み禁止）
3. 架空の一人称体験談・架空の口コミ・捏造データは絶対に書かない
4. 体験が必要な箇所は、次のマーカーを本文中に残す：
   `[体験談を追記：ここにご自身の実体験・失敗談・感想を書いてください]`
5. 健康・美容・収益保証などに触れる場合は断定せず、「個人差があります」「〜と言われています」など慎重な表現にする
6. 記事の目的に合った導線を自然に入れる（押し売りしない）

【絶対に書いてはいけない文言】
・Newlife、講師、添削、アシスタント、動画添削などの運営・メタ言及
・「お伝えしていきます」「一緒に見ていきましょう」「解説していきます」など講師口調のメタ文
・構成案の説明、前置き、後書き、応援メッセージ
・「以下が本文です」などの注釈

【出力形式】
・ブログ記事本文のMarkdownのみ
・最初にタイトル（# タイトル）
・その後に導入文とH2/H3本文
"""


def show_gemini_error(e, action_label="処理"):
    error_text = str(e)
    if "503" in error_text or "UNAVAILABLE" in error_text or "high demand" in error_text.lower():
        st.error(f"現在AIが混雑しているため、{action_label}できませんでした。少し時間をおいて、もう一度お試しください。")
    elif "API_KEY" in error_text or "api key" in error_text.lower():
        st.error("AIの設定に問題がある可能性があります。管理者にご連絡ください。")
    else:
        st.error(f"エラーが発生しました。時間をおいて再度お試しください。解決しない場合は管理者にご連絡ください。")


def generate_content(prompt, use_google_search=False):
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    config = None
    if use_google_search:
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=config
    )
    return response.text


def create_outline_with_serp_research(keyword, purpose, blog_level, notes, target_length):
    """上位記事調査（内部）→ 構成案のみ生成。"""
    research_prompt = build_serp_research_prompt(keyword, purpose, notes)
    try:
        serp_research = generate_content(research_prompt, use_google_search=True)
    except Exception:
        # 検索ツールが使えない場合は、検索なしで調査メモを作って継続する
        fallback_prompt = research_prompt + """

【補足】
Google検索ツールが使えない場合は、一般的に想定される上位記事の傾向として調査メモを作成してください。
その場合、冒頭に「※検索ツール未使用の推定メモ」と明記してください。
"""
        serp_research = generate_content(fallback_prompt, use_google_search=False)

    outline_prompt = build_outline_prompt(
        keyword, purpose, blog_level, notes, target_length, serp_research
    )
    outline_text = generate_content(outline_prompt, use_google_search=False)
    return outline_text, serp_research


def render_sidebar(mode):
    with st.sidebar:
        st.title("使い方")

        if mode == "記事作成":
            st.write("""
            1. 狙っているキーワードを入力  
            2. 記事の目的・ブログ歴を選択  
            3. （任意）独自の切り口を入力  
            4. 「構成案を作る」をクリック（内部で上位記事も確認）  
            5. 構成を確認・編集する  
            6. 「この構成で本文を書く」をクリック  
            """)
            st.divider()
            st.subheader("使うタイミング")
            st.write("""
            記事をゼロから書くときの下書き作成に使ってください。  
            できあがった本文は、必ずご自身の体験談を追記し、公開前に「記事添削」でチェックしてください。
            """)
            st.divider()
            st.subheader("利用上の注意")
            st.markdown("""
            <div style="color: #dc2626; font-weight: 700; line-height: 1.7;">
            ・β版のため、まずは1日1〜3回を目安にご利用ください。<br>
            ・たくさん使いたい方向けには、後日Newlife記事添削Gem版を案内予定です。<br>
            ・AI本文は下書きです。架空の体験談は入れません。ご自身の体験を追記してください。
            </div>
            """, unsafe_allow_html=True)
            st.info("""
            このツールは、検索意図に沿った構成と本文の下書きを作るものです。  
            そのまま公開する完成品ではありません。
            """)
        else:
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
        ・AIによる一次サポートです。最終判断は、実際の検索結果・読者の悩み・ご自身の体験談をもとに行ってください。  
        ・個人情報、ログイン情報、外部に共有したくない情報は入力しないでください。  
        ・入力内容や生成結果は、このアプリ側では保存しません。ただし、AIによる処理のため、入力内容はGemini APIに送信されます。
        """)


def render_create_mode():
    st.markdown(
        '<div class="sub-title">キーワードから構成案をつくり、確認後に完成稿寄りの本文を生成します。体験談はご自身で追記し、公開前は「記事添削」でチェックしてください。</div>',
        unsafe_allow_html=True
    )
    st.markdown("""
    <div class="notice-box">
    <strong>おすすめの使い方：</strong><br>
    ①構成案を作る → ②見出しを自分用に直す → ③本文を書く → ④体験談を追記 → ⑤記事添削で最終チェック
    </div>
    """, unsafe_allow_html=True)

    consume_flash_success()

    keyword = st.text_input(
        "この記事で狙うキーワード",
        key="create_keyword",
        placeholder="例：横浜 ランチ おすすめ"
    )
    purpose = st.selectbox(
        "記事の目的",
        PURPOSE_OPTIONS,
        key="create_purpose"
    )
    blog_level = st.radio(
        "ブログ歴",
        BLOG_LEVEL_OPTIONS,
        horizontal=True,
        key="create_blog_level"
    )
    notes = st.text_area(
        "独自の切り口・伝えたいこと（任意）",
        height=100,
        key="create_notes",
        placeholder="例：子連れでも入りやすい店だけ紹介したい／失敗談を中心に書きたい"
    )
    target_length = st.selectbox(
        "目標文字数",
        TARGET_LENGTH_OPTIONS,
        index=1,
        format_func=lambda n: f"約{n:,}文字",
        key="create_target_length"
    )

    if st.button("構成案を作る", type="primary"):
        if not keyword.strip():
            st.error("狙うキーワードを入力してください。")
        else:
            with st.spinner("上位記事を調べて構成案を作成しています..."):
                try:
                    outline_text, _serp_research = create_outline_with_serp_research(
                        keyword, purpose, blog_level, notes, target_length
                    )
                    st.session_state.outline = outline_text
                    st.session_state.outline_editor = outline_text
                    st.session_state.draft_article = ""
                    st.session_state.flash_success = (
                        "構成案ができました。内容を確認・編集してから本文を書いてください。"
                    )
                    st.rerun()
                except Exception as e:
                    show_gemini_error(e, "構成案の作成")

    consume_flash_success()

    if st.session_state.outline:
        st.subheader("構成案（編集できます）")
        if "outline_editor" not in st.session_state:
            st.session_state.outline_editor = st.session_state.outline

        edited_outline = st.text_area(
            "構成案",
            height=420,
            key="outline_editor",
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            write_clicked = st.button("この構成で本文を書く", type="primary")
        with col2:
            clear_clicked = st.button("構成案をクリア")

        if clear_clicked:
            st.session_state.outline = ""
            st.session_state.draft_article = ""
            if "outline_editor" in st.session_state:
                del st.session_state.outline_editor
            if "draft_copy_area" in st.session_state:
                del st.session_state.draft_copy_area
            st.rerun()

        if write_clicked:
            if not edited_outline.strip():
                st.error("構成案が空です。先に構成案を作るか、内容を入力してください。")
            else:
                st.session_state.outline = edited_outline
                with st.spinner("AIが本文を書いています。完成稿寄りのため少し時間がかかります..."):
                    try:
                        prompt = build_draft_prompt(
                            keyword,
                            purpose,
                            blog_level,
                            notes,
                            target_length,
                            edited_outline
                        )
                        draft = generate_content(prompt)
                        st.session_state.draft_article = draft
                        st.session_state.draft_copy_area = draft
                        st.session_state.flash_success = (
                            "本文ができました。体験談マーカーを自分の体験に置き換えてから公開してください。"
                        )
                        st.rerun()
                    except Exception as e:
                        show_gemini_error(e, "本文の作成")

    if st.session_state.draft_article:
        st.subheader("生成された本文")
        st.caption(f"文字数：{len(st.session_state.draft_article):,}文字")
        st.markdown(st.session_state.draft_article)
        if "draft_copy_area" not in st.session_state:
            st.session_state.draft_copy_area = st.session_state.draft_article
        st.text_area(
            "コピー用本文",
            height=280,
            key="draft_copy_area"
        )

        if st.button("この本文を記事添削へ渡す"):
            st.session_state.review_article = st.session_state.draft_article
            st.session_state.review_keyword = st.session_state.create_keyword
            st.session_state.review_purpose = st.session_state.create_purpose
            st.session_state.review_blog_level = st.session_state.create_blog_level
            st.session_state.mode = "記事添削"
            st.rerun()


def render_review_mode():
    st.markdown(
        '<div class="sub-title">キーワードと記事本文を入力すると、検索意図・構成・読者満足・収益導線の観点からAIが改善ポイントをチェックします。</div>',
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
        key="review_keyword",
        placeholder="例：横浜 ランチ おすすめ"
    )
    purpose = st.selectbox(
        "記事の目的",
        PURPOSE_OPTIONS,
        key="review_purpose"
    )
    blog_level = st.radio(
        "ブログ歴",
        BLOG_LEVEL_OPTIONS,
        horizontal=True,
        key="review_blog_level"
    )
    article = st.text_area(
        "記事本文を貼り付けてください",
        height=350,
        key="review_article",
        placeholder="ここに記事本文を貼り付けてください"
    )

    char_count = len(article)
    st.caption(f"現在の文字数：{char_count}文字 / 上限：{MAX_CHARS}文字")

    if char_count > MAX_CHARS:
        st.error("β版では1回あたり10,000文字までです。長い記事は、前半・後半に分けてチェックしてください。")

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
                prompt = build_review_prompt(keyword, purpose, blog_level, article)
                result = generate_content(prompt)
                st.success("添削が完了しました。")
                st.markdown(result)
            except Exception as e:
                show_gemini_error(e, "添削")


# =========================
# アプリ本体
# =========================
if not check_password():
    st.stop()

init_session_state()

st.markdown('<div class="main-title">Newlife SEOアシスタント β版</div>', unsafe_allow_html=True)

mode = st.radio(
    "モード",
    ["記事作成", "記事添削"],
    horizontal=True,
    key="mode"
)

render_sidebar(mode)

if mode == "記事作成":
    render_create_mode()
else:
    render_review_mode()
