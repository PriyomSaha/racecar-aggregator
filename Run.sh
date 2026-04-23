#!/bin/bash

read -p "Enter the full path to your Python script (.py): " script_path
read -p "Enter the full path to your requirements.txt: " requirements_path
read -p "Enter a name for your virtual environment (e.g., venv): " venv_name
read -p "Enter the name for your shell script (e.g., run_my_script.sh): " script_name

# Get base directory of the Python script
BASE_DIR="$(cd "$(dirname "$script_path")" && pwd)"
VENV_PATH="$BASE_DIR/$venv_name"

echo ""
echo "📁 Project directory: $BASE_DIR"

# Step 1: Create virtual environment if it doesn't exist
if [ ! -d "$VENV_PATH" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
else
    echo "✅ Virtual environment already exists"
fi

# Step 2: Activate and install dependencies
source "$VENV_PATH/bin/activate"

echo "⬆️ Upgrading pip..."
pip install --upgrade pip

echo "📦 Installing requirements..."
pip install -r "$requirements_path"

echo "🌐 Installing Playwright browsers..."
playwright install

# Step 3: Create executable script with absolute paths
echo "#!/bin/bash" > "$script_name"
echo "BASE_DIR=\"$BASE_DIR\"" >> "$script_name"
echo "source \"\$BASE_DIR/$venv_name/bin/activate\"" >> "$script_name"
echo "echo \"Using Python: \$(which python)\"" >> "$script_name"
echo "python \"$script_path\" \"\$@\"" >> "$script_name"
echo "read -p \"Press enter to exit...\"" >> "$script_name"

chmod +x "$script_name"

echo ""
echo "✅ DONE! Your script '$script_name' is ready."
echo "👉 Run it using: ./$script_name"

read -p "Press enter to continue..."