
def output_is_list(f):
    def l(*args, **kvargs):
        return list(f(*args, **kvargs))
    return l
