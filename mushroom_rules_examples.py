R_A = [
    ("r_a1", ("A", "¬ed(m1)"), [("X", "dc(m1)")]),
    ("r_a2", ("A", "col(m1)"), [("X", "ed(m1)")]),
    ("r_a3", ("A", "¬col(m1)"), [("X", "¬ed(m1)")]),
]


R_B = [
    ("r_b1", ("B", "¬ed(m1)"), [("B", "hv(m1)")]),
    ("r_b2", ("B", "col(m1)"), [("X", "ed(m1)")]),
    ("r_b3", ("B", "¬col(m1)"), [("X", "¬ed(m1)")]),
]

R_C = [
    ("r_c1", ("C", "ed(m1)"), [("X", "avl(m1)")])
]

R_D = [
    ("r_d1", ("D", "¬ed(m1)"), [("X", "am(m1)")])
]

R_E = [
    ("r_e1", ("E", "spa(m1)"), [("E", "hv(m1)"), ("E", "pbc(m1)")])
]

R_FOCUS_MUSHROOM = [
    ("r_fk1", ("FK", "hv(m1)"), []),
    ("r_fk2", ("FK", "pbc(m1)"), [])
]


R_MUSHROOM = dict(
    A=R_A,
    B=R_B,
    C=R_C,
    D=R_D,
    E=R_E
)