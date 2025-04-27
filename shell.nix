{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  # Build a custom Python interpreter with PySide6 bundled
  buildInputs = [
    (pkgs.python312.withPackages (ps: with ps; [
      pyside6      # Qt for Python bindings
    ]))
    # Include pip and venv for managing extra packages
    pkgs.python312Packages.pip
    pkgs.python312Packages.virtualenv
  ];

  # Automatically create or reuse a local virtualenv on shell entry
  shellHook = ''
    if [ -z "$VIRTUAL_ENV" ]; then
      echo "🛠 Creating virtual environment in .venv..."
      python -m venv .venv
      source .venv/bin/activate
      pip install --upgrade pip
      echo "✅ Activated virtualenv at $(pwd)/.venv"
    else
      echo "🔄 Using existing virtualenv at $VIRTUAL_ENV"
    fi
  '';
}
