# ai-shell-loop
Use openAi's gpt to generate and execute bash commands quickly.

## Installation

```bash
pipx install ai-shell-loop
```

### Open AI Key

Set your api key with `export OPENAI_API_KEY='your-api-key'`

See the [official-docs](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
for more information.


## Usage

```bash
ai-do "<plain english explanation of the goal>"
```

### Example

```bash
ai-do "create a python program that lists primes below 100"
```
## Logging
Each execution of ai-shell-loop generates a log file containing detailed information about the execution process.

### Log File Location
* Default Locations:
* * Linux: `~/.local/share/ai-shell-loop/logs/`
* * macOS: `~/Library/Application Support/ai-shell-loop/logs/`

### Custom Log Directory:

Set the environment variable `AI_SHELL_LOOP_LOG_DIR` to specify a custom directory for log files.
### Log File Naming
Log files are named with the current date and time, e.g., `ai-shell-loop_2024-04-27_15-30-00.log`.

### Logging Levels
By default, the logging level is set to INFO. To change the logging level, set the environment variable AI_SHELL_LOOP_LOG_LEVEL to one of the following:

* `DEBUG`
* `INFO`
* `WARNING`
* `ERROR`
* `CRITICAL`

#### Example:

```bash
export AI_SHELL_LOOP_LOG_LEVEL=DEBUG
```
## Development Setup

### Create environment
```bash
sudo apt install python3 python3-pip python3-venv pipx
python3 -m venv venv
source venv/bin/activate  # Activate the virtual environment
pip install -r requirements.txt  # Install dependencies
pip install -r build-requirements.txt  # Install dependencies for doing a build.
```


### Run 

With the virtual python environment activated, inside the project root, run `python -m ai_shell "echo the current time"`


## Build

Run `python -m build`

### Install locally

```
pipx install dist/ai_shell_loop-0.1.0-py3-none-any.whl
pipx ensurepath
```
After this, the `ai-do` command should be available anywhere. 

### Deploy to PyPi

```
twine upload dist/ai_shell_loop-0.1.0-py3-none-any.whl -u __token__ -p your_pypi_token
```