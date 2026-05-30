import subprocess
import sys
import re
from pathlib import Path


def get_modified_files():
    """Trouve les fichiers modifiés mais non commités."""
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True
    )
    changed_files = []
    for line in result.stdout.splitlines():
        if len(line) > 3:
            filepath = line[3:].strip()
            changed_files.append(filepath)
    return changed_files


def run_python_tests(changed_files: list[str]) -> int:
    import shutil

    # Clear __pycache__
    for p in Path(".").rglob("__pycache__"):
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)

    tests_to_run: set[str] = set()

    for f in changed_files:
        if not f.endswith(".py"):
            continue
        p = Path(f)
        if p.name == "conftest.py":
            continue

        p_str = str(p)
        if p_str.startswith("tests/") or p_str.startswith("test/") \
           or p_str.replace("\\", "/").startswith("tests/") \
           or p_str.replace("\\", "/").startswith("test/"):
            tests_to_run.add(str(p))
            continue

        module_name = p.stem
        rel_parts = list(p.parent.parts)
        if rel_parts and rel_parts[0] == "src":
            rel_parts = rel_parts[1:]
        rel_dir = Path(*rel_parts) if rel_parts else Path("")

        for base in [Path("tests/unit") / rel_dir, Path("tests") / rel_dir]:
            candidates = [base / f"{module_name}.py", base / f"test_{module_name}.py"]
            for candidate in candidates:
                if candidate.exists():
                    tests_to_run.add(str(candidate))

    if not tests_to_run:
        print("[OK] No specific Python unit tests found for these modifications.")
        return 0

    found_markers = set()
    marker_pattern = re.compile(r"^\s*@pytest\.mark\.([a-zA-Z0-9_]+)", re.MULTILINE)

    for test_file in tests_to_run:
        try:
            content = Path(test_file).read_text(encoding="utf-8")
            found_markers.update(marker_pattern.findall(content))
        except Exception:
            pass

    marker_args = []
    if found_markers:
        ignored = {"parametrize", "usefixtures", "skip", "skipif", "xfail", "asyncio"}
        valid_markers = [m for m in found_markers if m not in ignored]
        if valid_markers:
            marker_expr = " or ".join(valid_markers)
            marker_args = ["-m", marker_expr]
    else:
        if not any("e2e" in str(p).lower() for p in tests_to_run):
            marker_args = ["-m", "not e2e"]

    print(f"[RUN] Execution ciblee de Pytest sur : {', '.join(tests_to_run)}")
    if marker_args:
        print(f"[RUN] Filtrage des marqueurs actif : {marker_args[1]}")

    # FIX 1: Removed "-p", "no:cacheprovider" so --lf works
    base_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-qq",
        "--maxfail=20",
        "--tb=long",
        "--disable-warnings",
        "-o",
        "log_cli=False", 
    ] + marker_args

    cmd = base_cmd + list(tests_to_run)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        print("\n=== TEST SUITE TIMED OUT ===")
        print("\n[AI INSTRUCTION] The tests timed out after 180 seconds. You likely introduced an infinite loop. Please analyze your last edit.")
        return 1

    if result.returncode == 0:
        print("[OK] Tous les tests Python cibles sont passes.")
        return 0

    output = result.stdout + result.stderr

    if re.search(r"\b\d+ passed\b", output) and re.search(r"\b\d+ failed\b", output):
        print("[WARN] Echecs partiels detectes. Relance avec --lf pour Aider...")
        lf_cmd = base_cmd + ["--lf", "-v"] + list(tests_to_run)
        
        try:
            lf_result = subprocess.run(lf_cmd, capture_output=True, text=True, timeout=60)
            
            # FIX 2: If the --lf rerun fails with a configuration error (exit code 4), 
            # fall back to printing the original test output so the AI isn't left blind.
            if lf_result.returncode == 4 or "unrecognized arguments" in lf_result.stderr:
                print("\n=== ORIGINAL TEST FAILURES ===")
                print(output)
            else:
                print(lf_result.stdout)
                if lf_result.stderr:
                    print(lf_result.stderr)

            print("\n[AI INSTRUCTION] The tests above failed after the recent changes. Please analyze the traceback and implement a fix.")
            return lf_result.returncode if lf_result.returncode != 0 else 1
            
        except subprocess.TimeoutExpired:
            print("\n=== LAST FAILED TESTS TIMED OUT ===")
            print("\n[AI INSTRUCTION] The rerunning of failed tests timed out. You introduced an infinite loop or deadlock. Please fix the code.")
            return 1

    # Fallback for total failure or syntax errors
    print("\n=== TOTAL TEST FAILURE OR SYNTAX ERROR ===")
    print(output)
    print("\n[AI INSTRUCTION] The test suite failed to run or encountered major errors. Please fix the code so tests can execute.")
    return result.returncode if result.returncode != 0 else 1


