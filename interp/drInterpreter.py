#Dice Interpreter .dr
import sys
from dataStruct import Stack, TypedView as View
from dice import Die,FairDie
from typing import Any, Literal, Protocol, TypeVar
from colorama import Fore,Style,init
from pathlib import Path

init(True)

_T_contra = TypeVar("_T_contra", contravariant=True)
class SupportsWrite(Protocol[_T_contra]):
	def write(self, s: _T_contra) -> object: ...

			
class DrFunction:
	def __init__(self,name:str,args:list[str],body:list[str]):
		if not (isinstance(name,str)):
			raise ValueError(f'name should be str, not {type(name).__name__}')
		self.name:str = name 
		self.args:list[str] = args
		self.body:list[str] = body
	def __str__(self):
		return f'{repr(self)} {len(self.body)}'
	def __iter__(self):
		yield self.name
		yield self.args
		yield self.body
	def __repr__(self):
		s = ''
		for i in self.args: s = ' '.join([s,i])
		return f'.func {self.name}{s}'
class DrModule:
	def __init__(self,name:str,vals:dict[str,Any|DrFunction]):
		self.name = name
		self.vals = vals 
	def __getitem__(self,index:str):
		return self.vals[index]
	def __setitem__(self,index:str,value:DrFunction|Any):
		self.vals[index] = value
	def __contains__(self,index:str):
		return (index in self.vals) if not isinstance(index,(list,tuple)) else False
	def __str__(self):
		return f'ModuleObject{ {repr(self)}}{self.vals} '
	def __repr__(self):
		return f'{self.name} import'
