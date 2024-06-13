import ast


def render(node: ast.AST) -> str:
    return ast.unparse(node)
