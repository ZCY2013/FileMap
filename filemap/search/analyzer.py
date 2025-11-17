"""中文分词器"""
from whoosh.analysis import Tokenizer, Token
from whoosh.analysis.analyzers import CompositeAnalyzer
from whoosh.analysis.filters import LowercaseFilter, StopFilter
import re


class ChineseTokenizer(Tokenizer):
    """中文分词器（基于jieba）"""

    def __init__(self):
        super().__init__()
        # 不存储jieba模块引用，每次使用时导入
        try:
            import jieba
            # 测试导入
        except ImportError:
            raise ImportError("jieba not installed. Install with: pip install jieba")

    def __call__(self, value, positions=False, chars=False, keeporiginal=False,
                 removestops=True, start_pos=0, start_char=0, mode='', **kwargs):
        """
        分词处理

        Args:
            value: 待分词文本
            positions: 是否记录位置
            chars: 是否记录字符位置
        """
        assert isinstance(value, str), f"Expected str, got {type(value)}"

        # 每次使用时导入jieba
        import jieba

        pos = start_pos
        for word in jieba.cut_for_search(value):
            token = Token()
            token.text = word
            token.pos = pos
            token.startchar = start_char
            token.endchar = start_char + len(word)

            yield token

            pos += 1
            start_char += len(word)


class ChineseAnalyzer(CompositeAnalyzer):
    """中文分析器（分词 + 小写 + 停用词）"""

    def __init__(self, stoplist=None):
        """
        初始化中文分析器

        Args:
            stoplist: 停用词列表
        """
        # 默认中文停用词
        if stoplist is None:
            stoplist = self._default_chinese_stopwords()

        tokenizer = ChineseTokenizer()
        filters = [
            LowercaseFilter(),
        ]

        if stoplist:
            filters.append(StopFilter(stoplist=frozenset(stoplist)))

        super().__init__(tokenizer, *filters)

    @staticmethod
    def _default_chinese_stopwords():
        """默认中文停用词"""
        return {
            '的', '了', '在', '是', '我', '有', '和', '就',
            '不', '人', '都', '一', '一个', '上', '也', '很',
            '到', '说', '要', '去', '你', '会', '着', '没有',
            '看', '好', '自己', '这', '那', '里', '来', '而',
            '为', '以', '与', '及', '或', '等', '之', '于',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on',
            'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as'
        }


def create_chinese_analyzer():
    """创建中文分析器实例"""
    return ChineseAnalyzer()
