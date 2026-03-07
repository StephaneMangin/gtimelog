#!/usr/bin/env python3

import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

# ── Thresholds ──────────────────────────────────────────────────────────────
MAX_COMPLEXITY_GRADE = 'C'  # per-function ceiling (A=1-5, B=6-10, C=11-15)
MAX_AVG_GRADE = 'A'  # project-wide average ceiling
COVERAGE_MIN = 40  # percent
BAR_WIDTH = 50  # chars for ASCII bars

GRADE_ORDER = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5}
GRADE_LABELS = {
    'A': 'simple',
    'B': 'well structured',
    'C': 'slightly complex',
    'D': 'more complex',
    'E': 'high complexity',
    'F': 'very high complexity',
}


def _tool_cmd(name):
    """Return the command prefix to invoke a Python tool (radon, coverage, …).

    Prefers the tool binary on PATH (works inside a venv).  Falls back
    to ``sys.executable -m <name>`` when the binary isn't found.
    """
    path = shutil.which(name)
    if path:
        return [path]
    return [sys.executable, '-m', name]


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr, result.returncode


def bar(value, max_val, width=BAR_WIDTH, char='█'):
    filled = int(value / max(max_val, 1) * width)
    return char * filled + '░' * (width - filled)


# ═══════════════════════════════════════════════════════════════════════════
#  1. Cyclomatic Complexity (radon)
# ═══════════════════════════════════════════════════════════════════════════
def complexity_report():
    print('═' * 72)
    print('  CYCLOMATIC COMPLEXITY REPORT  (radon cc)')
    print('═' * 72)

    stdout, stderr, rc = run([*_tool_cmd('radon'), 'cc', 'src/', '-s', '-a', '-nc'])
    if rc != 0 and not stdout:
        print(f'  radon failed (rc={rc}): {stderr.strip()}')
        return False

    lines = stdout.strip().splitlines()
    grades = Counter()
    hotspots = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith(('src/', 'Average')):
            continue
        # Lines look like: "    M 42:4 method_name - B (8)"
        parts = line.split()
        if len(parts) >= 3 and parts[-1].endswith(')'):
            grade = parts[-2].strip('(')
            if grade in GRADE_ORDER:
                grades[grade] += 1
                if GRADE_ORDER.get(grade, 0) >= GRADE_ORDER.get('C', 2):
                    hotspots.append(line.strip())

    total = sum(grades.values()) or 1
    print()
    print('  Grade distribution:')
    print()
    for grade in ('A', 'B', 'C', 'D', 'E', 'F'):
        count = grades.get(grade, 0)
        pct = count / total * 100
        label = GRADE_LABELS.get(grade, '')
        marker = ' ◄── ceiling' if grade == MAX_COMPLEXITY_GRADE else ''
        print(f'    {grade} ({label:>18s})  {bar(count, total)} {count:4d} ({pct:5.1f}%){marker}')
    print()

    # Average line from radon
    avg_line = [ln for ln in lines if 'Average' in ln]
    if avg_line:
        print(f'  {avg_line[0].strip()}')
    print()

    # Hotspots (C and above)
    if hotspots:
        print(f'  ⚠  {len(hotspots)} function(s) at grade C or worse:')
        print()
        for h in hotspots[:15]:
            print(f'    ✗ {h}')
        if len(hotspots) > 15:
            print(f'    … and {len(hotspots) - 15} more')
        print()

    has_violations = any(
        GRADE_ORDER.get(g, 0) > GRADE_ORDER.get(MAX_COMPLEXITY_GRADE, 2) for g in grades if grades[g] > 0
    )
    if has_violations:
        print('  ✗ FAIL — functions above grade C detected')
    else:
        print('  ✓ PASS — no function exceeds grade C')

    return not has_violations


# ═══════════════════════════════════════════════════════════════════════════
#  2. Maintainability Index (radon mi)
# ═══════════════════════════════════════════════════════════════════════════
def maintainability_report():
    print()
    print('═' * 72)
    print('  MAINTAINABILITY INDEX  (radon mi)')
    print('═' * 72)

    stdout, _, rc = run([*_tool_cmd('radon'), 'mi', 'src/', '-s', '-n', 'B'])
    if rc != 0 and not stdout:
        print('  radon mi failed')
        return True  # non-blocking
    lines = [ln.strip() for ln in stdout.strip().splitlines() if ln.strip()]
    if not lines:
        print()
        print('  ✓ All modules rated A (very maintainable)')
        return True

    print()
    print('  Modules rated B or worse (mi < 20):')
    print()
    for line in lines[:20]:
        print(f'    {line}')
    if len(lines) > 20:
        print(f'    … and {len(lines) - 20} more')
    print()
    return True  # informational, not a gate


