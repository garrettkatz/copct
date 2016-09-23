import time
import pickle as pkl
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import copct
import monroe_corpus.monroe_domain as md
from monroe_corpus.monroe_corpus import corpus

def run_sample(M, causes, u_correct, w, verbose=True, timeout=600, timeout_irr=300, max_tlcovs=13000000):
    """
    Run experimental evaluation on one sample plan.
    Inputs:
        M: domain constant (maximum length of any effect sequence in the causal relation)
        causes: handle to the causes function encoding the domain
        u_correct: the "correct" cover against which copct is tested
        w: sequence of observed actions (the plan) to be covered by copct
        verbose: if True, print copct verbose output
        timeout: timeout for explain
        timeout_irr: timout for irredundancy
        max_tlcovs: maximum top-level cover count for explain
    Outputs:
        result: dictionary with various key:value pairs summarizing the outcomes of the experiment.
    """

    # run copct
    start = time.clock()
    status, tlcovs, g = copct.explain(causes, w, M=M, verbose=verbose, timeout=timeout, max_tlcovs=max_tlcovs)
    runtime = time.clock()-start

    # record execution info
    result = {}
    result["runtime"] = runtime
    result["status"] = status
    if not status == "Success": return result

    # top-level results
    result["correct"] = u_correct in [u for (u,_,_,_,_) in tlcovs]
    result["|tlcovs|"] = len(tlcovs)
    print("correct=%s, |tlcovs|=%d"%(result["correct"], result["|tlcovs|"]))

    # compare parsimony criteria
    criteria = [("_mc", copct.minCardinalityTLCovers),
                ("_md", copct.maxDepthTLCovers),
                ("_xd", copct.minimaxDepthTLCovers),
                ("_fsn", copct.minForestSizeTLCovers),
                ("_fsx", copct.maxForestSizeTLCovers),
                ("_mp", copct.minParametersTLCovers)]
    for (label, fun) in criteria:
        pruned_tlcovs, extremum = fun(tlcovs)
        correct = u_correct in [u for (u,_,_,_,_) in pruned_tlcovs]
        count = len(pruned_tlcovs)
        result["correct%s"%label] = correct
        result["|tlcovs%s|"%label] = count
        result["extremum%s"%label] = extremum
        print("%s: correct=%s, count=%d, extremum=%d"%(label, correct, count, extremum))

    # special handling for irredundancy
    status, tlcovs_irr = copct.irredundantTLCovers(tlcovs, timeout=timeout_irr)
    result["irr_success"] = status
    if not status: return result
    result["correct_irr"] = u_correct in [u for (u,_,_,_,_) in tlcovs_irr]
    result["|tlcovs_irr|"] = len(tlcovs_irr)
    print("correct_irr=%s, count_irr=%d"%(result["correct_irr"], result["|tlcovs_irr|"]))

    return result

def run_experiments(use_original=True, num_samples=None, filename=None, verbose=True, timeout=600, timeout_irr=300, max_tlcovs=13000000):
    """
    Run experiments on many samples in the corpus.
    Inputs:
        use_original: if True, run on the original corpus, otherwise run on the modified
        num_samples: number of randomly chosen sample plans from the corpus to use.  Defaults to all of them.
        filename: name of file in which to save results.
            Defaults to "monroe_results.pkl" or "monroe_results_modified.pkl" depending on use_original flag.
        verbose, timeout, timeout_irr, max_tlcovs: additional parameters for run_sample
    Outputs:
       results[s]: dictionary or results for s^th sample plan
    """

    # Setup
    samples = np.random.permutation(len(corpus))
    if num_samples is not None:
        samples = samples[:num_samples]
    if filename is None:
        if use_original: filename = "monroe_results.pkl"
        else: filename = "monroe_results_modified.pkl"

    # Run experiments
    results = {}
    for s in range(len(samples)):
        sample = samples[s]
        print("Starting sample %d of %d (plan # %d in %s corpus)..."%(s, len(samples), sample, "original" if use_original else "modified"))
        w = corpus[sample][2]
        if use_original:
            u_correct = corpus[sample][0]
            causes = md.causes
            # singleton top-level covers are always irredundant, no need to check (timeout_irr=0)
            results[sample] = run_sample(md.M, causes, u_correct, w, verbose=verbose, timeout=timeout, max_tlcovs=max_tlcovs, timeout_irr=0)
            if results[sample]["status"] == "Success":
                results[sample]["|tlcovs_irr|"] = results[sample]["|tlcovs|"]
                results[sample]["correct_irr"] = results[sample]["correct"]
        else:
            u_correct = corpus[sample][1]
            causes = md.mid_causes
            results[sample] = run_sample(md.M, causes, u_correct, w, verbose=verbose, timeout=timeout, max_tlcovs=max_tlcovs, timeout_irr=timeout_irr)
        results_file = open(filename, "w")
        pkl.dump(results, results_file)
        results_file.close()
        print("%d of %d samples processed..."%(s+1, len(samples)))

    return results

