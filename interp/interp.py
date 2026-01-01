#Dice Interpreter .dr
import sys
from dataStruct import Stack
from dice import Die,FairDie
from typing import Any, Literal
from colorama import Fore,init
from pathlib import Path
init(True)
#from dataStruct import Stack
def is_number(s):
		try:
			float(s)
			return True
		except ValueError:
			return False
def is_bool(s):
		return s in ['True','False']
			
'''
I have no idea if this is good code
'''
class Ev:
	keywords = ['vars','funcs','stack','push','pop', 'True', 'False', 'read', 'err', '.func','.endfunc','call','.if','.endif','.else','del','import']
	operators = ['!','+','-','*','/','**','&&','||','==','!=','=','#','"','--','>','<','>=','<=','T=','//','?']
	simple_ops = ['+','-','*','/','**','&&','||','==','!=','>','<','>=','<=','T='] # 2 inputs 1 operation
	
	t_stack = Stack[Any]
	t_func = tuple[list[str],list[str]] # (['arg1','arg2'],['arg1 arg2 +'])
	t_vars = dict[str,Any]
	t_funcs = dict[str,t_func]
	
	
	@staticmethod
	def is_valid_var(name:str)->bool:
		if not isinstance(name,str):
			return False
		if name in Ev.keywords:
			return False
		if ' ' in name:
			return False
		for c in name:
			if c in Ev.operators:
				return False
		return True
	def err(self,error_type:str='ERROR',message:str='',at:int|None=None,func:tuple[str,int]|None=None):
		self.quit = True
		if func:
			print(Fore.RED+f'At {func[1]}:')
		print(Fore.RED + f'{error_type}{': ' if message != '' else ''}{message}{f' at line {at}' if at is not None and at != -1 else ''}{f' in function {func[0]}' if func is not None else ''}')
	def __init__(self,varrs:t_vars={},funcs:t_funcs={}):
		
		self.force_quit:bool = False
		self.quit:bool = False
		self.vars:Ev.t_vars = varrs
		self.funcs:Ev.t_funcs = funcs
		self.str_next = False
		self.comment = False
		self.import_dr('stdlib')
	def import_dr(self,imported:str):
		p = Path.cwd()
		p /= imported
		p = p.with_suffix('.dr') 
		with open(p) as f:
			self.ev(f.read())
	def call_func(self, name:str, arg_vals:list[Any], line:int=-1,func:tuple[str,int]|None=None):
		"""Execute a defined function by name with provided argument values.
		Returns the function's return value (last value on the local stack) or None.
		Sets evaluator error state on failure.
		"""
		f = (name,line) # name, called
		if name not in self.funcs:
			self.err('FUNCTION_CALL_ERROR',f'unknown function {repr(name)}',line,func)
			return None
		arg_names, body = self.funcs[name]
		if len(arg_vals) < len(arg_names):
			self.err('ARGUMENT_ERROR',f'Too few arguments for function {repr(name)}',line,func)
			return None
		if len(arg_vals) > len(arg_names):
			self.err('ARGUMENT_ERROR',f'Too many arguments for function {repr(name)}',line,func)
			return None
		loc = dict(zip(arg_names, arg_vals))
		local_stack = Stack()
		# run in a child evaluator that shares globals (vars and funcs)
		child = Ev(varrs=self.vars.copy() if isinstance(self.vars,dict) else {}, funcs=self.funcs)
		# execute the function body using the child's ev so multi-line
		# constructs like .if and nested .func work inside functions
		child.ev('\n'.join(body), local_vars=loc, in_ev_stack=local_stack,func=f)
		if child.quit:
			self.quit = child.quit
			return None
		return local_stack.pop() if local_stack else None
	def log(self,*args:Any,sep:str=', '):
		sargs = [str(i) for i in args]
		print(Fore.GREEN+sep.join(sargs))
	def ev(self, s:str, local_vars: dict|None = None, in_ev_stack: t_stack|None = None,func:tuple[str,int]|None=None):
		
		lines = s.split('\n')
		i = 0
		while i < len(lines):
			line = lines[i].strip()

			if line == '': #Skips the line
				i += 1
				continue
			
					
			# function definition: .func name arg1 arg2 ...
			if line.startswith('.func'):
				parts = line.split()
				if len(parts) < 2: # <= 1 
					self.err('FUNCTION_DEFINITION_ERROR', f'malformed .func header',i+1,func)
					return
				# parts[0] is '.func'
				name = parts[1]
				args = parts[2:]
				
				body = []
				i += 1
				# collect until .endfunc
				while True:
					if i >= len(lines):
						self.err('FUNCTION_DEFINITION_ERROR', f'unterminated function definition for {name}')
						return
					l = lines[i].rstrip()
					if l.strip().startswith('.endfunc'):
						break
					body.append(l)
					i += 1
				self.funcs[name] = (args, body)
				# skip the .endfunc line
				i += 1
				continue
			
			if line.startswith(".if"):
				split = line.split(maxsplit=1)
				if len(split) < 2:
					self.err('IF_STATEMENT_ERROR','Missing expression for .if',i+1,func)
					i += 1
					continue
				expr = split[1]
				stck = self.ev_expr(expr, local_vars=local_vars, in_ev_stack=in_ev_stack, line=i+1,func=func)
				if not stck:
					self.err('IF_STATEMENT_ERROR','Expected expression result',i+1,func=func)
					# skip forward to matching .endif to stay in consistent state
					level = 0
					j = i + 1
					while j < len(lines):
						stripped = lines[j].strip()
						if stripped.startswith('.if'):
							level += 1
						elif stripped.startswith('.endif'):
							if level == 0:
								break
							level -= 1
						j += 1
					if j >= len(lines):
						self.err('IF_STATEMENT_ERROR','Unterminated if statement',func=func)
						return
					i = j + 1
					continue
				cond = bool(stck.pop())
				# scan for matching .else (at same nesting) and .endif
				level = 0
				j = i + 1
				else_index = -1
				end_index = -1
				while j < len(lines):
					stripped = lines[j].strip()
					if stripped.startswith('.if'):
						level += 1
					elif stripped.startswith('.endif'):
						if level == 0:
							end_index = j
							break
						else:
							level -= 1
					elif stripped.startswith('.else') and level == 0:
						else_index = j
					j += 1
				if end_index == -1:
					self.err('IF_STATEMENT_ERROR','Unterminated if statement',i+1,func)
					return
				# choose which block to execute
				if cond:
					start = i + 1
					stop = else_index if else_index != -1 else end_index
				else:
					if else_index == -1:
						# nothing to run
						i = end_index + 1
						continue
					start = else_index + 1
					stop = end_index
				# execute selected block using ev so nested statements are handled
				block = '\n'.join(lines[start:stop])
				self.ev(block, local_vars=local_vars, in_ev_stack=in_ev_stack, func=func)
				if self.quit:
					return
				i = end_index + 1
				continue

						
			# normal line -> evaluate
			self.ev_expr(line, local_vars=local_vars, in_ev_stack=in_ev_stack, line=i+1, func=func)
			if self.quit:
				break
			i += 1

	def ev_expr(self, expr:str, local_vars: dict|None = None, in_ev_stack: t_stack|None = None, line:int=-1,func:str|None=None):
		'''
		Evaluate a single expression line in the given context.
		Supports local variables and a provided stack.
		'''

		toks = expr.split()
		
		ev_stack:Ev.t_stack = Stack() if in_ev_stack is None else in_ev_stack
		for tok in toks:
			if tok == '//':
				self.comment = True if not self.comment else False
			if self.comment: continue
			if tok == 'read': tok = input("<read> ")
			if self.str_next:
				ev_stack.push(str(tok))
				self.str_next = False
				continue
			if tok == 'err':
				a = ev_stack.pop()
				self.err(str(a),line,func)
				break
			elif tok[0] == 'd' and tok[1:].isdigit(): ev_stack.push(FairDie(tok))
			elif tok[:-1].replace('.','').isdecimal() and tok[-1].lower() == 'f':
				ev_stack.push(float(tok[:-1]))
			elif is_number(tok):
				ev_stack.push(int(tok))
			
			elif tok in ['True','False']: ev_stack.push(True if tok == 'True' else False)
			elif local_vars and tok in local_vars:
				ev_stack.push(local_vars[tok])
			elif tok in self.vars: 
				ev_stack.push(self.vars[tok])
			elif tok == '--':
				a = ev_stack.pop()
				ev_stack.push((- a) if isinstance(a,float|int) and not isinstance(a,bool) else not a )
			elif tok == 'stack':
				ev_stack.push(Stack())
			elif tok == 'push':
				if len(ev_stack) < 2:
					self.err('ARGUMENT_ERROR',f'Not enough arguments for {tok}')
					break
				a = ev_stack.pop() #value
				s = ev_stack.pop() #stack
				if not isinstance(s,Stack):
					self.err('TYPE_ERROR',f'push expects arguments <Stack> <Any>, not <{type(s).__name__}> <Any>',line)
					break
				s:Stack
				s.push(a)
				ev_stack.push(s)

			elif tok == 'pop':
				s = ev_stack.pop()
				if not isinstance(s,Stack):
					self.err('TYPE_ERROR',f'push expects arguments <Stack> <Any>, not <{type(s).__name__}> <Any>',line,func)
					break
				if len(s) <= 0:
					self.err("STACK_ERROR","pop from empty stack",line,func)
					break	
				if isinstance(s,Stack):
					ev_stack.push(s.pop())
				
			elif tok == 'call':
				if len(ev_stack) < 1:
					self.err('FUNCTION_CALL_ERROR','No function name on stack',line,func)
					break
				name = str(ev_stack.pop())

				if name not in self.funcs:
					self.err('FUNCTION_CALL_ERROR',f'unknown function {repr(name)}',line,func)
					break
				arg_names = self.funcs[name][0]
				if len(ev_stack) < len(arg_names):
					self.err('ARGUMENT_ERROR',f'Too few arguments for function {repr(name)}',line,func)
					break
				arg_vals = [ev_stack.pop() for _ in range(len(arg_names))]
				arg_vals.reverse()
				res = self.call_func(name, arg_vals, line=line,func=func)
				if self.quit:
					break
				if res is not None:
					ev_stack.push(res)
				continue
			elif tok == '?':
				# COMMENT SHALL IGNORE
				break
			elif tok == '!':
				a = ev_stack.pop()
				ev_stack.push(a.play() if isinstance(a,Die) else a)