class Ev:
	keywords = ['vars','funcs',
				'stack','push','pop',
				'True', 'False',
				'read', 'err',
				'.func','.endfunc','call',
				'.if','.endif','.else',
				'import','dice',
				'del','quit','cls','log']
	operators = ['!',
				'+','-','*','/','**',
				'&&','||','--',
				'==','!=','>','<','>=','<=','T=',
				'//','?',
				'::','=','#','"',]
	simple_ops = ['+','-','*','/','**','&&','||','==','!=','>','<','>=','<=','T='] # 2 inputs 1 operation
	
	t_stack = Stack[Any]
	
	t_vars = dict[str,Any]
	t_funcs = dict[str,DrFunction]
	
	
	
	def is_valid_var(self,name)->bool:
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
	def repr(self,value:Any):
		if isinstance(value,(float)):
			return f'{value}f'
		return str(value)
	def err(self,error_type:str='ERROR',message:str='',at:int|None=None,func:tuple[str,int]|None=None):
		self.quit = True
		if func:
			print(Fore.RED+f'At {func[1]} in {self.name}:')
		print(Fore.RED + f'{error_type}{': ' if message != '' else ''}{message}{f' at line {at}' if at is not None and at != -1 else ''}{f' in function {func[0]}' if func is not None else ''}')
	def maj_err(self,error_type:str='MAJOR_ERROR',message:str='',at:int|None=None,func:tuple[str,int]|None=None):
		self.force_quit = True
		self.err(error_type,message,at,func)
	def __init__(self,filename:str,varrs:t_vars|None=None,is_main:bool=False):
		self.filename = filename
		self.name = 'MAIN' if is_main else filename
		self.force_quit:bool = False # for the quit command
		self.quit:bool = False # for errors
		self.vars:dict[str,DrFunction|DrModule|Any] = varrs if varrs is not None else {} # Includes modules and function
		self.vars |= {'FILENAME':self.name,'MAIN':'MAIN'}
		self.str_next = False # for " operator
		self.comment = False # // For multiline comments //
		
	@property
	def funcs(self):
		return View(DrFunction,self.vars)

	@property
	def modules(self):
		return View(DrModule,self.vars)


	def import_dr(self,imported:str,line:int|None = None ,func:tuple[str,int]|None = None):
		'''
		Imports a dr module and gives errors if a circular import is detected
		
		:param imported: The name of the imported module
		:type imported: str
		:param line: Used in err, the line this was activated on 
		:type line: int | None
		:param func: Used in err, the name of the function this is used and the in-function line
		:type func: tuple[str, int] | None
		'''
		path_local = Path.cwd() / imported
		path_std = Path(__file__).parent / 'stdlib' / imported
		path_local, path_std = path_local.with_suffix('.dr'), path_std.with_suffix('.dr')
		p = path_local if path_local.exists() else path_std
		
		if not p.exists():
			self.err('IMPORT_ERROR',f'Can\'t find path to {imported}',line,func)
			return
		
		with open(p,'r+') as f: # f turns empty after f.read() :(
			text = f.read()
			e = Ev(imported,None,False)
			if f'{self.filename} import' in text:
				self.err('IMPORT_ERROR','Circular import',line,func)
				return
			e.ev(text)
		self.modules[imported] = e.as_module(imported)
	def as_module(self,name:str) -> DrModule:
		return DrModule(name, self.vars)
	def call_func(self, func:DrFunction, arg_vals:list[Any], line:int=-1,func_in:tuple[str,int]|None=None):
		"""Execute a received function with provided argument values.
		Returns the function's return value (last value on the local stack) or None.
		Sets evaluator error state on failure.
		"""
		
		name,arg_names,body = func.name,func.args,func.body
		
		f = name, line

		loc = dict(zip(arg_names, arg_vals))
		local_stack = Stack()
		# run in a child evaluator that shares globals (vars and funcs)
		child = Ev(f'{self.name}/{name}',varrs=self.vars.copy() if isinstance(self.vars,dict) else {})
		# execute the function body using the child's ev so multi-line
		# constructs like .if and nested .func work inside functions
		child.ev('\n'.join(body), local_vars=loc, in_ev_stack=local_stack,func=f)
		if child.quit:
			self.quit = child.quit
			return None
		return local_stack.pop() if local_stack else None
	def log(self,*values:Any,sep:str=', ',end:str='\n',file: SupportsWrite[str]|None = None): # Debug ONLY
		'''
		Prints the values to a stream, or to sys.stdout by default.
		
		
		:type values: Any
		:param sep: string inserted between values, default a space.
		:type sep: str
		:param end: string appended after the last value, default a newline.
		:type end: str
		:param file: a file-like object (stream); defaults to the current sys.stdout.
		:type file: SupportsWrite[str] | None
		'''
		sargs = [self.repr(i) for i in values]
		print(Fore.GREEN+sep.join(sargs),end=end,file=file)
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
				line = line.split('?')[0] # ignore after comment
				
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
				level = 0
				while True:
					if i >= len(lines):
						self.err('FUNCTION_DEFINITION_ERROR', f'unterminated function definition for {name}')
						return
					l = lines[i].rstrip()
					if l.strip().startswith('.func'):
						level += 1
					if l.strip().startswith('.endfunc'):
						if level <= 0:
							break
						else:
							level -= 1
					body.append(l)
					i += 1
				if not isinstance(name,str): raise ValueError()
				self.funcs[name] = DrFunction(name, args, body)
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
	
	def ev_expr(self, expr:str, local_vars: dict|None = None, in_ev_stack: t_stack|None = None, line:int=-1,func:tuple[str,int]|None=None):
		'''
		Evaluate a single expression line in the given context.
		Supports local variables and a provided stack.
		'''

		toks = expr.split()
		
		ev_stack:Ev.t_stack = Stack() if in_ev_stack is None else in_ev_stack
		for i, tok in enumerate(toks):
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
				self.err(str(a),'',line,func)
				break
			elif tok[0] == 'd' and tok[1:].isdigit(): ev_stack.push(FairDie(tok))
			elif tok == 'dice':
				# stack dice -> Die(list(stack))
				if not len(ev_stack):
					self.err('ARGUMENT_ERROR',f'Not enough arguments for {repr(tok)}',line,func)
					break
				s = ev_stack.pop()
				if not isinstance(s, Stack):
					self.err('TYPE_ERROR',f'{repr(tok)} expects Stack, not {type(s).__name__}')
				ev_stack.push(Die(list(s))) 

			elif tok[:-1].replace('.','').isdecimal() and tok[-1].lower() == 'f':
				ev_stack.push(float(tok[:-1]))
			elif tok.isnumeric(): # Checks if tok is number
				ev_stack.push(int(tok)) # Turns into integer
			
			elif tok in ['True','False']: ev_stack.push(True if tok == 'True' else False)
			
			elif not len(toks)-1==i and toks[i+1] in ['=','import','::']:
				ev_stack.push(str(tok))
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
					self.err('TYPE_ERROR',f'push expects first argument to be Stack , not {type(s).__name__}',line)
					break
				s:Stack
				s.push(a)
				ev_stack.push(s)

			elif tok == 'pop':
				s = ev_stack.pop()
				if not isinstance(s,Stack):
					self.err('TYPE_ERROR',f'pop expects first argument to be Stack, not {type(s).__name__}',line,func)
					break
				if len(s) <= 0:
					self.err("STACK_ERROR","pop from empty stack",line,func)
					break	
				if isinstance(s,Stack):
					ev_stack.push(s.pop())
				
			elif tok == 'call':
				if len(ev_stack) < 1:
					self.err('FUNCTION_CALL_ERROR','No function on stack',line,func)
					break
				function1 = (ev_stack.pop())
				if not isinstance(function1,DrFunction):
					self.err('FUNCTION_CALL_ERROR','call last argument must be function',line,func)
					break


				name, arg_names, body = function1.name,function1.args,function1.body
				if len(arg_names) > len(ev_stack):
					self.err('FUNCTION_CALL_ERROR',f'Not enough arguments for {name}')
					break
				arg_vals = [ev_stack.pop() for _ in range(len(arg_names))]
				arg_vals.reverse()
				res = self.call_func(function1, arg_vals, line=line,func_in=func)
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
					self.err('TYPE_ERROR',f'Cannot compare string with {type(lh).__name__ if isinstance(lh,str) else type(rh).__name__}',line,func)
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
				print(Fore.YELLOW, ev_stack.pop(),end=' ')
			elif tok == 'log':
				if len(ev_stack) == 0:
					self.err('LOG_ERROR','Nothing to log',line,func)
					break
				self.log(ev_stack.pop())
			elif tok == '::':
				
				if len(ev_stack) < 2:
					self.err('ARGUMENT_ERROR','Not enough arguments for ::',line,func)
					break
					
				attr = (ev_stack.pop()) # Attr
				mod = (ev_stack.pop()) #DrModule
				
				if isinstance(mod,DrModule):
					if attr in mod:
						val = mod[attr]
					else:
						self.err('MODULE_ERROR',f'Can\'t find value {repr(attr)} in module {repr(mod)}',line,func)
						break
				else:
					self.err('MODULE_ERROR',f'{repr(mod)} isn\'t a module',line,func)
					break
				ev_stack.push(val)
			elif tok == 'import':
				if len(ev_stack) == 0:
					self.err('IMPORT_ERROR','Expected expression',line,func)
				file = ev_stack.pop()
				self.import_dr(file)
			elif tok == 'cls':
				print("\033[H\033[J", end="",flush=True)
			elif tok == '=':
				if len(ev_stack) < 2:
					self.err('VARIABLE_DEFINITION_ERROR',f'Not enough arguments for {tok}',line,func)
					break
				name = ev_stack.pop() # Name
				val = ev_stack.pop() # Value
				
				if not self.is_valid_var(name):
					self.err('VARIABLE_DEFINITION_ERROR',f'Invalid variable name: {repr(name)}',line,func)
					break
				name:str
				if name.upper() == name:
					self.err('VARIABLE_DEFINITION_ERROR',f'Can\'t modify constant {repr(name)}')
					break
					
				self.vars[name] = val
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



