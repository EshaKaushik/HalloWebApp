def friend(adj, user, k):
    frnd = []
    mut = {}
    l = adj.get(user,[])

    while len(frnd) < k and l != []:
        sugg = {}
        for i in l:
            m = adj.get(i, [])
            for j in m:
                if j not in frnd and j not in adj.get(user,[]) and j != user:
                    if j not in sugg:
                        sugg[j] = 0
                    sugg[j] += 1
                    if i in adj.get(user,[]):
                        if j not in mut:
                            mut[j] = []
                        mut[j].append(i)
        
        sugg = sorted(sugg, key=sugg.get, reverse=True)
        frnd += sugg
        l = sugg
    return (frnd[:k] if len(frnd) >= k else frnd,mut)
