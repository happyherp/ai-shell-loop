# ai-shell
Use openAi's gpt to generate and execute bash commands quickly.

## Setup

### Create environment
```bash
sudo apt install python3 python3-pip python3-venv pipx
python3 -m venv venv
source venv/bin/activate  # Activate the virtual environment
pip install -r requirements.txt  # Install dependencies
pip install -r build-requirements.txt  # Install dependencies for doing a build.
```

### Open AI Key
Put your openAI api-key in the file `openai.key` in the project root. 

# Build

Run `python -m build`

## Install locally

```
pipx install dist/ai_do-0.1.0-py3-none-any.whl
pipx ensurepath
```