#			elif tok == '%': TODO fix this
#				a = ev_stack.pop()
#				b = ev_stack.pop()
#				ev_stack.push(a.probability(b) if isinstance(a,Die) else (int(a == b)))
			elif tok in  Ev.simple_ops:
				if len(ev_stack) < 2:
					self.err('ARGUMENT_ERROR',f'Not enough arguments for {tok}',line)
				rh = ev_stack.pop()
				lh = ev_stack.pop()
				comp = ['<','<=','>','>=']
				math = ['+','-','*','/','**']
				if (isinstance(lh,str) or isinstance(rh,str)) and tok in comp:
					self.err('TYPE_ERROR',f'Cannot compare string with {type(lh) if isinstance(lh,str) else type(rh)}',line,func)
					break
				if (isinstance(lh,(str,Stack,Die,bool)) or isinstance(rh,(str,Stack,Die,bool))) and (tok in math or tok in comp):
					self.err('TYPE_ERROR',f'Cannot perform operation {tok} with {type(lh).__name__} and {type(rh).__name__}',line,func)
					break
				if tok in comp:
					lh:int|float
					rh:int|float
				match tok:
					#Type Comp
					case 'T=': ev_stack.push(type(lh)==type(rh))
					# Math
					case '+': ev_stack.push(lh + rh)
					case '-': ev_stack.push(lh - rh)
					case '*': ev_stack.push(lh * rh)
					case '/': ev_stack.push(lh / rh)
					case '**': ev_stack.push(lh ** rh)
					# Bool
					case '&&': ev_stack.push(bool(lh) and bool(rh))
					case '||': ev_stack.push(bool(lh) or bool(rh))
					#Comp
					case '==': ev_stack.push(lh == rh)
					case '!=': ev_stack.push(lh != rh)
					case '<': ev_stack.push(lh < rh)
					case '<=': ev_stack.push(lh <= rh)
					case '>': ev_stack.push(lh > rh)
					case '>=': ev_stack.push(lh >= rh)
					# Bitwise
					case '^': ev_stack.push(lh ^ rh) if isinstance(lh,int) and isinstance(rh,int) else self.err('TYPE_ERROR','Bitwise XOR requires integer or boolean operands',line,func)
			elif tok == '#':
				if len(ev_stack) == 0:
					self.err('PRINT_ERROR','Nothing to print',line,func)
					break
				print(Fore.YELLOW + repr(ev_stack.peek()),end=' ')
			elif tok == 'import':
				if len(ev_stack) == 0:
					self.err('IMPORTING_ERROR','Expected expression',line,func)
				file = ev_stack.pop()
				self.import_dr(file)
			elif tok == '=':
				if len(ev_stack) < 2:
					self.err('VARIABLE_DEFINITION_ERROR',f'Not enough arguments for {tok}',line,func)
					break
				a = ev_stack.pop() # Name
				b = ev_stack.pop() # Value
					
				if not Ev.is_valid_var(a):
					self.err('VARIABLE_DEFINITION_ERROR',f'Invalid variable name: {repr(a)}',line,func)
					break
				self.vars[a] = b
			elif tok == '"':
				self.str_next = True
			elif tok == 'del':
				var_name = ev_stack.pop()
				if var_name in self.vars:
					del self.vars[var_name]
				else:
					self.err('VARIABLE_DELETION_ERROR',f'Can\'t find variable {repr(var_name)} in vars')
			elif tok == 'quit':
				self.quit = self.force_quit = True
			elif tok == 'vars':
				print(Fore.MAGENTA + str(list(self.vars.keys())))
			elif tok == 'funcs':
				print(Fore.MAGENTA + str(list(self.funcs.keys())))
			else:
				ev_stack.push(str(tok))
		if ('#' in toks or 'vars' in toks or 'funcs' in toks) and not self.comment:
			print('',end='\n')
		return ev_stack
	

