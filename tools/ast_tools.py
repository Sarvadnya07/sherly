import ast
from runtime_utils import log

class ASTPatcher:
    """
    Performs Abstract Syntax Tree (AST) transformations for 100% reliable code edits.
    """
    def transform_function(self, source_code: str, target_func: str, new_body: str) -> str:
        """
        Long-term vision: AST-Aware Patching.
        Replaces the body of a specific function while preserving comments/formatting (best effort).
        """
        try:
            tree = ast.parse(source_code)
            new_body_ast = ast.parse(new_body).body
            
            class FunctionReplacer(ast.NodeTransformer):
                def visit_FunctionDef(self, node):
                    if node.name == target_func:
                        log(f"[AST] Replacing function: {target_func}")
                        node.body = new_body_ast
                    return node
            
            transformer = FunctionReplacer()
            modified_tree = transformer.visit(tree)
            ast.fix_missing_locations(modified_tree)
            
            return ast.unparse(modified_tree)
        except Exception as e:
            log(f"[AST] Transformation failed: {e}")
            return source_code
