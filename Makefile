# Makefile for pybabel workflow

# Variables
DOMAIN = messages
LOCALE_DIR = lang
POT_FILE = $(DOMAIN).pot
BABEL_CFG = babel.cfg

# Extract messages to POT file
extract:
	pybabel extract -F $(BABEL_CFG) -o $(POT_FILE) .

# Update translations from POT file
update:
	pybabel update -i $(POT_FILE) -d $(LOCALE_DIR)

# Compile translations into MO files
compile:
	pybabel compile -d $(LOCALE_DIR)

# Clean compiled .mo files (optional)
clean:
	find $(LOCALE_DIR) -name "*.mo" -delete

# Export environment
env:
    export $(xargs < .env)