def run_rust_tests():
    print("[RUN] Execution des tests Cargo...")
    cmd = ["cargo", "test"]

    # Check for Rust projects in standard locations
    rust_manifest_paths = []
    if Path("src/secure_core/Cargo.toml").exists():
        rust_manifest_paths.append("src/secure_core/Cargo.toml")
    if Path("scrubbers/Cargo.toml").exists():
        rust_manifest_paths.append("scrubbers/Cargo.toml")

    if not rust_manifest_paths:
        print("[OK] No Rust Cargo.toml found in standard locations. Skipping Rust tests.")
        return 0

    # Use the first found Cargo.toml
    cmd.extend(["--manifest-path", rust_manifest_paths[0]])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("[OK] Tous les tests Rust sont passes.")
        return 0

    output = result.stdout + result.stderr
    passed_match = re.search(r"(\d+) passed;", output)
    if passed_match and int(passed_match.group(1)) > 0:
        print("[WARN] Echecs Rust detectes. Extraction des logs...")
        try:
            fail_section = output.split("\nfailures:\n")[1]
            print("\nfailures:\n" + fail_section)
        except IndexError:
            print(output)
        print(
            "\n[AI INSTRUCTION] Please analyze the Rust failures above and fix the corresponding source code."
        )
        return result.returncode if result.returncode != 0 else 1

    print("\n=== RUST COMPILATION OR TOTAL FAILURE ===")
    print(output)
    print(
        "\n[AI INSTRUCTION] Rust compilation failed. Please fix the syntax/borrow-checker errors above."
    )
    return result.returncode if result.returncode != 0 else 1


def run_dart_flutter_tests():
    print("[RUN] Execution des tests Dart/Flutter...")
    is_flutter = False
    pubspec = Path("pubspec.yaml")
    if pubspec.exists():
        try:
            if "flutter:" in pubspec.read_text(encoding="utf-8", errors="ignore"):
                is_flutter = True
        except Exception:
            pass

    cmd_base = "flutter" if is_flutter else "dart"
    cmd = [cmd_base, "test"]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] Tous les tests {cmd_base.capitalize()} sont passes.")
        return 0

    output = result.stdout + result.stderr
    print(f"\n=== {cmd_base.upper()} TEST FAILURES ===")
    print(output)
    print(
        f"\n[AI INSTRUCTION] The {cmd_base.capitalize()} tests failed. Please analyze the logs and provide a fix."
    )
    return result.returncode if result.returncode != 0 else 1


def main():
    changed_files = get_modified_files()

    run_python = any(f.endswith(".py") for f in changed_files)
    run_rust = any(f.endswith((".rs", "Cargo.toml")) for f in changed_files)
    run_dart = any(f.endswith((".dart", "pubspec.yaml")) for f in changed_files)

    if not run_python and not run_rust and not run_dart:
        print(
            "[OK] Aucun fichier source pertinent (Python, Rust, Dart) modifie. Ignore."
        )
        return 0

    exit_codes = []

    if run_rust:
        exit_codes.append(run_rust_tests())
    if run_python:
        exit_codes.append(run_python_tests(changed_files))
    if run_dart:
        exit_codes.append(run_dart_flutter_tests())

    return max(exit_codes) if exit_codes else 0


if __name__ == "__main__":
    sys.exit(main())
