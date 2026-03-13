from langgraph.checkpoint.postgres import PostgresSaver

from src.config.config import Config

_checkpointer_resource = None
_checkpointer = None


def get_checkpointer():
    """懒加载 PostgreSQL checkpointer，兼容上下文管理器与直接实例两种返回。"""
    global _checkpointer_resource, _checkpointer

    if _checkpointer is not None:
        return _checkpointer

    resource = PostgresSaver.from_conn_string(Config.DATABASE_URL)
    _checkpointer_resource = resource

    if hasattr(resource, "__enter__"):
        _checkpointer = resource.__enter__()
    else:
        _checkpointer = resource

    return _checkpointer


def setup_checkpoint() -> None:
    """初始化 checkpoint 相关表（幂等）。"""
    checkpointer = get_checkpointer()
    checkpointer.setup()


def close_checkpoint() -> None:
    """释放 checkpointer 资源（如果底层支持）。"""
    global _checkpointer_resource, _checkpointer

    if _checkpointer_resource is not None and hasattr(
        _checkpointer_resource, "__exit__"
    ):
        _checkpointer_resource.__exit__(None, None, None)

    _checkpointer = None
    _checkpointer_resource = None
