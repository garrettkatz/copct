# co-pct

## Parsimonious Covering Theory with Causal Chaining and Ordering Constraints

`copct` is an automated cause-effect reasoning library based on Parsimonious Covering Theory.  Given a compendium of background knowledge, `copct` can automatically explain a set of observations by inferring causes from their effects.  `copct` is specialized for problems involving causal chaining (*A* causes *B*, *B* causes *C*, *C* causes *D* ...) and ordered effects (*A* causes *B*, then *C*, then *D* ...).  When there is more than one valid explanation, `copct` can find all of them.  It can also extract the most *parsimonious* explanations, according to various criteria of parsimony.

## Requirements

`copct` has been tested with Python 2.7.6 and 3.4.3 on Ubuntu 14.04, but it should work with other OS's and other Python versions >= 2.7.  The Monroe County experiments require NumPy and MatPlotLib.

## Installation

`copct` isn't currently set up for automatic installation.  To use `copct`, [clone or download](https://help.github.com/articles/cloning-a-repository/) the repository into a directory of your choice.  You may wish to configure your environment so that `copct` is readily available in other directories and projects (e.g., add the `copct` directory to your [PYTHONPATH](https://docs.python.org/2/using/cmdline.html#envvar-PYTHONPATH) environment variable).

## Usage

### Causal Knowledge and Parsimonious Explanations

`copct` relies on background knowledge about the possible causal relationships in your application domain that you must provide.  We use *V* to denote the set of all possible events that can cause or be caused.  For the sake of example, suppose your application domain involves 6 events labeled 'a' through 'f'.  You could represent this in Python as follows:

```python
>>> V = set(['a','b','c','d','e','f'])
``` 

Since `copct` is specialized to deal with ordering constraints, a central concept is *sequences* of events.  We use *V*\* to denote the set of all finite sequences of events.  A "causal relation" *C* is a subset of *V* x *V*\*.  An pair (u,v) is in C if and only if u can cause v.  u is an event in *V* and v is a sequence of events in *V*\*.  For example:

```python
>>> C = (
... ('c', ('a','b')), # c can cause the sequence a,b
... ('d', ('a','b')), # so can d
... ('e', ('d','f')), # e can cause the sequence d,f
... )
```

Suppose w is some sequence of observed events in *V*\*.  For example:

```python
>>> w = ('a','b','f')
```

A *covering forest* of w is an ordered forest whose leaves are w, and each of whose child-parent relationships are in *C*.  For example,

>  c
>  /\
> a  b  f

>  d
>  /\
> a  b  f

>    e
>   / \
>  d   \
>  /\   \
> a  b   f

are all covering forests of (a,b,f).  The elements of *C* are the *direct* causal links between causes and effects.  Covering forests also capture *indirect* causations that result from *causal chaining* (e.g., e causes d, and d causes a,b).

The root sequence of a covering forest is called a *cover*.  It represents hypothesized causes that can account for the observations.  For example, (c,f), (d,f), and (e) are all covers of w.  A *top-level* cover is a cover that cannot be covered itself by any higher-level causes.  For example, (c,f) and (e) are top-level, but (d,f) is not.  Top-level covers represent acceptable *explanations* for the observed events.

Good explanations are generally expected to satisfy some notion of parsimony.  `copct` supports several parsimony criteria for extracting the best explanations when there are many valid explanations.  For example, *minimum cardinality* explanations are the top-level covers with the fewest number of elements.  (e) is minimum cardinality but (c,f) is not.

### Encoding Causal Knowledge for copct

You expose the causal knowledge to `copct` by implementing a `causes` function.  Given any sequence `v`, `causes(v)` should return the set of all events that can directly cause `v` - that is, all `u` for which `(u,v)` is included in the causal relation.  For example, you could implement a `causes` function for the example relation above as follows:

```python
>>> def causes(v):
...     return set([u for u in V if (u,v) in C])
... 
>>> causes(('a','b'))
set(['c', 'd'])
>>> causes(('c','f'))
set(['e'])
```

`copct` relies only on the `causes` function you provide, and treats it as a black box.  Under the hood, you can decide whether to represent *V* and *C* with, say, a more sophisticated graph-based data structure, or a logic programming rule set, or you could implement `causes` directly without storing *V* or *C* at all, such as:

