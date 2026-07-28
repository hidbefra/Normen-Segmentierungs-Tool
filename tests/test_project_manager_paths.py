from __future__ import annotations


from normen_tool.api.project_manager import _resolve_project_path


def test_resolve_project_path_corrects_duplicates_after_resolution(
    monkeypatch, tmp_path
):
    root = tmp_path / "Normen-Segmentierungs-Tool"
    nested_repo = root / "Normen-Segmentierungs-Tool"
    project_dir = root / "Mein_Normen_Projekt"

    nested_repo.mkdir(parents=True)
    project_dir.mkdir(parents=True)

    monkeypatch.chdir(nested_repo)

    resolved = _resolve_project_path("Mein_Normen_Projekt")
    assert resolved == project_dir.resolve()


def test_resolve_project_path_strips_wrapping_quotes(tmp_path):
    project_dir = tmp_path / "project"
    project_dir.mkdir(parents=True)

    resolved = _resolve_project_path(f'"{project_dir}"')
    assert resolved == project_dir.resolve()
