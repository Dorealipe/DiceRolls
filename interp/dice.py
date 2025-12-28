class Die:
    import random
    def __init__(self,sides:list[int]):
        self.sides = sides
    def play(self):
       return Die.random.choice(self.sides)
class FairDie(Die):
    def __init__(self,quant_sides:int):
        super().__init__(list(range(quant_sides)))
