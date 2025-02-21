
class GVL:
    # def __init__(self):
    _shared_borg_state = {}
    def __new__(cls, *args, **kwargs):
        obj = super(GVL, cls).__new__(cls, *args, **kwargs)
        # check dtype
        obj.__dict__ = cls._shared_borg_state
        return obj
    
    @staticmethod
    def initialise(dic: dict):
        GVL._shared_borg_state = dic


# GVL sample usage


# GVL.initialise({"va1": False, "var2": 123, "var3": "asdasda"})
# GVL().va1 = True
# print(GVL().va1)

# g1 = GVL()
# g1.initialise({"va1": False, "var2": 123, "var3": "asdasda"})
# g1.hello = "oi"

# g2= GVL()
# all the vars should be accessible from here
# print(g2.var2)
