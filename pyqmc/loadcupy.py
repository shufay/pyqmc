try:
    import cupy as cp
    from cupy import get_array_module, asnumpy, fuse
    cp.array([1.0])
except Exception as e:
    print("Caught exception:")
    print(e)
    print("using numpy instead of cupy")
    import numpy as cp

    def get_array_module(a):
        return cp

    def asnumpy(a):
        return a

    def fuse():
        return lambda x: x


finally:
    print("cp is module", cp)
