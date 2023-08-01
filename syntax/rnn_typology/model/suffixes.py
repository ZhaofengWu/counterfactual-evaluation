explicit = False

nsubj_sg = "~" if not explicit else ".nsubj.sg"
nsubj_pl = "^" if not explicit else ".nsubj.pl"
dobj_sg = "#" if not explicit else ".dobj.sg"
dobj_pl = "*" if not explicit else ".dobj.pl"
iobj_sg = "@" if not explicit else ".iobj.sg"
iobj_pl = "&" if not explicit else ".iobj.pl"


nsubj_sg = "kar" if not explicit else ".nsubj.sg"
nsubj_pl = "kon" if not explicit else ".nsubj.pl"
dobj_sg = "kin" if not explicit else ".dobj.sg"
dobj_pl = "ker" if not explicit else ".dobj.pl"
iobj_sg = "kan" if not explicit else ".iobj.sg"
iobj_pl = "kre" if not explicit else ".iobj.pl"

suffixes = [nsubj_sg, nsubj_pl, dobj_sg, dobj_pl, iobj_sg, iobj_pl]


