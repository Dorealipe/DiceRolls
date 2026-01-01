from typing import Generic, TypeVar as typeVar,Any,Callable, Optional, Iterable, Literal
_T = typeVar('_T',default=Any)
_T2 = typeVar("_T2",default=Any)

class Node(Generic[_T]):
	def __init__(self,value:_T):
		self.value = value
		self.next:Optional[Node] = None
	def __str__(self):
		return f'N:{self.value} -> {self.next}' 
	def copy(self):
		n = Node(self.value)
		n.next = n.next.copy() if n.next is not None else None
		return n
	def __eq__(self,other:Any):
		if not isinstance(other,Node):
			return False
		return (self.value == other.value) and (self.next == other.next)	
	def __ne__(self,other:Any):
		return not self == other
	def __repr__(self):
		return str(self)
		  
class TreeNode(Generic[_T]):
	def __init__(self,value:_T):
		self.value = value
		self.left:Optional[TreeNode[_T]] = None
		self.right:Optional[TreeNode[_T]] = None
	def swap_children(self):
		self.left,self.right = self.right, self.left
	
	def __repr__(self):
		center = f'TN:{self.value}'
		left = f'({self.left}) <- ' if self.left is not None else ''
		right = f' -> ({self.right})' if self.right is not None else ''
		return left + center + right
		
	


		
class Stack(Generic[_T]):
	def __init__(self,iterable:Optional[Iterable]=None):
		self.head:Optional[Node] = None
		self.__size:int = 0
		
		if iterable is not None:
			for i in list(reversed(iterable)):
				self.push(i)
	def push(self,value:_T):
		node:Node[_T] = Node(value)
		node.next = self.head
		self.head = node
		self.__size += 1
	def pop(self) -> _T:
		node = self.head
		if self.head is Node: raise IndexError('pop from empty stack')
		self.head = node.next 
		self.__size -= 1
		return node.value
	def peek(self):
		if self.head is None:
			raise IndexError('peek empty stack')
		return self.head.value
	def __iter__(self):
		n = self.head
		while n is not None:
			yield n.value
			n = n.next
	def __str__(self):
		return f'Stack{[i if i is not self else '...' for i in self]}'
	def __len__(self):
		return self.__size
	def __repr__(self):
		return f'S:{[i if i is not self else '...' for i in self]}'
	def __reversed__(self):
		s=Stack()
		for i in self:
			s.push(i)
		return s
	def copy(self):
		s = Stack()
		s.head = self.head.copy()
		return s
	def clear(self):
		self.head = None
		self.__size = 0
class Queue(Generic[_T]):
	def __init__(self,iterable:Optional[Iterable]=None):
		self.head:Optional[Node[_T]] = None
		self.tail:Optional[Node[_T]] = None
		self.__size: int = 0
		if iterable is not None:
			for i in list(reversed(iterable)):
				self.enqueue(i)
	def __str__(self):
		return f'Back -> {[i for i in self]} -> Front' 
	def __repr__(self):
		return f'B{[i for i in self]}F'	   
	def enqueue(self,value:_T):
		node:Node[_T] = Node(value)
		if self.head is None:
			self.tail = node
		node.next = self.head
		self.head = node
		self.__size += 1
	def dequeue(self) -> _T:
		node = self.tail
		n = self.head
		if self.head is None: raise IndexError('pop from empty queue')
		if self.head == self.tail:
			self.clear()
			return n.value
			
		while n.next != node:
			n = n.next
			if n is None:
				break
		self.tail = n
		
		self.tail.next = None
		self.__size -= 1
		return node.value
	def clear(self):
		self.head = self.tail = None
		self.__size = 0
	def __iter__(self):
		n = self.head
		while n is not None:
			yield n.value
			n = n.next
			
	def __reversed__(self):
		q = Queue()
		for i in self:
			q.enqueue(i)
		return q
	def __len__(self):
		return self.__size		
class BinaryTree:
	OptNode = Optional[TreeNode[float]]
	def __init__(self):
		self.root: BinaryTree.OptNode = None
	def insert(self,value:float):
		
		def _m(node:BinaryTree.OptNode):
			if value < node.value:
				return 'l'
			if value > node.value:
				return 'r'
		
		self.__insert(self.root,value,_m)
	
	def __insert(tree,node:OptNode,value:_T,metric:Callable[[TreeNode[_T]],Literal['l','r']]):
		if node is None:
			node = TreeNode(value)
			if tree.root is None: tree.root = node
			return node
		
		if metric(node) == 'l':
			if node.left is not None:
				tree.__insert(node.left,value,metric)
			else:
				node.left = TreeNode(value)
		if metric(node) == 'r':
			if node.right is not None:
				tree.__insert(node.right,value,metric)
				
			else:
				node.right = TreeNode(value)
	def __len_line(self) -> tuple[int,int]:
		nr = nl = 0
		nodel = noder = self.root
		while nodel.left != None:
			nodel = nodel.left
			nl += 1
		while noder.right != None:
			noder = noder.right
			nr += 1
		return (nl,nr)


		
	def __str__(self):
		return str(self.root)

			
			




				
				
class HashMap(Generic[_T2,_T]):
	def __init__(self,hasher:Callable[[_T2],Any]=hash):
		self.__items: dict[_T2,_T] = {}
		self.hash = hasher
		
	def set(self,key:_T2,value:_T):
		i:_T2 = self.hash(key)
		self.__items[i]=(key,value)
	def get(self,key:_T2):
		i = self.hash(key)
		if i in self.__items:
			return self.__items[i][1]
		raise KeyError(f'Couldn\'t find {key} ')  
	def __getitem__(self,key:_T2):
		return self.get(key)
	def __setitem__(self,key:_T2,value:_T):
		self.set(key,value)
	def __str__(self):
		return str({key:value for key,value in self.__items.values()})
	def __len__(self):
		return len(self.__items)
			

def main():
	t = BinaryTree()
	t.insert(0)
	print(t)
	t.insert(7)
	print(t)
	t.insert(-4)
	print(t)
	t.insert(4)
	print(t)
	t.insert(-2)
	print(t)
	

		
		
#v9
#TODO class Tree
# I just need a tip, don't make the code
if __name__ == '__main__':
	main()
	
	