import logging
from groq import Groq

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """
    Groq API (Llama 3.1) を使用して、会話の文脈から攻撃性や皮肉を判定するクラス。
    """
    def __init__(self, api_key: str, model_name: str = "llama-3.1-8b-instant"):
        if not api_key:
            raise ValueError("GROQ_API_KEY を指定する必要があります。")
        
        self.api_key = api_key
        self.model_name = model_name
        
        self.client = Groq(api_key=self.api_key)
        logger.info(f"SentimentAnalyzerを初期化しました (Model: {self.model_name})")

    def analyze_context(self, current_author: str, current_message: str, history: list[dict]) -> bool:
        """
        現在のメッセージと会話履歴をLLMに渡し、低速モードが必要なほど
        雰囲気が悪化しているか（攻撃性、煽り、皮肉など）を判定する。
        """
        # プロンプトの構築（履歴＋最新メッセージを同じ形式で繋げる）
        context_str = ""
        for msg in history:
            context_str += f"{msg['author']}: {msg['content']}\n"
        context_str += f"{current_author}: {current_message}"

        system_prompt = (
            "あなたはDiscordコミュニティの秩序を守る高度なモデレーターAIです。\n"
            "与えられた会話の流れを分析し、最新のメッセージに対して「低速モードを適用して冷却期間を設けるべきか」を判定してください。\n"
            "\n"
            "【判定基準：YES（低速モードが必要）】\n"
            "- 相手を不快にさせることを目的とした、執拗な皮肉や煽り\n"
            "- 特定の個人やグループに対する直接的な攻撃・暴言\n"
            "- 会話の文脈を無視した一方的な非難や、議論を破壊するような過度に攻撃的な態度\n"
            "- このまま放置すると喧嘩や激しい対立に発展することが確実視される状況\n"
            "\n"
            "【判定基準：NO（低速モードは不要）】\n"
            "- 強い言葉を使っていても、建設的な議論や個人の意見表明の範囲内である場合\n"
            "- 単なる冗談や、親しい間柄での軽いからかい（文脈から判断）\n"
            "- 意見の相違はあるが、対話が成立している場合\n"
            "- 感情的ではあるが、他者への攻撃性は低い場合\n"
            "\n"
            "【回答ルール】\n"
            "迷った場合は 'NO' と判定し、表現の自由を尊重してください。\n"
            "理由などは一切書かず、必ず 'YES' か 'NO' の一言だけで答えてください。"
        )

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"分析対象の会話：\n{context_str}"}
                ],
                model=self.model_name,
                temperature=0.0, # 安定した判定のため
                max_tokens=5
            )
            
            answer = chat_completion.choices[0].message.content.strip().upper()
            logger.debug(f"LLM判定結果: {answer} (Context: {context_str[:50]}...)")
            
            return "YES" in answer
        except Exception as e:
            logger.error(f"Groq APIリクエスト中にエラーが発生しました: {e}")
            return False