def help(command:Literal[None,'--help']=None):
	match command:
		case None:
			print('~~DiceRolls Interpreter~~')
			print('--help ~> Provides help for other commands.')
		case '--help':
			print('Shows general help or help for a specific command.')

def console(evaluator:Ev=Ev()):
	print('DiceRolls interpreter running, note that it doesn\'t support dot keywords')
	while not evaluator.force_quit:
		command = input(Fore.LIGHTBLUE_EX+'>> '+Fore.RESET)
		evaluator.ev_expr(command)
		# TODO Check signals

def main(evaluator:Ev=Ev()):
	if len(sys.argv) == 1: # only dr
		console(evaluator)
		

	if len(sys.argv) >= 2:
		if sys.argv[1][0:2] != '--':	
			with open(sys.argv[-1]) as interpreted:#argv[0] is dr
				evaluator.ev(interpreted.read())
		else:
			match sys.argv[1]:
				case '--':
					console(evaluator)
				case '--help':
					if len(sys.argv) == 3: # dr --help <command>
						help(sys.argv[2])
					elif len(sys.argv) == 2: # dr --help
						help()
					elif len(sys.argv) > 3: 
						evaluator.err('ARGUMENT_ERROR','Too many arguments for --help')
	
def test(interpreted:str,evaluator:Ev=Ev()):
	'''
	Tests the evaluator for a given string
	
	:param evaluator: 
		The evaluator from the Ev class that will be used, if no evaluator is received, will use a single-use instance of the Ev class. 
		
		Can have default variables and functions.
	:type evaluator: Ev
	:param interpreted: The str that will be evaluated as DR code
	:type interpreted: str
	'''
	evaluator.ev(interpreted)
if __name__ == "__main__":
	
	e = Ev()
	main(e)

