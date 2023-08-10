def uniquify_list(seq):
    seen = set()
    return [val for val in seq if val not in seen and not seen.add(val)]