```python
 >>> def causes(v):
...     if v == ('a','b'): return set(['c','d'])
...     if v == ('c','f'): return set(['e'])
...
```

The main requirement is that any element of *V* which ends up in memory (whether in `w`, or in the output of some call to `causes`) is *hashable* (see the [Python glossary](https://docs.python.org/2/glossary.html)), so that it can be stored in Python sets.  You can either use hashable (e.g., tuple-based) data structures from the start, or provide your data structures with a [__hash__](https://docs.python.org/2/reference/datamodel.html#object.__hash__) method, or convert them to unhashable types (list-based, dict-based, etc.) and back to hashable types (tuple-based) inside `causes` as necessary.

### Computing explanations

Once you have implemented `causes`, you can easily invoke `copct` to find explanations for any sequence of observations:

```python
>>> import copct
>>> w = ('a','b','f','a','b')
>>> status, explanations, _ = copct.explain(causes, w)
>>> status
'Success'
```

Each explanation returned is a tuple that includes additional details such as the overall size and depths of the covering forest.  The first entry of the tuple is the actual cover.  To see a list of all top-level covers found:

```python
>>> [e[0] for e in explanations]
[('d', 'f', 'd'), ('d', 'f', 'c'), ('e', 'd'), ('e', 'c')]
```

The `explain` procedure is fixed-parameter tractable in *M*, where *M* is the length of the longest effect sequence occurring in *C*.  In the example above, *M* is 2, realized by the length-2 effect sequence ('a','b').  On larger examples there will be a significant speed-up if you provide the value of *M* as a keyword argument:

```python
>>> status, explanations, _ = copct.explain(causes, w, M=2)
```

`copct` supports several parsimony criteria.  For example, you can filter for minimum cardinality:

```python
>>> mc_explanations, mc = copct.minCardinalityTLCovers(explanations)
>>> mc
2
>>> [e[0] for e in mc_explanations]
[('e', 'd'), ('e', 'c')]
```

## Documentation

For full API documentation, use:

```python
>>> import copct
>>> help(copct)
```

For more details about algorithmic details and proofs, empirical performance, the parsimony criteria available, and the example applications, please consult the following:

> Katz, Garrett, et al. "Imitation Learning as Cause-Effect Reasoning." International Conference on Artificial General Intelligence. Springer International Publishing, 2016.

## Examples

This repository includes three examples of cause-effect reasoning problems where `copct` can be used.  Each example can be run as a python script.

### toy_example.py

A slightly larger example that still uses letters to label causes and effects and contains a few additional usage patterns.

### baxter_experiments.py

A more realistic example that models an agent's intentions and actions in a tabletop workspace environment.  Hidden intentions ultimately cause the actions that are observed.  `copct` is used to infer the intentions based on the observed actions.  Every cause and effect (i.e., intention and action) is of the form `(state, task, parameters)`, where `state` is the current state of the tabletop environment, `task` is the name of the intention or action about to be carried out, and `parameters` is a list of parameter values that ground the task (such as names of objects in the environment).  For example,

> (('on', 'block1', 'table'), 'pickup', ('left-hand', 'block1'))

signifies an intention to use the left hand to pick up block 1, which is currently on the table.  There are eleven "demonstrations" (i.e., observed action sequences) to be explained, ranging in length from 3 to 39 actions.  `copct` is used on each demonstration to infer the plausible top-level intention sequences that can explain it.

The last demonstration, which is the longest, may take several minutes to complete.

### monroe_experiments.py

A large-scale example that models an emergency response team's intentions and actions in Monroe County of upstate New York.  There are 5000 plans (i.e., observed action sequences); `copct` is used on each one to infer the top-level intentions that best explain it.  The input data was taken from the [Monroe Plan Corpus](https://www.cs.rochester.edu/research/speech/monroe-plan/).

On average, each of the 5000 plans takes about a second to process.  However some take upwards of 5 minutes and may time out.  Running the example on the full corpus may take on the order of 1 week of computation time.  By default, the script will only process a random subset of 10 plans.  To run on the full corpus, change the `num_samples` keyword argument to 5000 in the `__main__` code block.
