"""自定义异常类"""


class FileMapError(Exception):
    """FileMap 基础异常类"""
    pass


class FileNotFoundError(FileMapError):
    """文件不存在异常"""
    pass


class FileAlreadyExistsError(FileMapError):
    """文件已存在异常"""
    pass


class TagNotFoundError(FileMapError):
    """标签不存在异常"""
    pass


class TagAlreadyExistsError(FileMapError):
    """标签已存在异常"""
    pass


class CategoryNotFoundError(FileMapError):
    """分类不存在异常"""
    pass


class CategoryAlreadyExistsError(FileMapError):
    """分类已存在异常"""
    pass


class InvalidPathError(FileMapError):
    """无效路径异常"""
    pass


class DatabaseError(FileMapError):
    """数据库错误异常"""
    pass


class IndexingError(FileMapError):
    """索引错误异常"""
    pass


class SearchError(FileMapError):
    """搜索错误异常"""
    pass


class ConfigurationError(FileMapError):
    """配置错误异常"""
    pass


class ValidationError(FileMapError):
    """验证错误异常"""
    pass
