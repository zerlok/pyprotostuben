import typing as t

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorResponse

from tests.integration.cases.case import Case


def test_file_content_matches(case: Case) -> None:
    response = case.generator.run(case.request)
    assert _join_contents(response.file) == _join_contents(case.gen_expected_files)


def _join_contents(files: t.Sequence[CodeGeneratorResponse.File]) -> str:
    return "\n".join(
        f"""#\n# response file: "{file.name}"\n#\n{file.content}""" for file in sorted(files, key=lambda f: f.name)
    )
