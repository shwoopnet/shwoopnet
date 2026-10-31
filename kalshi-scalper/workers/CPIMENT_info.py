"""Information line for CPIMENT-RERUN (not a second verdict): the registered scorers with ONE addition, a trade is skipped if the
quote at the registered look has a spread above CAP. Cap 1.0 must reproduce the registered numbers. Reads data/, writes /tmp only."""
import importlib, inspect, sys, pathlib
sys.path.insert(0, "src")
CAP = float(sys.argv[1])
for modname, anchor, ins in (("cpi1", "c = cs[-1]; pdate", ""),
                             ("ment1", "bid, ask = cs[-1][1], cs[-1][2]", "if cs[-1][2] - cs[-1][1] > CAP: continue\n        ")):
    mod = importlib.import_module("scalper." + modname)
    src = pathlib.Path(mod.__file__).read_text()
    assert src.count(anchor) == 1
    src = src.replace(anchor, ("c = cs[-1]\n            if c[2] - c[1] > CAP: continue\n            pdate" if modname == "cpi1" else ins + anchor)).replace("RESULT = DATA_DIR", "RESULT_X = DATA_DIR")
    ns = {"__name__": "x", "__package__": "scalper", "CAP": CAP}
    exec(compile(src, modname + "_info", "exec"), ns)
    ns["RESULT"] = pathlib.Path(f"/tmp/{modname}_info_{CAP}.txt")
    ns["RESULT"].unlink(missing_ok=True)
    print(f"--- {modname} spread cap {CAP}")
    ns["main"](["x", "run"])
