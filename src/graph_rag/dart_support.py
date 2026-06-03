from __future__ import annotations

from loguru import logger

_DART_VALUE = "dart"
_registered = False


def _extend_str_enum(enum_cls: type, name: str, value: str):
    if name in enum_cls._member_map_:
        return enum_cls[name]
    member = str.__new__(enum_cls, value)
    member._name_ = name
    member._value_ = value
    enum_cls._member_map_[name] = member
    enum_cls._value2member_map_[value] = member
    enum_cls._member_names_.append(name)
    return member


def register_dart() -> bool:
    global _registered
    if _registered:
        return True

    try:
        import tree_sitter_language_pack as tslp
        from tree_sitter import Parser

        from codebase_rag import constants as cs
        from codebase_rag import language_spec as lspec
        from codebase_rag import parser_loader as pl
        from codebase_rag.models import LanguageSpec
    except Exception as e:
        logger.warning(f"Dart support unavailable (import failed): {e}")
        return False

    dart = _extend_str_enum(cs.SupportedLanguage, "DART", _DART_VALUE)

    dart_spec = LanguageSpec(
        language=dart,
        file_extensions=(".dart",),
        function_node_types=(
            "function_signature",
            "getter_signature",
            "setter_signature",
            "constructor_signature",
        ),
        class_node_types=(
            "class_definition",
            "mixin_declaration",
            "enum_declaration",
            "extension_declaration",
        ),
        module_node_types=("program",),
        call_node_types=(),
        import_node_types=(),
        import_from_node_types=(),
        name_field="name",
        body_field="body",
        package_indicators=("pubspec.yaml",),
    )
    lspec.LANGUAGE_SPECS[dart] = dart_spec
    lspec._EXTENSION_TO_SPEC[".dart"] = dart_spec

    dart_language = tslp.get_language(_DART_VALUE)
    pl.LANGUAGE_LIBRARIES[dart] = lambda: dart_language

    if not getattr(pl._process_language, "_dart_wrapped", False):
        _orig_process = pl._process_language

        def _process_language_with_dart(lang_name, lang_config, parsers, queries):
            if lang_name == dart:
                try:
                    parser = Parser(dart_language)
                    parsers[lang_name] = parser
                    queries[lang_name] = pl._create_language_queries(
                        dart_language, parser, lang_config, lang_name
                    )
                    logger.success("Dart grammar loaded")
                    return True
                except Exception as e:
                    logger.warning(f"Dart grammar load failed: {e}")
                    return False
            return _orig_process(lang_name, lang_config, parsers, queries)

        _process_language_with_dart._dart_wrapped = True
        pl._process_language = _process_language_with_dart

    _registered = True
    logger.info("Dart support registered (tree-sitter-language-pack)")
    return True