# ═══════════════════════════════════════════════════════════════════════════
#  3. Dead Code Detection (vulture)
# ═══════════════════════════════════════════════════════════════════════════
VULTURE_MIN_CONFIDENCE = 80


def dead_code_report():
    print()
    print('═' * 72)
    print(f'  DEAD CODE DETECTION  (vulture ≥{VULTURE_MIN_CONFIDENCE}% confidence)')
    print('═' * 72)

    stdout, _stderr, _rc = run(
        [
            *_tool_cmd('vulture'),
            'src/gtimelog',
            'vulture_whitelist.py',
            '--min-confidence',
            str(VULTURE_MIN_CONFIDENCE),
        ]
    )

    lines = [ln.strip() for ln in stdout.strip().splitlines() if ln.strip()]
    if not lines:
        print()
        print('  ✓ PASS — no dead code detected')
        return True

    print()
    print(f'  ⚠  {len(lines)} dead code finding(s):')
    print()
    for line in lines[:20]:
        short = line.replace('src/gtimelog/', '')
        print(f'    ✗ {short}')
    if len(lines) > 20:
        print(f'    … and {len(lines) - 20} more')
    print()
    print(f'  ✗ FAIL — {len(lines)} unused code finding(s)')
    print('  (i) Add false positives to vulture_whitelist.py')
    return False


# ═══════════════════════════════════════════════════════════════════════════
#  4. Coverage quick-report
# ═══════════════════════════════════════════════════════════════════════════
def _extract_coverage_pct(stdout, stderr):
    """Parse the TOTAL coverage percentage from coverage report output."""
    import contextlib

    for line in (stdout + stderr).splitlines():
        if 'TOTAL' in line and '%' in line:
            for part in reversed(line.split()):
                if part.endswith('%'):
                    with contextlib.suppress(ValueError):
                        return float(part.rstrip('%'))
    return None


def _extract_uncovered_modules(stdout):
    """Return list of (module, pct) for modules below 50% coverage."""
    import contextlib

    uncovered = []
    for line in stdout.splitlines():
        if '%' not in line or 'TOTAL' in line or '---' in line or not line.strip():
            continue
        parts = line.split()
        for part in reversed(parts):
            if part.endswith('%'):
                with contextlib.suppress(ValueError):
                    pct = float(part.rstrip('%'))
                    if pct < 50:
                        uncovered.append((parts[0], pct))
                break
    return sorted(uncovered, key=lambda x: x[1])


def coverage_report():
    print()
    print('═' * 72)
    print(f'  TEST COVERAGE  (minimum: {COVERAGE_MIN}%)')
    print('═' * 72)

    run(
        [
            *_tool_cmd('coverage'),
            'run',
            '--source=src/gtimelog',
            '--branch',
            '--omit=*/tests/*,*/__pycache__/*,*/locale/*,*/i18n/*,*/data/*',
            '-m',
            'pytest',
            '--override-ini=addopts=--doctest-modules',
            '-q',
            '--tb=no',
        ]
    )
    stdout, stderr, rc = run(
        [
            *_tool_cmd('coverage'),
            'report',
            f'--fail-under={COVERAGE_MIN}',
            '--skip-covered',
        ]
    )

    cov_pct = _extract_coverage_pct(stdout, stderr)
    if cov_pct is not None:
        print()
        filled = int(cov_pct / 100 * BAR_WIDTH)
        threshold_pos = int(COVERAGE_MIN / 100 * BAR_WIDTH)
        bar_str = '█' * filled + '░' * (BAR_WIDTH - filled)
        bar_list = list(bar_str)
        if threshold_pos < len(bar_list):
            bar_list[threshold_pos] = '│'
        bar_str = ''.join(bar_list)

        status = '✓' if cov_pct >= COVERAGE_MIN else '✗'
        print(f'  {status} Coverage: {bar_str} {cov_pct:.1f}%')
        print(f'              {"":>{threshold_pos}}▲ {COVERAGE_MIN}% minimum')
        print()
    else:
        print()
        print('  Could not parse coverage percentage')
        print()

    uncovered = _extract_uncovered_modules(stdout)
    if uncovered:
        print('  Lowest-coverage modules (< 50%):')
        print()
        for mod, pct in uncovered[:10]:
            short = mod.replace('src/gtimelog/', '')
            b = bar(pct, 100, width=30)
            print(f'    {b} {pct:5.1f}%  {short}')
        if len(uncovered) > 10:
            print(f'    … and {len(uncovered) - 10} more')
        print()

    passed = rc == 0
    if passed:
        print(f'  ✓ PASS — coverage ≥ {COVERAGE_MIN}%')
    else:
        print(f'  ✗ FAIL — coverage below {COVERAGE_MIN}%')
    return passed


