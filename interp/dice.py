class Die:
    import random
    def __init__(self,sides:list[int]):
        self.sides = sides
    def play(self):
       return Die.random.choice(self.sides)
    def __str__(self):
        return f'{self.sides} dice'
    def __repr__(self):
        
        return f'Stack{self.sides} dice'
    def __len__(self):
        return len(self.sides)
    def __bool__(self):
        return bool(self.sides)
class FairDie(Die):
    def __init__(self,quant_sides:int|str):
        if isinstance(quant_sides,int):
            super().__init__(list(range(quant_sides)))
        elif isinstance(quant_sides,str):
            if quant_sides[0] == 'd' and  quant_sides[1:].isdigit():
                super().__init__(list(range(int(quant_sides[1:]))))
            else: raise TypeError('Strings must have the format dX, where X is a natural number')
    def __repr__(self):
        return f'd{max(self.sides)}'
