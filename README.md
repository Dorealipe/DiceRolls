
# DiceRolls Interpreter (.dr)
A stack-based interpreter designed for data manipulation, modular functions, and dice-based simulations.

## Installation (Windows)
1. The project includes a setup script to integrate the interpreter directly into your terminal.

2. Run the setup.ps1 script as an Administrator.

3. The script will automatically add the `DiceRolls/interp` folder to your User PATH.

4. Restart your terminal.

You can now use the `dr` command from any folder.

## Usage
### Running the Console
`dr --`
or
`dr`
### Executing a Script
`dr script.dr`

## Commands
- `--help`: Shows the help menu.
## Syntax Overview
### Stack Operations
- `stack`: Creates a new stack.

- `push`: Pushes a value into a target stack.

- `pop`: Pops the top value of a stack.

### Variables and Functions
- `value " name =`: Assigns a value to a variable.

- `.func name args ... .endfunc`: Defines a reusable function.

- `args func call`: Executes a function currently on the stack.

### Dice Mechanics
- `dX`: Creates a fair die with X sides (e.g., d20).
- `stackType dice`: Converts a stack of value into a Die object.
- `diceType !`: Rolls the die and returns a result, if the received value is not a dice, it will return the value itself.

### If statements
- `.if True`: Checks if the following expression returns True
- `.else`: Executes if the expression was false
### Others
- `vars`: Prints all vars
- `funcs`: Prints all functions
- `cls`: Clears the console
- `quit`: Ends the session
- `ERROR_TYPE err`: Outputs an error