# ═══════════════════════════════════════════════════════════════════════════
#  5. Addon Dependency Graph
# ═══════════════════════════════════════════════════════════════════════════
def _load_addon_dependencies():
    """Parse all addon manifests and return dependency graph."""
    addons_dir = Path('src/gtimelog/addons')
    graph = {}

    for manifest_path in sorted(addons_dir.glob('*/__manifest__.py')):
        addon = manifest_path.parent.name
        try:
            with open(manifest_path) as f:
                manifest = eval(f.read())
            graph[addon] = {
                'name': manifest.get('name', addon),
                'depends': manifest.get('depends', []),
                'version': manifest.get('version', '?'),
            }
        except Exception as e:
            graph[addon] = {'name': addon, 'depends': [], 'version': '?', 'error': str(e)}

    return graph


def _get_dependency_levels(graph):
    """Organize addons into levels based on dependency depth."""
    levels = []
    remaining = set(graph.keys())
    processed = set()

    while remaining:
        # Find addons with all dependencies satisfied
        current_level = []
        for addon in sorted(remaining):
            deps = set(graph[addon]['depends'])
            if deps.issubset(processed):
                current_level.append(addon)

        if not current_level:
            # Circular dependency or error - add remaining to last level
            current_level = sorted(remaining)

        levels.append(current_level)
        processed.update(current_level)
        remaining -= set(current_level)

    return levels


def _draw_addon_box(name, width=16):
    """Draw a sexy box for an addon."""
    name_short = name[:width-2]
    padding = width - 2 - len(name_short)
    left_pad = padding // 2
    right_pad = padding - left_pad

    return [
        f"╭{'─' * (width-2)}╮",
        f"│{' ' * left_pad}{name_short}{' ' * right_pad}│",
        f"╰{'─' * (width-2)}╯",
    ]


def _render_graph_horizontal(graph, levels):
    """Render dependency graph with horizontal layout."""
    lines = []
    box_width = 16
    level_spacing = 4

    # Build level columns
    level_boxes = []
    for level in levels:
        level_column = []
        for addon in level:
            level_column.append((addon, _draw_addon_box(addon, box_width)))
        level_boxes.append(level_column)

    # Calculate vertical positions
    max_height = max(len(level) * 4 for level in levels)

    # Draw level by level
    for level_idx, level_addons in enumerate(level_boxes):
        level_lines = [''] * max_height

        # Position boxes vertically in this level
        total_boxes = len(level_addons)
        spacing = max_height // (total_boxes + 1) if total_boxes > 0 else 0

        for box_idx, (addon, box) in enumerate(level_addons):
            y_pos = spacing * (box_idx + 1) - 1
            if y_pos < 0:
                y_pos = box_idx * 4

            # Place the box
            for line_offset, box_line in enumerate(box):
                line_num = y_pos + line_offset
                if 0 <= line_num < max_height:
                    level_lines[line_num] = box_line

        # Add level to output with spacing
        for i, line in enumerate(level_lines):
            if len(lines) <= i:
                lines.append('')
            lines[i] += line + (' ' * level_spacing if level_idx < len(level_boxes) - 1 else '')

    return lines


