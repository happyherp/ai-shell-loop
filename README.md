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

Set your api key with `export OPENAI_API_KEY='your-api-key'`

See the [official-docs](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
for more information.

# Run 

With the virtual python environment activated, inside the project root, run `python -m ai_shell "echo the current time"`


# Build

Run `python -m build`

## Install locally

```
pipx install dist/ai_do-0.1.0-py3-none-any.whl
pipx ensurepath
```
After this, the `ai-do` command should be available anywhere. 