# Set authorization and base URL

$env:ANTHROPIC_BASE_URL="https://api.cborg.lbl.gov"

# Model selection -- set to latest version of each model
# NOTE: You will need to update these each time a new model is released
# NOTE: Other models can be used, but ClaudeCode will incorrectly calculate API costs
$env:ANTHROPIC_SMALL_FAST_MODEL="anthropic/claude-haiku"

# Default conversation model
$env:ANTHROPIC_MODEL="anthropic/claude-sonnet"

# Recommended setting
$env:DISABLE_NON_ESSENTIAL_MODEL_CALLS=1

# Recommended setting
$env:DISABLE_TELEMETRY=1

# Recommended setting for compatibility
$env:CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1

# Recommended setting to reduce model throttling
# Higher max output tokens can be used but may cause prompts to be rejected with "too many tokens" error
$env:CLAUDE_CODE_MAX_OUTPUT_TOKENS=8192

.\.venv\Scripts\activate.ps1

C:\Users\lab\.local\bin\claude.exe -d