def _render_graph_ascii(graph, levels):
    """Render a proper ASCII graph with boxes and connection lines."""
    BOX_WIDTH = 16
    BOX_HEIGHT = 3
    LEVEL_SPACING = 6
    VERTICAL_SPACING = 1

    # Calculate positions for each addon
    positions = {}  # addon -> (x, y)
    x_offset = 2

    for level_idx, level_addons in enumerate(levels):
        x = x_offset + level_idx * (BOX_WIDTH + LEVEL_SPACING)
        y = 0
        for addon in level_addons:
            positions[addon] = (x, y)
            y += BOX_HEIGHT + VERTICAL_SPACING

    # Calculate canvas size
    if not positions:
        return []
    max_x = max(pos[0] for pos in positions.values()) + BOX_WIDTH + 2
    max_y = max(pos[1] for pos in positions.values()) + BOX_HEIGHT

    # Create canvas
    canvas = [[' ' for _ in range(max_x)] for _ in range(max_y)]
    protected = [[False for _ in range(max_x)] for _ in range(max_y)]

    # Helper to safely draw on canvas
    def draw_char(x, y, char, protect=False):
        """Draw char at position."""
        if 0 <= y < max_y and 0 <= x < max_x:
            canvas[y][x] = char
            if protect:
                protected[y][x] = True

    def safe_draw(x, y, char):
        """Draw char unless position is protected."""
        if 0 <= y < max_y and 0 <= x < max_x and not protected[y][x]:
            canvas[y][x] = char

    def draw_box(x, y, name):
        """Draw a box for an addon."""
        name_short = name[:BOX_WIDTH-4]
        padding = BOX_WIDTH - 4 - len(name_short)
        left_pad = padding // 2

        # Top border
        for i, char in enumerate('┌' + '─' * (BOX_WIDTH-2) + '┐'):
            draw_char(x + i, y, char, protect=True)

        # Middle with name - protect entire row
        draw_char(x, y + 1, '│', protect=True)
        for i in range(1, BOX_WIDTH - 1):
            draw_char(x + i, y + 1, ' ', protect=True)
        for i, char in enumerate(name_short):
            draw_char(x + 2 + left_pad + i, y + 1, char, protect=True)
        draw_char(x + BOX_WIDTH - 1, y + 1, '│', protect=True)

        # Bottom border
        for i, char in enumerate('└' + '─' * (BOX_WIDTH-2) + '┘'):
            draw_char(x + i, y + 2, char, protect=True)

    # Draw all boxes first
    for addon, (x, y) in positions.items():
        draw_box(x, y, addon)

    # Now draw connections
    for addon, info in graph.items():
        if addon not in positions:
            continue

        x_to, y_to = positions[addon]
        end_y = y_to + 1  # Middle of target box

        for dep in info['depends']:
            if dep not in positions:
                continue

            x_from, y_from = positions[dep]
            start_x = x_from + BOX_WIDTH
            start_y = y_from + 1  # Middle of source box

            if start_y == end_y:
                # Straight horizontal connection
                for x in range(start_x, x_to - 1):
                    safe_draw(x, start_y, '─')
                safe_draw(x_to - 1, start_y, '─')
                safe_draw(x_to, start_y, '>')
            else:
                # L-shaped connection
                mid_x = start_x + 3

                # Horizontal from source
                for x in range(start_x, mid_x):
                    safe_draw(x, start_y, '─')

                # Corner
                if start_y < end_y:
                    safe_draw(mid_x, start_y, '┐')
                else:
                    safe_draw(mid_x, start_y, '┘')

                # Vertical
                min_y = min(start_y, end_y)
                max_y_conn = max(start_y, end_y)
                for y in range(min_y + 1, max_y_conn):
                    curr = canvas[y][mid_x]
                    if curr == '─':
                        safe_draw(mid_x, y, '┼')
                    elif curr == '┐':
                        safe_draw(mid_x, y, '┤')
                    elif curr == '┘':
                        safe_draw(mid_x, y, '┤')
                    elif curr not in '│┼├┤':
                        safe_draw(mid_x, y, '│')

                # Corner at target
                if start_y < end_y:
                    curr = canvas[end_y][mid_x]
                    if curr == '│':
                        safe_draw(mid_x, end_y, '├')
                    else:
                        safe_draw(mid_x, end_y, '└')
                else:
                    curr = canvas[end_y][mid_x]
                    if curr == '│':
                        safe_draw(mid_x, end_y, '├')
                    else:
                        safe_draw(mid_x, end_y, '┌')

                # Horizontal to target
                for x in range(mid_x + 1, x_to - 1):
                    curr = canvas[end_y][x]
                    if curr == '│':
                        safe_draw(x, end_y, '┼')
                    elif curr == '┐':
                        safe_draw(x, end_y, '┬')
                    elif curr == '┘':
                        safe_draw(x, end_y, '┴')
                    else:
                        safe_draw(x, end_y, '─')

                safe_draw(x_to - 1, end_y, '─')
                safe_draw(x_to, end_y, '>')

    # Convert canvas to lines
    lines = ['  ' + ''.join(row).rstrip() for row in canvas]

    # Remove trailing empty lines
    while lines and not lines[-1].strip():
        lines.pop()

    return lines


