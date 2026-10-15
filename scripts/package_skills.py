#!/usr/bin/env python3
"""Build one portable Agent Skills ZIP per skill using only the standard library."""

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


def package_skills(source: Path, destination: Path) -> list[Path]:
    skills = sorted(path.parent for path in source.glob('*/SKILL.md'))
    if not skills:
        raise ValueError(f'No skills found in {source}')
    source = source.resolve()
    destination = destination.resolve()
    if destination == source or source in destination.parents:
        raise ValueError('Output directory must be outside the skills directory')
    destination.mkdir(parents=True, exist_ok=True)
    archives = []
    for skill in skills:
        files = sorted(path for path in skill.rglob('*') if path.is_file())
        if any(path.is_symlink() or not path.resolve().is_relative_to(skill.resolve()) for path in files):
            raise ValueError(f'Skill contains a symlink or external file: {skill.name}')
        archive = destination / f'{skill.name}.zip'
        with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as bundle:
            for path in files:
                relative = path.relative_to(skill.parent).as_posix()
                info = ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                bundle.writestr(info, path.read_bytes())
        with ZipFile(archive) as bundle:
            if bundle.testzip() is not None:
                raise ValueError(f'Corrupt archive: {archive}')
        archives.append(archive)
    return archives


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=root / 'dist')
    args = parser.parse_args()
    for output in package_skills(root / 'skills', args.output_dir):
        print(output)