def help(ev:Ev,command:Literal[None,'--help']|Any=None):
	match command:
		case None:
			print('~~DiceRolls Interpreter~~')
			print('--help ~> Provides help for other commands.')
		case '--repl':
			print('Runs the console')
			print('Syntax:')
			print('--repl --load <file>')
		case '--help':
			print('Shows general help or help for a specific command.')
			print('Syntax: ')
			print('--help | Shows general help')
			print('--help *<command> | Shows help for every command given')
		case _:
			ev.err(f'Can\'t find help for "{command}"')

def console(evaluator:Ev):	
	print('DiceRolls interpreter running, note that it doesn\'t support dot keywords')
	while not evaluator.force_quit:
		try:
			print(Fore.CYAN+'>> '+Fore.RESET,end='')
			command = input()
			s = evaluator.ev_expr(command)
			print((Style.DIM+str(s.pop())+'\n') if len(s) else '',end='',flush=True)
		except KeyboardInterrupt:
			evaluator.maj_err('KEYBOARD_INTERRUPT')
		except EOFError:
			evaluator.maj_err('END_OF_FILE_ERROR')
		except Exception as e:
			evaluator.maj_err('MAJOR_CONSOLE_ERROR',f'A major error ocorred: "{e}"')

def main(evaluator:Ev|None=None):
	evaluator = Ev('console',is_main=True) if evaluator is None else evaluator
	if len(sys.argv) == 1: # only dr
		console(evaluator)
		

	elif len(sys.argv) >= 2:
		if sys.argv[1][0:2] != '--':	
			pathh = (Path.cwd() / sys.argv[-1]).with_suffix('.dr')
			if pathh.exists():
				with open(pathh) as interpreted: #argv[0] is dr
					evaluator.filename = sys.argv[-1]
					try:
						evaluator.ev(interpreted.read())
					except KeyboardInterrupt:
						evaluator.maj_err('KEYBOARD_INTERRUPT')
					except EOFError:
						evaluator.maj_err('END_OF_FILE_ERROR')
					except Exception as e:
						evaluator.maj_err('MAJOR_CONSOLE_ERROR',f'A major error ocorred: "{e}"')
			else:
				evaluator.err('FILE_NOT_FOUND_ERROR',f'Can\'t find file \'{sys.argv[-1]}\' in path')
		else:
			match sys.argv[1]:
				case '--repl':
					console(evaluator)
				case '--help':
					if len(sys.argv) == 3: # dr --help <command>
						help(evaluator,sys.argv[2])
					elif len(sys.argv) == 2: # dr --help
						help(evaluator)
					elif len(sys.argv) > 3: # dr --help <command> <command> ...
						for c in sys.argv[2:]:
							help(evaluator,c)
				case '--version' | '-v':
					print(Fore.BLUE+'DiceRolls v0.7b')
				case _:
					evaluator.err('CONSOLE_ERROR',f'Can\'t find command {sys.argv[1]}')
	
def test(interpreted:str,evaluator:Ev):
	'''
	Tests the evaluator for a given string
	
	:param evaluator: 
		The evaluator from the Ev class that will be used, if no evaluator is received, will use a single-use instance of the Ev class. 
		
		Can have default variables.
	:type evaluator: Ev
	:param interpreted: The str that will be evaluated as DiceRolls code
	:type interpreted: str
	'''
	evaluator.ev(interpreted)
	evaluator.log([f'{k}: {v}' for k,v in evaluator.vars.items()])
if __name__ == "__main__":
	main()

"""
TODO
---
Closures: When adding line to the body, if tok in vars replace tok

"""