def addon_dependency_graph():
    """Display addon dependency graph visualization."""
    print()
    print('═' * 72)
    print('  ADDON DEPENDENCY GRAPH')
    print('═' * 72)
    print()

    try:
        graph = _load_addon_dependencies()

        if not graph:
            print('  ⚠  No addons found')
            return True

        levels = _get_dependency_levels(graph)

        # Print statistics header with visual bar
        total_addons = len(graph)
        total_deps = sum(len(info['depends']) for info in graph.values())
        max_depth = len(levels) - 1
        avg_deps = total_deps / total_addons if total_addons > 0 else 0

        print(f'  📦 Total Addons: {total_addons:>2}  │  🔗 Dependencies: {total_deps:>2}  │  📊 Max Depth: {max_depth}  │  ⌀ Avg Deps: {avg_deps:.1f}')
        print()

        # Render ASCII graph
        graph_lines = _render_graph_ascii(graph, levels)
        for line in graph_lines:
            print(line)
        print()
        print(f"  {'─' * 64}")
        print()

        # Dependency statistics
        print('  📈 Dependency Statistics:')
        print()

        # Most depended-on modules
        dep_count = {}
        for addon, info in graph.items():
            for dep in info['depends']:
                dep_count[dep] = dep_count.get(dep, 0) + 1

        if dep_count:
            top_deps = sorted(dep_count.items(), key=lambda x: x[1], reverse=True)[:3]
            for dep, count in top_deps:
                bar_vis = '█' * count + '░' * (total_addons - count)
                print(f'    {dep:20s} {bar_vis[:20]} ({count} dependents)')

        print()

        # Check for issues
        issues = []

        # Check for circular dependencies
        for addon, info in graph.items():
            for dep in info['depends']:
                if dep in graph and addon in graph[dep]['depends']:
                    issues.append(f"Circular dependency: {addon} ↔ {dep}")

        # Check for missing dependencies
        all_addons = set(graph.keys())
        for addon, info in graph.items():
            for dep in info['depends']:
                if dep not in all_addons:
                    issues.append(f"Missing dependency: {addon} → {dep}")

        if issues:
            print('  ⚠  Issues detected:')
            for issue in issues:
                print(f'    ✗ {issue}')
            print()
            return False
        else:
            print('  ✓ PASS — clean dependency graph (no cycles, all dependencies valid)')
            return True

    except Exception as e:
        print(f'  ✗ Error analyzing dependencies: {e}')
        import traceback
        traceback.print_exc()
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print()
    print('┌──────────────────────────────────────────────────────────────────────┐')
    print('│               G T I M E L O G   Q U A L I T Y   G A T E            │')
    print('└──────────────────────────────────────────────────────────────────────┘')
    print()

    results = {}

    # First show the addon dependency graph
    results['addon dependencies'] = addon_dependency_graph()

    results['complexity'] = complexity_report()
    results['maintainability'] = maintainability_report()
    results['dead code'] = dead_code_report()

    # Coverage is informational in pre-commit (UI modules need a display).
    # The strict coverage gate runs in the pre-push stage instead.
    coverage_passed = coverage_report()
    results['coverage (informational)'] = True  # never blocks commit
    if not coverage_passed:
        print('  (i) Coverage is below threshold but not blocking commit.')

    # ── Summary ─────────────────────────────────────────────────────────
    print()
    print('═' * 72)
    print('  SUMMARY')
    print('═' * 72)
    print()
    all_ok = True
    for name, passed in results.items():
        icon = '✓' if passed else '✗'
        print(f'    {icon}  {name}')
        if not passed:
            all_ok = False
    print()

    if all_ok:
        print('  ══════════════════════════════════════')
        print('  ✓  ALL QUALITY GATES PASSED')
        print('  ══════════════════════════════════════')
        return 0
    print('  ══════════════════════════════════════')
    print('  ✗  SOME QUALITY GATES FAILED')
    print('  ══════════════════════════════════════')
    return 1


if __name__ == '__main__':
    sys.exit(main())
