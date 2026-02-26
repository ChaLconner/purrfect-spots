#!/usr/bin/env python3
import subprocess
import sys
import re
import os
import argparse

def run_uv_install(requirements_file):
    """Run the uv pip install command and return exit code, stdout, stderr"""
    command = ["uv", "pip", "install", "-r", requirements_file, "--system"]
    try:
        # Capture output for analysis
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        print("Error: 'uv' command not found. Please ensure uv is installed and in your PATH.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Python Dependency Conflict Analyzer & Installer")
    parser.add_argument("-r", "--requirements", default="requirements.txt", help="Path to requirements file (default: requirements.txt)")
    parser.add_argument("--auto-resolve", action="store_true", help="Automatically downgrade failing packages and reinstall without prompting")
    args = parser.parse_args()

    requirements_file = args.requirements

    if not os.path.exists(requirements_file):
        print(f"Error: Requirements file '{requirements_file}' not found.")
        sys.exit(1)

    print(f"[*] Running initial dependency resolution with uv for {requirements_file}...")
    returncode, stdout, stderr = run_uv_install(requirements_file)

    # Success path
    if returncode == 0:
        print("[+] Success: All dependencies resolved and installed seamlessly!")
        print(stdout)
        sys.exit(0)

    print("[-] Dependency resolution failed. Analyzing conflict...\n")

    # Regex patterns matching uv's structured resolution failure output
    # Specifically handling: Because the current Python version (3.9.16) does not satisfy...
    current_py_match = re.search(r"current Python version \(([\d\.]+)\) does not satisfy", stderr)
    package_constraint_match = re.search(r"and ([a-zA-Z0-9_\-\.]+)(?:==([a-zA-Z0-9_\-\.]+))? depends on Python([><=\d\.]+)", stderr)
    
    # Check if a Python version conflict was identified
    if current_py_match and package_constraint_match:
        current_py_version = current_py_match.group(1)
        package_name = package_constraint_match.group(1)
        package_version = package_constraint_match.group(2)
        required_py_version = package_constraint_match.group(3)
        
        pkg_display = f"{package_name}=={package_version}" if package_version else package_name
        
        # Output detailed conflict analysis
        print("="*75)
        print(" !!! PYTHON VERSION CONFLICT DETECTED !!!")
        print("="*75)
        print(f" Current Python Interpreter : {current_py_version} (at /usr or active env)")
        print(f" Problematic Package        : {pkg_display}")
        print(f" Constraint Failed          : {package_name} requires Python {required_py_version}")
        print("="*75)
        
        print("\n[ ACTIONABLE RECOMMENDATIONS ]")
        
        print(f"\n1. DOWNGRADE PROBLEMATIC PACKAGE (Recommended workaround)")
        print(f"   Downgrade '{package_name}' to a previously released version that supports Python {current_py_version}.")
        
        # Determine a safe downgrade version specification
        downgrade_version_str = f"{package_name}<{package_version}" if package_version else f"{package_name}"
        if package_name.lower() == "alembic":
            # Alembic versions <= 1.13.1 support Python 3.9
            downgrade_version_str = "alembic<=1.13.1"
            print(f"   -> Suggestion: Change to '{downgrade_version_str}' as it natively supports Python 3.9.")
        else:
            print(f"   -> Update {requirements_file} to specify a constraint like '{downgrade_version_str}'.")
            
        print(f"\n2. UPGRADE PYTHON INTERPRETER")
        print(f"   Upgrade your system or environment to use Python {required_py_version.replace('>=', '')} or higher.")
        print("   If using CI/CD or Docker, update the base image (e.g., from python:3.9 to python:3.10).")
        
        print(f"\n3. ALTERNATIVE PACKAGES")
        print(f"   If you cannot downgrade '{package_name}' or upgrade Python, seek alternative libraries offering similar capabilities.\n")

        # Conflict Resolution Phase
        # Only prompt in interactive terminals unless auto-resolve is overridden
        if args.auto_resolve or sys.stdout.isatty():
            if not args.auto_resolve:
                choice = input(f"Do you want to automatically apply the downgrade workaround ({downgrade_version_str}) in {requirements_file} and retry? [y/N]: ").strip().lower()
                should_resolve = choice in ('y', 'yes')
            else:
                should_resolve = True

            if should_resolve:
                with open(requirements_file, "r") as f:
                    content = f.read()
                
                # Replace the exact requirement string in requirements.txt
                search_pattern = rf"^{package_name}=={package_version}" if package_version else rf"^{package_name}"
                new_content = re.sub(search_pattern, downgrade_version_str, content, flags=re.MULTILINE)
                
                if new_content != content:
                    print(f"[*] Applying downgrade constraint to {requirements_file}...")
                    with open(requirements_file, "w") as f:
                        f.write(new_content)
                    
                    print(f"[*] Performing uv pip installation after conflict resolution...\n")
                    # Reruning with stdout directly rendered to user
                    command = ["uv", "pip", "install", "-r", requirements_file, "--system"]
                    resolution_result = subprocess.run(command, check=False)
                    
                    if resolution_result.returncode == 0:
                        print("\n[+] Success: Dependencies successfully installed after conflict resolution!")
                        sys.exit(0)
                    else:
                        print("\n[-] Error: Installation failed even after conflict resolution.")
                        sys.exit(resolution_result.returncode)
                else:
                    print(f"[-] Could not locate exact package string '{pkg_display}' in '{requirements_file}'. Please modify it manually.")
    else:
        # Fallback for other dependency resolution errors
        print("An error occurred during dependency resolution:")
        print(stderr)
        print("\nPlease check your requirements file for typos or incompatible package version constraints.")
        
    # Standard exit with error code to indicate failure if resolution was not applied/successful
    sys.exit(returncode)

if __name__ == "__main__":
    main()
