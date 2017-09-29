"""
Descriptive knowledge base support for accumulation over time
"""
import sys
import copct

class DescriptiveKnowledgeBase:
    def __init__(self):
        self.causal_relation = set()
    def grow(self, name, covers):
        for cover in covers:
            u, _, _, _, _ = cover
            schemata = tuple([(sub_name, len(args)) for (_, sub_name, args) in u])
            self.causal_relation.add((name, schemata))
    def causes(self, v):
        state = v[0][0]
        v_schemata = tuple([(name, len(args)) for (_, name, args) in v])
        all_args = tuple([a for (_, _, args) in v for a in args])
        u = set([(state, name, all_args) for (name, schemata) in self.causal_relation if schemata == v_schemata])
        return u
    def make_heterogenous_causes(self, operational_causes):
        def causes(v):
            return self.causes(v) | operational_causes(v)
        return causes

if __name__ == "__main__":

    from baxter_experiments import M, causes
    # from baxter_corpus.demo_replace_red_with_spare_2 import demo    
    # from baxter_corpus.demo_remove_red_drive_2 import demo
    # demo = demo[3:7] # exclude open/close
    from baxter_corpus.demo_remove_bad_drive import demo
    
    status, tlcovs, g = copct.explain(causes, demo, M=M)
    pcovs, _ = copct.minCardinalityTLCovers(tlcovs)
    copct.logCovers(pcovs, sys.stdout)

    kb = DescriptiveKnowledgeBase()

    name = "remove bad drive"
    kb.grow(name, pcovs)
    print(kb.causal_relation)

    from baxter_corpus.demo_remove_two_bad_drives import demo
    het_causes = kb.make_heterogenous_causes(causes)

    status, tlcovs, g = copct.explain(het_causes, demo, M=M)
    pcovs, _ = copct.minParametersTLCovers(tlcovs)
    copct.logCovers(pcovs, sys.stdout)
    