def show_results(filename="monroe_results.pkl"):
    """
    Print/plot results shown in publication
    Inputs:
        filename: name of file where results are saved
    """

    # load results
    f = open(filename, "r")
    results = pkl.load(f)
    f.close()

    # accuracy
    for criterion in ["","_mc","_irr","_md","_xd", "_mp", "_fsn", "_fsx"]:
        r = {s:results[s] for s in results if "correct%s"%criterion in results[s] and results[s]["correct"]}
        num_correct = len([s for s in r if r[s]["correct%s"%criterion]])
        if len(r) > 0:
            print("%s: %d of %d (%d %%)"%(criterion, num_correct, len(r), 100*num_correct/len(r)))
        else:
            print("%s: %d of %d"%(criterion, num_correct, len(r)))

    # specificity
    counts = []
    for criterion in ["_mc", "_irr", "_md", "_xd", "_mp"]:
        counts.append([results[s]["|tlcovs%s|"%criterion] for s in results if "|tlcovs%s|"%criterion in results[s]])

    # count summaries
    print("%d of %d samples have 1 MC cover"%(np.count_nonzero(np.array(counts[0])==1), len(counts[0])))
    print("90 %% of samples <= %d MC covers"%(np.sort(counts[0])[int(np.floor(0.9*len(counts[0])))]))
    print("%d of %d samples have 1 MP cover"%(np.count_nonzero(np.array(counts[4])==1), len(counts[4])))
    print("90 %% of samples <= %d MP covers"%(np.sort(counts[4])[int(np.floor(0.9*len(counts[4])))]))

    # histogram
    fig = plt.figure()
    fig.subplots_adjust(bottom=0.15)
    bins = np.arange(7)
    greys = [str(g) for g in np.linspace(0.0,1.0,len(counts))]
    _,bins,_ = plt.hist([np.log10(c) for c in counts], bins=bins, color=greys)
    plt.xlabel('# of covers found')
    plt.ylabel('# of times in corpus')
    plt.legend(['MC','IR','MD','XD','MP'])
    fig.canvas.draw()
    ax = plt.gca()
    old_ticks = ax.get_xticks()
    new_ticks = []
    labels = []
    mpl.rcParams['mathtext.default'] = 'regular'
    for b in range(len(bins)-1):
        new_ticks.append(bins[b])
        labels.append("|")
        new_ticks.append(0.5*(bins[b]+bins[b+1]))
        if b < len(bins)-2:
            labels.append("$10^%d-10^%d$"%(b, b+1))
        else:
            labels.append("$>10^%d$"%b)
    new_ticks.append(bins[-1])
    labels.append("|")
    ax.set_xticks(new_ticks)
    ax.set_xticklabels(labels, rotation=0)
    ax.set_ylim([0, len(results)])
    plt.show()

    # top-level vs irredundant
    fig = plt.figure()
    ax = plt.gca()
    fig.subplots_adjust(bottom=0.15)
    r = {k:results[k] for k in results if '|tlcovs_irr|' in results[k]}
    ax.scatter(np.log2([r[k]['|tlcovs|'] for k in r]), np.log2([r[k]['|tlcovs_irr|'] for k in r]))
    plt.xlabel("# of top-level covers")
    plt.ylabel("# of irredundant top-level covers")
    ax.set_xlim([-0.5, 16])
    ax.set_ylim([-0.5, 16])
    fig.canvas.draw()
    labels = ["$2^{%d}$"%x for x in (2*np.arange(-1, 9))]
    ax.set_xticklabels(labels, rotation=0)
    ax.set_yticklabels(labels, rotation=0)
    fig.canvas.draw()
    return results

if __name__ == "__main__":

    full_experiments = raw_input("Run full experiments?  May use up to 32GB of RAM and about one week of CPU time. [y/n]")

    # Run experiments.
    if full_experiments == "y":
        run_experiments() # original
        run_experiments(use_original=False) # modified
    else:
        run_experiments(num_samples=50, max_tlcovs=1000) # original
        run_experiments(num_samples=50, max_tlcovs=1000, use_original=False) # modified

    # Show results
    plt.ion()
    results = show_results() # original
    results_modified = show_results(filename="monroe_results_modified.pkl") # modified
    raw_input("Enter to close...")
